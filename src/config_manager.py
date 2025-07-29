#!/usr/bin/env python3
"""Configuration manager for HoYoLAB Auto Check-in"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from src.game_config import GameType
from src.logger import EnhancedFormatter
import platform
import subprocess
import requests
from colorama import Fore, Style, init

class ConfigManager:
    CONFIG_FILE = "checkin_config.json"
    DEFAULT_CONFIG = {
        "run_mode": "all",
        "games": {gt.value: {"enabled": gt in [GameType.HONKAI_STAR_RAIL, GameType.GENSHIN_IMPACT]} for gt in GameType},
        "settings": {
            "run_on_start": True,
            "show_detailed_rewards": True,
            "delay_between_games": 3,
            "max_retries": 3,
            "retry_delay_seconds": 5,
            "colorful_output": True,
            "show_game_emoji": True,
            "enhanced_logging": False,
            "clear_console": False,
            "language": "en-us",
            "console_width": 50
        },
        "loop": {
            "enabled": True,
            "mode": "daily",
            "interval_hours": 24,
            "daily_time": "09:00",
            "timezone": "UTC",
            "max_runs": 0,
            "retry_failed": True,
            "retry_delay_minutes": 30
        },
        "notifications": {
            "enabled": True,
            "success_only": True,
            "webhook_url": "",
            "discord_webhook": "",
            "telegram_bot_token": "",
            "telegram_chat_id": ""
        },
        "advanced": {
            "request_timeout": 30,
            "rate_limit_delay": 2,
            "user_agent_rotation": True,
            "proxy_support": False,
            "proxy_url": ""
        }
    }

    def __init__(self):
        self.config = self.load_config()
        self.run_count = 0
        self._setup_logging()
        self.last_success = True  # Dùng để giữ trạng thái check-in gần nhất


    def _setup_logging(self):
        """Configure logging with enhanced formatter"""
        logging.getLogger().setLevel(logging.DEBUG if self.get_setting("enhanced_logging") else logging.INFO)
        logging.getLogger().handlers = [logging.StreamHandler()]
        logging.getLogger().handlers[0].setFormatter(EnhancedFormatter())

    def clear_console(self):
        """Clear the console if enabled"""
        if self.get_setting("clear_console"):
            subprocess.run("cls" if platform.system() == "Windows" else "clear", shell=True)

    def load_config(self) -> Dict:
        """Load configuration from file or create default"""
        if not os.path.exists(self.CONFIG_FILE):
            self.save_config(self.DEFAULT_CONFIG)
            logging.warning(f"{Fore.YELLOW}📄 Created default config file{Style.RESET_ALL}", 
                            extra={"operation": "config"})
            return self.DEFAULT_CONFIG.copy()

        try:
            with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            merged = self._deep_merge(self.DEFAULT_CONFIG.copy(), config)
            self._validate_config(merged)
            logging.info(f"{Fore.GREEN}✅ Config loaded{Style.RESET_ALL}", 
                         extra={"operation": "config"})
            return merged
        except json.JSONDecodeError:
            logging.error(f"{Fore.RED}❌ Invalid JSON in config file, using defaults{Style.RESET_ALL}", 
                          extra={"operation": "config"})
            self.save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            logging.error(f"{Fore.RED}❌ Config load error: {e}, using defaults{Style.RESET_ALL}", 
                          extra={"operation": "config"})
            self.save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()

    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """Merge two dictionaries recursively"""
        for k, v in update.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                base[k] = self._deep_merge(base[k], v)
            elif v is not None:
                base[k] = v
        return base

    def _validate_config(self, config: Dict):
        """Validate configuration and set defaults for missing keys"""
        for section in ["settings", "loop", "notifications", "advanced"]:
            if section not in config:
                config[section] = self.DEFAULT_CONFIG[section]
                logging.warning(f"{Fore.YELLOW}⚠️ Missing {section} section, using defaults{Style.RESET_ALL}", 
                                extra={"operation": "config"})
            for k, v in self.DEFAULT_CONFIG[section].items():
                if k not in config[section]:
                    config[section][k] = v
                    logging.warning(f"{Fore.YELLOW}⚠️ Missing {section}.{k}, using default: {v}{Style.RESET_ALL}", 
                                    extra={"operation": "config"})
                elif type(v) != type(config[section][k]):
                    logging.warning(f"{Fore.YELLOW}⚠️ Invalid type for {section}.{k}, expected {type(v).__name__}, got {type(config[section][k]).__name__}, using default: {v}{Style.RESET_ALL}", 
                                    extra={"operation": "config"})
                    config[section][k] = v
        
        if "games" not in config:
            config["games"] = self.DEFAULT_CONFIG["games"]
            logging.warning(f"{Fore.YELLOW}⚠️ Missing games section, using defaults{Style.RESET_ALL}", 
                            extra={"operation": "config"})
        
        valid_games = [gt.value for gt in GameType]
        for game in list(config["games"].keys()):
            if game not in valid_games:
                logging.warning(f"{Fore.YELLOW}⚠️ Invalid game {game}, disabling{Style.RESET_ALL}", 
                                extra={"operation": "config"})
                config["games"][game] = {"enabled": False}
            elif "enabled" not in config["games"][game]:
                config["games"][game]["enabled"] = False
                logging.warning(f"{Fore.YELLOW}⚠️ Missing enabled field for {game}, defaulting to false{Style.RESET_ALL}", 
                                extra={"operation": "config"})
        
        if not any(config["games"][game]["enabled"] for game in config["games"]):
            logging.error(f"{Fore.RED}❌ No games enabled in configuration{Style.RESET_ALL}", 
                          extra={"operation": "config"})
            raise ValueError("No games enabled in configuration")
        
        if config["loop"]["mode"] not in ["daily", "interval", "once"]:
            logging.warning(f"{Fore.YELLOW}⚠️ Invalid loop mode {config['loop']['mode']}, defaulting to daily{Style.RESET_ALL}", 
                            extra={"operation": "config"})
            config["loop"]["mode"] = "daily"
        
        try:
            h, m = map(int, config["loop"]["daily_time"].split(':'))
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
        except (ValueError, KeyError):
            logging.warning(f"{Fore.YELLOW}⚠️ Invalid daily_time {config['loop'].get('daily_time', 'Unknown')}, defaulting to 09:00{Style.RESET_ALL}", 
                            extra={"operation": "config"})
            config["loop"]["daily_time"] = "09:00"

    def save_config(self, config: Dict):
        """Save configuration to file"""
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            logging.info(f"{Fore.GREEN}✅ Config saved{Style.RESET_ALL}", 
                         extra={"operation": "config"})
        except Exception as e:
            logging.error(f"{Fore.RED}❌ Config save error: {e}{Style.RESET_ALL}", 
                          extra={"operation": "config"})

    def get_enabled_games(self) -> List[GameType]:
        """Get list of enabled games based on configuration"""
        enabled = []
        for game in self.config["games"]:
            if self.config["games"][game].get("enabled", False):
                try:
                    enabled.append(GameType(game))
                except ValueError:
                    logging.warning(f"{Fore.YELLOW}⚠️ Invalid game type {game} in config, skipping{Style.RESET_ALL}", 
                                    extra={"operation": "config"})
        if not enabled:
            logging.error(f"{Fore.RED}❌ No valid games enabled in configuration{Style.RESET_ALL}", 
                          extra={"operation": "config"})
        return enabled

    def get_setting(self, key: str, default=None):
        """Get a setting value from configuration"""
        return self.config["settings"].get(key, default)

    def is_loop_enabled(self) -> bool:
        """Check if loop mode is enabled"""
        return self.config["loop"]["enabled"]

    def get_loop_mode(self) -> str:
        """Get the loop mode"""
        return self.config["loop"]["mode"]

    def should_continue_loop(self) -> bool:
        """Check if the loop should continue based on max runs"""
        max_runs = self.config["loop"]["max_runs"]
        return self.is_loop_enabled() and (max_runs == 0 or self.run_count < max_runs)

    def increment_run_count(self):
        """Increment the run counter"""
        self.run_count += 1

    def get_next_run_time(self) -> datetime:
        """Calculate the next run time based on loop mode"""
        loop = self.config["loop"]
        now = datetime.now(timezone.utc)
        if loop["mode"] == "daily":
            try:
                h, m = map(int, loop["daily_time"].split(':'))
                next_run = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
                return next_run
            except (ValueError, KeyError) as e:
                logging.warning(f"{Fore.YELLOW}⚠️ Invalid daily_time format: {loop.get('daily_time', 'Unknown')}, using 24h interval{Style.RESET_ALL}", 
                                extra={"operation": "config"})
                return now + timedelta(hours=24)
        return now + timedelta(hours=loop.get("interval_hours", 24))

    def send_notification(self, game: str, message: str, success: bool):
        """Send notifications to configured webhooks"""
        if not self.config["notifications"]["enabled"] or (self.config["notifications"]["success_only"] and not success):
            return
        for url, method in [
            (self.config["notifications"]["webhook_url"], "Webhook"),
            (self.config["notifications"]["discord_webhook"], "Discord"),
            (self.config["notifications"].get("telegram_bot_token") and
             f"https://api.telegram.org/bot{self.config['notifications']['telegram_bot_token']}/sendMessage", "Telegram")
        ]:
            if url:
                try:
                    payload = {"content": f"[{game}] {message}"} if method != "Telegram" else {
                        "chat_id": self.config["notifications"]["telegram_chat_id"], "text": f"[{game}] {message}"}
                    requests.post(url, json=payload, timeout=10).raise_for_status()
                    logging.info(f"{Fore.GREEN}📬 {method} notification sent: {message}{Style.RESET_ALL}", 
                                 extra={"game": game, "operation": "notification"})
                except Exception as e:
                    logging.error(f"{Fore.RED}❌ {method} notification failed: {e}{Style.RESET_ALL}", 
                                  extra={"game": game, "operation": "notification"})