#!/usr/bin/env python3
"""Core API functionality for HoYoLAB"""

import json
import logging
import random
import time
import hashlib
import requests
from typing import Dict, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from src.game_config import GameType, GameConfig
from src.config_manager import ConfigManager
from colorama import Fore, Style, init

init()  # Initialize colorama

class HoYoLabCore:
    REQUIRED_COOKIES = ["ltuid_v2", "ltoken_v2", "account_id_v2", "cookie_token_v2"]
    
    def __init__(self, game_type: GameType, config: ConfigManager):
        self.game_type = game_type
        self.game_config = GameConfig.GAMES[game_type]
        self.config = config
        self.cookies = self._load_cookies()
        self.session = self._create_session()
        self.current_endpoint = self.game_config["api_endpoints"]["primary"]
        self.endpoint_index = 0
        self.request_timeout = config.get_setting("request_timeout", 10)

    def _load_cookies(self) -> Dict:
        """Load cookies from file with validation"""
        try:
            with open(self.game_config["cookie_file"], "r", encoding="utf-8") as f:
                data = json.load(f)
            
            cookies = {c["name"]: c["value"] for c in data.get("cookies", [])} if "cookies" in data else data
            missing = [c for c in self.REQUIRED_COOKIES if not cookies.get(c)]
            
            if missing:
                raise ValueError(f"Missing cookies: {', '.join(missing)}")
            return cookies
            
        except Exception as e:
            logging.error(
                f"{Fore.RED}❌ Cookie error: {e}{Style.RESET_ALL}", 
                extra={"game": self.game_config["short_name"], "operation": "load_cookies"}
            )
            raise

    def _create_session(self) -> requests.Session:
        """Create and configure requests session"""
        session = requests.Session()
        
        # Configure headers
        chrome_ver = random.choice(["120.0.0.0", "121.0.0.0", "122.0.0.0"]) if self.config.get_setting("user_agent_rotation") else "120.0.0.0"
        headers = {
            "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
            "Cookie": "; ".join(f"{k}={v}" for k, v in self.cookies.items()),
            "Accept": "application/json",
            "x-rpc-lang": self.config.get_setting("language", "en-us"),
            "Referer": self.game_config["checkin_url"]
        }
        
        # Game-specific headers
        if self.game_type == GameType.GENSHIN_IMPACT:
            headers.update({
                "x-rpc-app_version": "1.5.0",
                "DS": self._generate_ds()
            })
        else:
            headers.update({
                "x-rpc-app_version": "2.73.1",
                "x-rpc-game_biz": self.game_config["game_biz"]
            })
        
        session.headers.update(headers)

        # Configure proxy if enabled
        if self.config.get_setting("proxy_support") and self.config.get_setting("proxy_url"):
            session.proxies = {
                "http": self.config.get_setting("proxy_url"),
                "https": self.config.get_setting("proxy_url")
            }

        # Configure retry strategy
        retry = Retry(
            total=self.config.get_setting("max_retries", 3),
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        session.mount("https://", HTTPAdapter(max_retries=retry))
        
        return session

    def _generate_ds(self) -> str:
        """Generate dynamic security token for Genshin Impact"""
        t = int(time.time())
        r = ''.join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=6))
        h = hashlib.md5(f"salt=6s25p5ox5y14umn1p61aqyyvbvvl3lrt&t={t}&r={r}".encode()).hexdigest()
        return f"{t},{r},{h}"

    def _try_next_endpoint(self) -> bool:
        """Switch to next fallback endpoint if available"""
        endpoints = self.game_config["api_endpoints"].get("fallback", [])
        if self.endpoint_index < len(endpoints):
            self.current_endpoint = endpoints[self.endpoint_index]
            self.endpoint_index += 1
            logging.info(
                f"{Fore.YELLOW}🔄 Switched to endpoint: {self.current_endpoint}{Style.RESET_ALL}",
                extra={"game": self.game_config["short_name"], "operation": "try_next_endpoint"}
            )
            return True
        return False

    def make_request(self, endpoint: str, method: str = "GET", **kwargs) -> Optional[Dict]:
        """Make API request with retry and endpoint fallback"""
        url = f"{self.current_endpoint}{endpoint}"
        max_attempts = self.config.get_setting("max_retries", 3)
        game = self.game_config["short_name"]

        for attempt in range(max_attempts):
            try:
                # Rate limiting
                time.sleep(random.uniform(0.5, self.config.get_setting("rate_limit_delay", 1.5)))
                
                logging.debug(
                    f"{Fore.CYAN}🔍 {method} {url} (attempt {attempt + 1}){Style.RESET_ALL}",
                    extra={"game": game, "operation": "make_request"}
                )

                # Make request
                kwargs.setdefault("timeout", self.request_timeout)
                response = self.session.request(method.upper(), url, **kwargs)
                response.raise_for_status()
                data = response.json()

                # Handle response codes
                match data.get("retcode", -1):
                    case 0 | -5003:  # Success or already claimed
                        return data
                    case -500001 | -1 | -10001 if self._try_next_endpoint():  # Retry with new endpoint
                        continue
                    case _:
                        logging.warning(
                            f"{Fore.YELLOW}⚠️ API error: {data.get('message', 'Unknown')}{Style.RESET_ALL}",
                            extra={"game": game, "operation": "make_request"}
                        )
                        return data

            except requests.exceptions.RequestException as e:
                if isinstance(e, requests.exceptions.Timeout) and self._try_next_endpoint():
                    continue
                
                if isinstance(e, requests.exceptions.HTTPError):
                    if e.response.status_code == 401:
                        logging.error(
                            f"{Fore.RED}❌ Unauthorized: Invalid or expired cookies{Style.RESET_ALL}",
                            extra={"game": game, "operation": "make_request"}
                        )
                        return None
                    elif e.response.status_code == 429:
                        time.sleep(random.uniform(5, 10))
                        continue
                
                logging.error(
                    f"{Fore.RED}❌ Request error: {type(e).__name__}{Style.RESET_ALL}",
                    extra={"game": game, "operation": "make_request"}
                )
                return None

        logging.error(
            f"{Fore.RED}❌ Failed after {max_attempts} attempts{Style.RESET_ALL}",
            extra={"game": game, "operation": "make_request"}
        )
        return None