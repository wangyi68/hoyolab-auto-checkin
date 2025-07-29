# 🌟 HoYoLAB Auto Check-in

A robust, user-friendly Python script to automate daily check-ins for HoYoverse games, including **Honkai: Star Rail**, **Genshin Impact**, **Zenless Zone Zero**, and **Honkai Impact 3rd**. Enjoy a seamless experience with a polished console interface, multilingual support, flexible scheduling, and advanced configuration for reliability and customization.

## ✨ Features

- **Multi-Game Support**: Automates check-ins for Honkai: Star Rail, Genshin Impact, Zenless Zone Zero, and Honkai Impact 3rd.
- **Multilingual Interface**: Supports English (`en-us`) and Chinese (`zh-cn`) for console and logs.
- **Flexible Scheduling**: Choose daily, interval-based, or one-time check-in modes.
- **Enhanced Console UI**: Features colorful output, game-specific emojis, and detailed reward summaries.
- **Notifications**: Sends results to Discord and Telegram with customizable settings.
- **Robust Error Handling**: Includes retries, fallback endpoints, and user agent rotation for reliable API calls.
- **Advanced Configuration**: Supports proxies, customizable delays, and detailed logging.
- **Cross-Platform**: Runs on Windows, macOS, and Linux.

## 📋 Prerequisites

- **Python**: Version 3.8 or higher.
- **Dependencies**: Install libraries listed in `requirements.txt` (see [Installation](#installation)).
- **HoYoverse Account**: Required for cookie-based authentication.

## 🛠️ Installation

1. **Clone the Repository**:
   - Download or clone from GitHub: `https://github.com/wangyi68/hoyolab-auto-checkin`
   - Navigate to the project directory.

2. **Install Dependencies**:
   - Create a `requirements.txt` file (example provided below).
   - Run: `pip install -r requirements.txt`.

3. **Set Up Cookies**: Configure cookie files for each game (see [Cookie Setup](#cookie-setup)).

**Example `requirements.txt`**:
```
requests>=2.28.0
schedule>=1.1.0
colorama>=0.4.4
python-telegram-bot>=20.0
```

## ⚙️ Configuration

The script generates a `checkin_config.json` file with default settings on first run. Customize it as needed.

### Cookie Setup

Create a JSON file for each game in the `cookies/` directory (e.g., `cookies/hsr_cookie.json`). To obtain cookies:

1. Visit the check-in page for each game:
   - **Honkai: Star Rail**: [Link](https://act.hoyolab.com/bbs/event/signin/hkrpg/index.html?act_id=e202303301540311)
   - **Genshin Impact**: [Link](https://act.hoyolab.com/ys/event/signin-sea-v3/index.html?act_id=e202102251931481)
   - **Zenless Zone Zero**: [Link](https://act.hoyolab.com/bbs/event/signin/zzz/e202406031448091.html?act_id=e202406031448091)
   - **Honkai Impact 3rd**: [Link](https://act.hoyolab.com/bbs/event/signin-bh3/index.html?act_id=e202110291205111)

2. Log in to your HoYoverse account.
3. Open Developer Tools (`F12`) → **Application** → **Cookies**.
4. Copy `ltuid_v2`, `ltoken_v2`, `account_id_v2`, `cookie_token_v2`.
5. Create or update the cookie file:
   ```json
   {
     "ltuid_v2": "your_ltuid_v2_here",
     "ltoken_v2": "your_ltoken_v2_here",
     "account_id_v2": "your_account_id_v2_here",
     "cookie_token_v2": "your_cookie_token_v2_here",
     "mi18nLang": "en-us"
   }
   ```

### Configuration File (`checkin_config.json`)

Key sections include:

- **run_mode**: Select games to check in (`"all"` or specific: `hsr`, `gi`, `zzz`, `hi3`).
- **games**: Enable/disable specific games.
- **settings**: Options for immediate runs, reward details, delays, retries, and console styling.
- **loop**: Configure looping mode, schedule, and retries.
- **notifications**: Set up Discord/Telegram notifications.
- **advanced**: Manage timeouts, rate limits, user agents, and proxies.

**Example `checkin_config.json`**:
```json
{
  "run_mode": "all",
  "games": {
    "hsr": {"enabled": true},
    "gi": {"enabled": true},
    "zzz": {"enabled": false},
    "hi3": {"enabled": false}
  },
  "settings": {
    "run_on_start": true,
    "show_detailed_rewards": true,
    "delay_between_games": 1.5,
    "max_retries": 5,
    "colorful_output": true,
    "show_game_emoji": true,
    "enhanced_logging": false,
    "clear_console": true,
    "language": "en-us",
    "save_logs_to_file": true,
    "console_width": 50
  },
  "loop": {
    "enabled": false,
    "mode": "daily",
    "interval_hours": 24,
    "daily_time": "09:00",
    "timezone": "UTC",
    "max_runs": 0,
    "retry_failed": true,
    "retry_delay_minutes": 10
  },
  "notifications": {
    "enabled": true,
    "success_only": false,
    "discord_webhook": "",
    "telegram_bot_token": "",
    "telegram_chat_id": ""
  },
  "advanced": {
    "request_timeout": 15,
    "rate_limit_delay": 1.0,
    "user_agent_rotation": true,
    "proxy_support": false,
    "proxy_url": ""
  }
}
```

## 🚀 Usage

Run the script with:
```bash
python main.py
```

## 📬 Notifications

- **Discord**: Set `discord_webhook` in `checkin_config.json` (get from Discord: Server Settings → Integrations → Webhooks).
- **Telegram**: Configure `telegram_bot_token` (from BotFather) and `telegram_chat_id`.
- Enable with `notifications.enabled: true`. Use `success_only: true` for successful check-ins only.

## 🖥️ Console Output

The script offers a vibrant, user-friendly interface:
- **Game Headers**: Include emojis and names.
- **Status Summaries**: Show check-in status, sign-in days, missed days, and rewards.
- **Color Coding**: Green (success), yellow (warnings), red (errors), gold (rewards).
- **Languages**: English or Chinese based on `language` setting.

**Example Output (Chinese)**:
```
┌────────────── 状态 ──────────────┐
│ HoYoLAB 自动签到                 │
│ 2025-07-29 21:42:00 UTC          │
└──────────────────────────────────┘

┌────────────── 游戏 ──────────────┬──────── 状态 ───────┐
│ 🚂 崩坏：星穹铁道               │ 已启用              │
│ ⚔️ 原神                         │ 已启用              │
└──────────────────────────────────┴─────────────────────┘

┌────────────── 循环 ──────────────┐
│ 模式: 每日                       │
│ 下次: 2025-07-30 09:00           │
│ ✓ 立即开始                       │
└──────────────────────────────────┘

┌──────────── 签到 ────────────┐
│ 🔍 开始签到...                │
└──────────────────────────────┘

┌──────────────────────────────┬───────────────┐
│ 游戏                         │ 状态          │
├──────────────────────────────┼───────────────┤
│ 🚂 崩坏：星穹铁道           │ ✅ 成功       │
│ ⚔️ 原神                     │ ✅ 成功       │
└──────────────────────────────┴───────────────┘
```

## 📜 Logging

- **Log File**: Saved to `checkin.log` with timestamps and levels (INFO, WARNING, ERROR) if `save_logs_to_file: true`.
- **Styling**: Includes game emojis and colors.
- **Debug Mode**: Enable with `enhanced_logging: true` for detailed API logs.
- **Console Clearing**: Enabled by default; disable with `clear_console: false`.

## 📂 Project Structure

```
├── main.py              # Script entry point
├── hoyolab.py           # Manages check-in loops and UI
├── hoyolab_client.py    # Handles API requests
├── hoyolab_core.py      # Core API and session management
├── config_manager.py    # Configuration handling
├── game_config.py       # Game-specific settings
├── logger.py            # Custom logging
├── cookies/             # Stores game cookie files
│   ├── hsr_cookie.json  # Honkai: Star Rail cookies
│   ├── gi_cookie.json   # Genshin Impact cookies
│   ├── zzz_cookie.json  # Zenless Zone Zero cookies
│   ├── hi3_cookie.json  # Honkai Impact 3rd cookies
├── checkin_config.json  # Configuration file
└── README.md            # Documentation
```

## 🛠️ Troubleshooting

- **Notifications Fail**:
  - Check `discord_webhook` starts with `https://discord.com/api/webhooks/`.
  - Verify `telegram_bot_token` and `telegram_chat_id`.
  - Ensure `notifications.enabled: true`.

- **Cookie Issues**:
  - Confirm all cookies (`ltuid_v2`, `ltoken_v2`, `account_id_v2`, `cookie_token_v2`) are present.
  - Refresh cookies for `retcode: -100` errors.

- **Verbose Output**:
  - Disable debug with `enhanced_logging: false`.
  - Keep console uncleared with `clear_console: false`.

- **API Failures**:
  - Adjust `max_retries` and `request_timeout`.
  - Enable `user_agent_rotation` or `proxy_support`.
  - Check internet and API endpoint status.

## 🤝 Contributing

1. Fork the repository.
2. Create a branch for your changes.
3. Follow PEP 8 and add clear comments.
4. Submit a pull request with a detailed description.

Report issues or suggest features via GitHub Issues.

## 📄 License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.