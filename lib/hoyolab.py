#!/usr/bin/env python3
"""HoYoLAB Check-in Manager"""

import logging
import time
from datetime import datetime, timezone

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.align import Align
from colorama import init

from src.game_config import GameType, GameConfig
from src.config_manager import ConfigManager
from lib.hoyolab_client import HoYoLabCheckin

init()  # Initialize colorama

class HoYoLab:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.clients = {gt: HoYoLabCheckin(gt, config) for gt in config.get_enabled_games()}
        self.console = Console(width=config.get_setting("console_width", 50))
        self.config.last_success = True  # Mặc định ban đầu là thành công

    def run_checkins(self) -> tuple[bool, dict]:
        if self.config.get_setting("clear_console"):
            self.console.clear()

        success = True
        results = {}
        delay = self.config.get_setting("delay_between_games", 3)

        self.console.print(Panel(
            Align.center("🔍 Starting check-ins..."),
            style="cyan",
            width=self.console.width
        ))

        table = Table(show_header=True, header_style="bold magenta", width=self.console.width)
        table.add_column("Game", style="cyan", width=30)
        table.add_column("Status", style="green", width=15)

        for index, gt in enumerate(sorted(self.clients.keys(), key=lambda x: x.value)):
            if index > 0 and delay > 0:
                self.console.print(f"[yellow]⏳ Waiting {delay}s for next game...[/]")
                time.sleep(delay)

            try:
                result = self.clients[gt].run()
                success &= result
                results[gt] = {"success": result, "config": self.config.config}
                status = "[green]✅ Success[/]" if result else "[red]❌ Failed[/]"
                name = GameConfig.GAMES[gt]["name"]
                emoji = GameConfig.GAMES[gt]["emoji"]
                table.add_row(f"{emoji} {name}", status)
            except Exception as e:
                logging.error(f"Check-in error: {e}", extra={"game": GameConfig.GAMES[gt]["short_name"], "operation": "run_checkins"})
                self.config.send_notification(GameConfig.GAMES[gt]["short_name"], f"Check-in error: {e}", False)
                success = False
                results[gt] = {"success": False, "config": self.config.config}
                table.add_row(f"{GameConfig.GAMES[gt]['emoji']} {GameConfig.GAMES[gt]['name']}", "[red]❌ Failed[/]")

        self.console.print(table)
        self.config.last_success = success
        return success, results

    def _format_timedelta(self, seconds: float) -> str:
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


    def start_loop(self):

        while self.config.should_continue_loop():
            try:
                now = datetime.now(timezone.utc)
                next_run = self.config.get_next_run_time()
                sleep_secs = (next_run - now).total_seconds()

                if sleep_secs > 0:
                    with Live(refresh_per_second=1, console=self.console) as live:
                        while sleep_secs > 0:
                            now = datetime.now(timezone.utc)
                            sleep_secs = (next_run - now).total_seconds()

                            status = "All successful" if self.config.last_success else "Some failed"
                            status_color = "green" if self.config.last_success else "yellow"
                            loop_panel = Panel(
                                Align.center(
                                    f"[{status_color}]✓ {status}[/]\n"
                                    f"[magenta]Mode:[/] {self.config.get_loop_mode().capitalize()}\n"
                                    f"[cyan]Next run:[/] {next_run.strftime('%Y-%m-%d %H:%M:%S')}\n"
                                    f"[yellow]⏳ Waiting {self._format_timedelta(sleep_secs)}[/]",
                                    vertical="middle"
                                ),
                                title="STATUS LOOP",
                                border_style="cyan",
                                width=self.config.get_setting("console_width", 46),
                                padding=(1, 1)
                            )
                            live.update(loop_panel)
                            time.sleep(1)

                success, _ = self.run_checkins()
                self.config.last_success = success
                self.config.increment_run_count()

                if not self.config.should_continue_loop():
                    logging.info("Max runs reached", extra={"operation": "start_loop"})
                    self.console.print(Panel(
                        Align.center("[yellow]Max runs reached[/]"),
                        title="Exit",
                        border_style="yellow",
                        expand=False,
                        width=self.config.get_setting("console_width", 46))
                    )
                    break

                if not success and self.config.config["loop"]["retry_failed"]:
                    delay = self.config.config["loop"]["retry_delay_minutes"] * 60
                    logging.warning(f"Retrying in {delay//60} minutes", extra={"operation": "start_loop"})
                    self.console.print(Panel(
                        Align.center(f"[yellow]Retry in {delay//60} min[/]"),
                        title="Retry",
                        border_style="yellow",
                        expand=False,
                        width=self.config.get_setting("console_width", 46))
                    )
                    time.sleep(delay)
                    continue

            except KeyboardInterrupt:
                logging.info("Loop interrupted by user", extra={"operation": "start_loop"})
                self.console.print(Panel(
                    Align.center("[red]Interrupted by user[/]"),
                    title="Exit",
                    border_style="red",
                    expand=False,
                    width=self.config.get_setting("console_width", 46))
                )
                break

            except Exception as e:
                logging.error(f"Loop error: {e}", extra={"operation": "start_loop"})
                self.console.print(Panel(
                    Align.center(f"[red]Error: {str(e)[:30]}...[/]"),
                    title="Error",
                    border_style="red",
                    expand=False,
                    width=self.config.get_setting("console_width", 46))
                )
                time.sleep(60)
