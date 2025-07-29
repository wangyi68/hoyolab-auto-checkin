#!/usr/bin/env python3
"""Main entry point for HoYoLAB Auto Check-in"""

import sys
import signal
import time
from datetime import datetime, UTC
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lib.hoyolab import HoYoLab
from src.config_manager import ConfigManager
from src.logger import setup_logger
from src.game_config import GameConfig

# Global console
console = Console(width=50)

# Global variables
config: Optional[ConfigManager] = None
logger = None


def print_header():
    """Print compact system status header"""
    global config
    global logger

    if config is None or logger is None:
        return

    console.width = config.get_setting("console_width", 50)
    console.clear()

    logger.info("🌟 HoYoLAB Auto Check-in Started", extra={"operation": "startup"})

    # Main panel header
    console.print(Panel(
        f"[cyan]HoYoLAB Auto Check-in[/]\n[white]{datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC[/]",
        title="Status", border_style="green", expand=False, width=console.width
    ))

    # Enabled games table
    if enabled_games := config.get_enabled_games():
        table = Table(show_header=True, header_style="bold magenta", expand=False, width=console.width)
        table.add_column("Game", style="cyan", width=25)
        table.add_column("Status", style="green", width=15)

        for gt in sorted(enabled_games, key=lambda x: x.value):
            game = GameConfig.GAMES[gt]
            emoji = game['emoji'] if config.get_setting("show_game_emoji") else ""
            table.add_row(f"{emoji} {game['name'][:23]}", "[green]Enabled[/]")
        console.print(table)

    # Loop panel
    if config.is_loop_enabled():
        next_run = config.get_next_run_time()
        mode = config.get_loop_mode().capitalize()
        run_now = config.get_setting("run_on_start")

        loop_info = (
            f"[magenta]Mode:[/] {mode}\n"
            f"[magenta]Next:[/] {next_run.strftime('%Y-%m-%d %H:%M')}\n"
            f"{'[green]✓ Start Now[/]' if run_now else '[yellow]⏳ Scheduled[/]'}"
        )

        console.print(Panel(loop_info, title="Loop", border_style="magenta", expand=False, width=console.width))


def handle_shutdown(signum, frame):
    """Handle graceful shutdown"""
    global config, logger
    if logger is None:
        logger = setup_logger(False)

    logger.info("👋 Program interrupted by user", extra={"operation": "shutdown"})
    console.print(Panel("[red]Shutting down...[/]", title="Exit", border_style="red", expand=False, width=console.width))
    sys.exit(0)


def main():
    """Main execution function"""
    global config
    global logger

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    try:
        config = ConfigManager()
        logger = setup_logger(config.get_setting("enhanced_logging"))

        print_header()

        # ✅ Delay 1.5s sau khi in header
        time.sleep(1.5)

        hoyolab = HoYoLab(config)

        if config.get_setting("run_on_start") or not config.is_loop_enabled():
            success, _ = hoyolab.run_checkins()
            if not config.is_loop_enabled():
                sys.exit(0 if success else 1)

        if config.is_loop_enabled():
            hoyolab.start_loop()

    except Exception as e:
        if logger is None:
            logger = setup_logger(False)
        logger.error(f"💥 Fatal error: {e}", extra={"operation": "fatal"})
        console.print(Panel(f"[red]Fatal: {str(e)[:100]}[/]", title="Error", border_style="red", expand=False, width=console.width))
        sys.exit(1)


if __name__ == "__main__":
    main()
