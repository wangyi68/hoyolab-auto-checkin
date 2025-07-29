#!/usr/bin/env python3
"""API Client for HoYoLAB Check-in operations"""

import json
import logging
import os
import time
import requests
from datetime import datetime
from typing import Dict, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from src.game_config import GameType, GameConfig
from src.config_manager import ConfigManager
from lib.hoyolab_core import HoYoLabCore


class HoYoLabCheckin(HoYoLabCore):
    def __init__(self, game_type: GameType, config: ConfigManager):
        super().__init__(game_type, config)
        self.lang = config.get_setting("language", "en-us")
        self.console = Console(width=config.get_setting("console_width", 50))
        self.last_log = None
        self.max_retries = config.get_setting("max_retries", 3)
        self.retry_delay = config.get_setting("retry_delay_seconds", 5)

    def _print_game_header(self):
        emoji = self.game_config["emoji"] if self.config.get_setting("show_game_emoji") else ""
        game_name = self.game_config["name_zh"] if self.lang == "zh-cn" else self.game_config["name"]
        content = f"{emoji} {game_name}"
        panel = Panel(
            Align.center(content, vertical="middle"),
            title="Check-in",
            border_style="cyan",
            width=self.console.width
        )
        self.console.print(panel)

    def _create_sample_cookie_file(self):
        file = self.game_config["cookie_file"]
        if os.path.exists(file):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    json.load(f)
                return
            except json.JSONDecodeError:
                logging.warning(f"⚠️ Invalid JSON in {file}, creating sample", extra={"game": self.game_config["short_name"]})

        sample = {c: f"your_{c}_here" for c in self.REQUIRED_COOKIES}
        sample["mi18nLang"] = self.lang
        try:
            os.makedirs(os.path.dirname(file), exist_ok=True)
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(sample, f, indent=2)
            logging.warning(f"📄 Created sample cookie file: {file}", extra={"game": self.game_config["short_name"]})
        except Exception as e:
            logging.error(f"❌ Failed to create sample cookie file: {e}", extra={"game": self.game_config["short_name"]})

    def _show_cookie_help(self):
        msg = {
            "en-us": [
                f"Visit: {self.game_config['checkin_url'][:30]}...",
                "Log in to HoYoverse",
                "F12 → Application → Cookies",
                f"Copy: {', '.join(self.REQUIRED_COOKIES)}",
                f"Update: {self.game_config['cookie_file'][:30]}..."
            ],
            "zh-cn": [
                f"访问: {self.game_config['checkin_url'][:30]}...",
                "登录 HoYoverse 账户",
                "按 F12 → 应用程序 → Cookies",
                f"复制: {', '.join(self.REQUIRED_COOKIES)}",
                f"更新: {self.game_config['cookie_file'][:30]}..."
            ]
        }[self.lang]

        table = Table(title="Cookie Setup", show_header=False)
        table.add_column("Step", style="white")
        for i, step in enumerate(msg, 1):
            table.add_row(f"{i}. {step}")
        self.console.print(table)

    def _retry_request(self, method: str, endpoint: str, operation: str, **kwargs) -> Optional[Dict]:
        game = self.game_config["short_name"]
        for attempt in range(self.max_retries):
            try:
                return self.make_request(endpoint, method=method, **kwargs)
            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    logging.warning(f"⚠️ Retry {attempt + 1}/{self.max_retries}: {e}", extra={"game": game, "operation": operation})
                    time.sleep(self.retry_delay)
                else:
                    msg = f"❌ Failed after {self.max_retries} retries: {e}"
                    logging.error(msg, extra={"game": game, "operation": operation})
                    self.console.print(Panel(f"[red]{msg[:60]}...[/]", title=f"Error [{game}]", border_style="red"))
                    self.config.send_notification(game, msg, False)
                    return None

    def get_checkin_info(self) -> Optional[Dict]:
        params = {"act_id": self.game_config["act_id"], "lang": self.lang}
        data = self._retry_request("GET", self.game_config["info_endpoint"], "get_checkin_info", params=params)
        if not data or data.get("retcode") != 0:
            if data and data.get("retcode") == -100:
                self._show_cookie_help()
            msg = f"❌ Failed to get check-in info: {data.get('message', 'Unknown')}" if data else "❌ No response"
            logging.error(msg, extra={"game": self.game_config["short_name"], "operation": "get_checkin_info"})
            self.config.send_notification(self.game_config["short_name"], msg, False)
            return None
        return data.get("data")

    def get_today_reward(self, info: Dict) -> Optional[Tuple[str, int]]:
        params = {"act_id": self.game_config["act_id"], "lang": self.lang}
        data = self._retry_request("GET", self.game_config["reward_endpoint"], "get_today_reward", params=params)
        if not data or data.get("retcode") != 0:
            return None
        rewards = data["data"].get("awards", [])
        day = info.get("total_sign_day", 0)
        return self._format_reward_name(rewards[day - 1]) if 0 < day <= len(rewards) else None

    def get_next_reward(self, day: int) -> Optional[Tuple[str, int]]:
        params = {"act_id": self.game_config["act_id"], "lang": self.lang}
        data = self._retry_request("GET", self.game_config["reward_endpoint"], "get_next_reward", params=params)
        if not data or data.get("retcode") != 0:
            return None
        rewards = data["data"].get("awards", [])
        return self._format_reward_name(rewards[day]) if day < len(rewards) else None

    def _format_reward_name(self, award: Dict) -> Tuple[str, int]:
        name = award.get("name", "Unknown").lower()
        count = award.get("cnt", 1)
        for key, fmt in GameConfig.REWARD_NAMES[self.lang].items():
            if key in name:
                return fmt, count
        return f"🎁 {award.get('name', 'Reward')}", count

    def perform_checkin(self) -> bool:
        game = self.game_config["short_name"]
        params = {"act_id": self.game_config["act_id"]}
        payload = {"lang": self.lang}
        data = self._retry_request("POST", self.game_config["sign_endpoint"], "perform_checkin", params=params, json=payload)

        if not data:
            self.last_log = f"❌ [{game}] Check-in failed"
            return False

        code = data.get("retcode")
        if code == 0:
            reward, count = self._format_reward_name(data["data"]["award"])
            msg = f"✅ Success! {reward} x{count}"
        elif code == -5003:
            msg = f"✅ Already checked in"
        elif code == -100:
            self._show_cookie_help()
            msg = f"❌ Invalid cookie: {data.get('message', 'Unknown')}"
        else:
            msg = f"❌ Failed: {data.get('message', 'Unknown')}"

        logging.info(msg, extra={"game": game, "operation": "perform_checkin"})
        self.config.send_notification(game, msg, code in (0, -5003))
        self.last_log = f"[{game}] {msg}"
        return code in (0, -5003)

    def display_status(self, info: Dict, today: Optional[Tuple[str, int]], next_r: Optional[Tuple[str, int]]):
        msg = {
            "en-us": {
                "checked": f"✅ Day {info.get('total_sign_day', 0)}",
                "pending": "⏰ Pending",
                "missed": "Missed", "time": "Time", "progress": "Progress",
                "today": "Reward", "next": "Next", "log": "Log"
            },
            "zh-cn": {
                "checked": f"✅ 第 {info.get('total_sign_day', 0)} 天",
                "pending": "⏰ 待签到",
                "missed": "错过", "time": "时间", "progress": "进度",
                "today": "奖励", "next": "下次", "log": "日志"
            }
        }[self.lang]
        status = msg["checked"] if info.get("is_sign", False) else msg["pending"]
        table = Table(show_header=False)
        table.add_column("Field", style="cyan", width=14)
        table.add_column("Value", style="white")
        table.add_row(msg["time"], datetime.now().strftime('%H:%M:%S'))
        table.add_row(msg["progress"], status)
        if info.get("sign_cnt_missed", 0):
            table.add_row(msg["missed"], str(info["sign_cnt_missed"]))
        if today:
            table.add_row(msg["today"], f"{today[0][:24]} x{today[1]}")
        if next_r:
            table.add_row(msg["next"], f"{next_r[0][:24]} x{next_r[1]}")
        if self.last_log:
            table.add_row(msg["log"], self.last_log[:35])
        self.console.print(table)

    def run(self) -> bool:
        self._print_game_header()
        info = self.get_checkin_info()
        if not info:
            return False
        if not info.get("is_sign", False):
            if not self.perform_checkin():
                return False
            info = self.get_checkin_info() or info
        today = self.get_today_reward(info) if self.config.get_setting("show_detailed_rewards") else None
        next_r = self.get_next_reward(info["total_sign_day"]) if self.config.get_setting("show_detailed_rewards") else None
        self.display_status(info, today, next_r)
        return True
