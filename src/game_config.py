#!/usr/bin/env python3
"""Game configuration for HoYoLAB Auto Check-in"""

from enum import Enum

class GameType(Enum):
    HONKAI_STAR_RAIL = "hsr"
    GENSHIN_IMPACT = "gi"
    ZENLESS_ZONE_ZERO = "zzz"
    HONKAI_IMPACT_3RD = "hi3"

class GameConfig:
    GAMES = {
        GameType.HONKAI_STAR_RAIL: {
            "name": "Honkai: Star Rail", "name_zh": "崩坏：星穹铁道", "short_name": "HSR", "act_id": "e202303301540311",
            "game_biz": "hkrpg_global", "cookie_file": "cookies/hsr_cookie.json",
            "emoji": "🚂", "color": "magenta",
            "checkin_url": "https://act.hoyolab.com/bbs/event/signin/hkrpg/index.html",
            "api_endpoints": {
                "primary": "https://sg-public-api.hoyolab.com",
                "fallback": ["https://sg-hk4e-api.hoyolab.com", "https://api-os-takumi.mihoyo.com"]
            },
            "info_endpoint": "/event/luna/info", "sign_endpoint": "/event/luna/sign",
            "reward_endpoint": "/event/luna/home"
        },
        GameType.GENSHIN_IMPACT: {
            "name": "Genshin Impact", "name_zh": "原神", "short_name": "GI", "act_id": "e202102251931481",
            "game_biz": "hk4e_global", "cookie_file": "cookies/gi_cookie.json",
            "emoji": "⚔️", "color": "cyan",
            "checkin_url": "https://act.hoyolab.com/ys/event/signin-sea-v3/index.html",
            "api_endpoints": {
                "primary": "https://sg-hk4e-api.hoyoverse.com",
                "fallback": ["https://sg-hk4e-api.hoyolab.com", "https://hk4e-api-os.hoyoverse.com"]
            },
            "info_endpoint": "/event/sol/info", "sign_endpoint": "/event/sol/sign",
            "reward_endpoint": "/event/sol/home"
        },
        GameType.ZENLESS_ZONE_ZERO: {
            "name": "Zenless Zone Zero", "name_zh": "绝区零", "short_name": "ZZZ", "act_id": "e202406031448091",
            "game_biz": "nap_global", "cookie_file": "cookies/zzz_cookie.json",
            "emoji": "🌆", "color": "yellow",
            "checkin_url": "https://act.hoyolab.com/bbs/event/signin/zzz/index.html",
            "api_endpoints": {
                "primary": "https://sg-act-nap-api.hoyolab.com",
                "fallback": ["https://sg-public-api.hoyolab.com", "https://api-os-takumi.mihoyo.com"]
            },
            "info_endpoint": "/event/luna/zzz/info", "sign_endpoint": "/event/luna/zzz/sign",
            "reward_endpoint": "/event/luna/zzz/home"
        },
        GameType.HONKAI_IMPACT_3RD: {
            "name": "Honkai Impact 3rd", "name_zh": "崩坏3", "short_name": "HI3", "act_id": "e202110291205111",
            "game_biz": "bh3_global", "cookie_file": "cookies/hi3_cookie.json",
            "emoji": "⚡", "color": "green",
            "checkin_url": "https://act.hoyolab.com/bbs/event/signin-bh3/index.html",
            "api_endpoints": {
                "primary": "https://sg-public-api.hoyolab.com",
                "fallback": ["https://api-os-takumi.mihoyo.com", "https://sg-hk4e-api.hoyolab.com"]
            },
            "info_endpoint": "/event/mani/info", "sign_endpoint": "/event/mani/sign",
            "reward_endpoint": "/event/mani/home"
        }
    }

    REWARD_NAMES = {
        "en-us": {
            "mora": "💰 Mora", "primogem": "💎 Primogem", "stellar_jade": "💎 Stellar Jade",
            "polychrome": "🌈 Polychrome", "crystal": "💎 Crystal", "credit": "💰 Credit",
            "denny": "💰 Denny", "exp": "📚 EXP Material", "enhancement_ore": "⚡ Enhancement Ore",
            "mystic_enhancement_ore": "⭐ Mystic Enhancement Ore", "hero_wit": "📘 Hero's Wit",
            "resin": "🌳 Fragile Resin", "recipe": "📜 Recipe", "artifact": "🗿 Artifact",
            "relic": "🏺 Relic", "planar_ornament": "🌟 Planar Ornament", "w_engine": "⚙️ W-Engine",
            "adventure_log": "📖 Adventure Log", "condensed_aether": "🌌 Condensed Aether"
        },
        "zh-cn": {
            "mora": "💰 摩拉", "primogem": "💎 原石", "stellar_jade": "💎 星穹",
            "polychrome": "🌈 多色", "crystal": "💎 水晶", "credit": "💰 信用点",
            "denny": "💰 丹尼", "exp": "📚 经验材料", "enhancement_ore": "⚡ 强化矿石",
            "mystic_enhancement_ore": "⭐ 精炼矿石", "hero_wit": "📘 英雄智慧",
            "resin": "🌳 脆弱树脂", "recipe": "📜 配方", "artifact": "🗿 圣遗物",
            "relic": "🏺 遗器", "planar_ornament": "🌟 平面饰品", "w_engine": "⚙️ W引擎",
            "adventure_log": "📖 冒险日志", "condensed_aether": "🌌 浓缩以太"
        }
    }