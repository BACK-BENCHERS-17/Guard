#!/usr/bin/env python3
"""
Telegram Channel Guard & Message Purge Bot
Built for Kurigram / Modern Pyrogram Forks
100% MongoDB Persistence (Motor) + Native ButtonStyle Colors & Custom Emojis
Render 24/7 Deployment Ready
"""

from __future__ import annotations

import asyncio
import html
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

# Global event loop initialization compatible with Python 3.12 - 3.14+
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client, filters, idle
from pyrogram.enums import ButtonStyle, ChatMemberStatus, ChatType
from pyrogram.errors import (
    ChannelInvalid,
    ChatAdminRequired,
    FloodWait,
    InputUserDeactivated,
    MessageDeleteForbidden,
    MessageNotModified,
    PeerIdInvalid,
    UserIsBlocked,
)
from pyrogram.types import (
    CallbackQuery,
    Chat,
    ChatJoinRequest,
    ChatMember,
    ChatPrivileges,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    User,
)

# ---------------------------------------------------------------------------
# CUSTOM PREMIUM EMOJI IDs (Strict Numeric IDs)
# ---------------------------------------------------------------------------
ICON_CHECK = 5985596818912712352
ICON_CROSS = 5985346521103604145
ICON_WARN = 5881702736843511327
ICON_WIFI = 5375365992891312468
ICON_DIAMOND = 5807499888245612254
ICON_CROWN = 5814374395719721769
ICON_SHIELD = 5352888345972187597
ICON_SPARKLE = 5172834782823842584
ICON_FOLDER = 5875462364110787088
ICON_STATS = 5931472654660800739
ICON_DOC = 5447421246172069841
ICON_GLOBE = 5796157163084718357
ICON_HAMMER = 5940433880585605708
ICON_SEARCH = 5429571366384842791
ICON_KEY = 6005570495603282482
ICON_MEGAPHONE = 5771695636411847302
ICON_USERS = 5942877472163892475
ICON_NEXT = 5877468380125990242
ICON_BACK = 5258236805890710909
ICON_REFRESH = 5244758760429213978
ICON_CHAT = 5884510167986343350
ICON_OUTBOX = 5877540355187937244
ICON_INBOX = 5776182936638329359
ICON_PIN = 5796440171364749940
ICON_USER = 5258011929993026890

# Standard text tags for message bodies
TG_CHECK = f'<tg-emoji emoji-id="{ICON_CHECK}">✅</tg-emoji>'
TG_CROSS = f'<tg-emoji emoji-id="{ICON_CROSS}">❌</tg-emoji>'
TG_WARN = f'<tg-emoji emoji-id="{ICON_WARN}">⚠️</tg-emoji>'
TG_WIFI = f'<tg-emoji emoji-id="{ICON_WIFI}">🛜</tg-emoji>'
TG_DIAMOND = f'<tg-emoji emoji-id="{ICON_DIAMOND}">💎</tg-emoji>'
TG_CROWN = f'<tg-emoji emoji-id="{ICON_CROWN}">👑</tg-emoji>'
TG_SHIELD = f'<tg-emoji emoji-id="{ICON_SHIELD}">🛡</tg-emoji>'
TG_SPARKLE = f'<tg-emoji emoji-id="{ICON_SPARKLE}">✨</tg-emoji>'
TG_FOLDER = f'<tg-emoji emoji-id="{ICON_FOLDER}">🗂</tg-emoji>'
TG_STATS = f'<tg-emoji emoji-id="{ICON_STATS}">📊</tg-emoji>'
TG_DOC = f'<tg-emoji emoji-id="{ICON_DOC}">📄</tg-emoji>'
TG_GLOBE = f'<tg-emoji emoji-id="{ICON_GLOBE}">🌐</tg-emoji>'
TG_HAMMER = f'<tg-emoji emoji-id="{ICON_HAMMER}">🔨</tg-emoji>'
TG_SEARCH = f'<tg-emoji emoji-id="{ICON_SEARCH}">🔎</tg-emoji>'
TG_KEY = f'<tg-emoji emoji-id="{ICON_KEY}">🔑</tg-emoji>'
TG_MEGAPHONE = f'<tg-emoji emoji-id="{ICON_MEGAPHONE}">📢</tg-emoji>'
TG_USERS = f'<tg-emoji emoji-id="{ICON_USERS}">👥</tg-emoji>'
TG_CHAT = f'<tg-emoji emoji-id="{ICON_CHAT}">💬</tg-emoji>'
TG_OUTBOX = f'<tg-emoji emoji-id="{ICON_OUTBOX}">📤</tg-emoji>'
TG_INBOX = f'<tg-emoji emoji-id="{ICON_INBOX}">📥</tg-emoji>'
TG_PIN = f'<tg-emoji emoji-id="{ICON_PIN}">📌</tg-emoji>'
TG_USER = f'<tg-emoji emoji-id="{ICON_USER}">👤</tg-emoji>'

# ---------------------------------------------------------------------------
# CONFIGURATION & ENVIRONMENT
# ---------------------------------------------------------------------------

load_dotenv()

API_ID_RAW = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "")
MONGO_URI = os.getenv("MONGO_URI") or os.getenv("DATABASE_URL") or os.getenv("MONGODB_URI", "")
BOT_NAME = os.getenv("BOT_NAME", "Channel Guard Pro")
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://t.me/BotXCore")
PORT = int(os.getenv("PORT", 8080))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

if not API_ID_RAW or not API_HASH or not BOT_TOKEN:
    sys.exit("CRITICAL: Missing API_ID, API_HASH, or BOT_TOKEN in environment variables.")

if not MONGO_URI:
    sys.exit("CRITICAL: Missing MONGO_URI in environment variables. Database connection required.")

try:
    API_ID = int(API_ID_RAW)
except ValueError:
    sys.exit("CRITICAL: API_ID must be a valid integer.")

ADMIN_IDS: set[int] = set()
for raw_id in ADMIN_IDS_RAW.split():
    raw_id = raw_id.strip()
    if raw_id.isdigit() or (raw_id.startswith("-") and raw_id[1:].isdigit()):
        ADMIN_IDS.add(int(raw_id))

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ChannelGuard")

DEFAULT_JOIN_REQUEST_TEXT = f"""┌────── ˹ {TG_SHIELD} ᴀᴄᴄᴇss ʀᴇǫᴜᴇsᴛ ˼ ─── ⏤‌●
┆
┆ {TG_WARN} ʜᴇʟʟᴏ, <b>{{mention}}</b>
┆
┆ {TG_DOC} ᴄʜᴀɴɴᴇʟ : <b>{{channel_name}}</b>
┆ {TG_KEY} sᴛᴀᴛᴜs : ᴘᴇɴᴅɪɴɢ ʀᴇᴠɪᴇᴡ
┆ {TG_DIAMOND} ᴀᴄᴛɪᴏɴ : ᴍᴀɴᴜᴀʟ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ
┆
┆ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ʜᴀs ɴᴏᴛ ʙᴇᴇɴ ᴀᴘᴘʀᴏᴠᴇᴅ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ.
┆ ᴀɴ ᴀᴅᴍɪɴɪsᴛʀᴀᴛᴏʀ ᴡɪʟʟ ʀᴇᴠɪᴇᴡ ʏᴏᴜʀ ᴀᴄᴄᴇss sʜᴏʀᴛʟʏ.
┆
└──────────────────●"""

DEFAULT_BUTTONS_JSON = json.dumps(
    [
        [
            {"text": "Support Hub", "url": SUPPORT_URL},
            {"text": "Privacy Rules", "url": "https://telegram.org/privacy"},
        ]
    ]
)

USER_STATES: Dict[int, Dict[str, Any]] = {}
CHANNELS_PER_PAGE = 5
BOT_USERNAME: str = ""

# ---------------------------------------------------------------------------
# MONGODB DATABASE ENGINE (MOTOR)
# ---------------------------------------------------------------------------


class MongoDatabase:
    def __init__(self, uri: str):
        self.uri = uri
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.channels = None
        self.users = None
        self.logs = None

    async def connect(self) -> None:
        self.client = AsyncIOMotorClient(self.uri)
        # Parse database name from URI or fallback to default
        db_name = "channel_guard_db"
        self.db = self.client.get_default_database(default=db_name)
        self.channels = self.db["channels"]
        self.users = self.db["users"]
        self.logs = self.db["join_request_logs"]

        # Ensure unique indexes
        await self.channels.create_index("channel_id", unique=True)
        await self.users.create_index("user_id", unique=True)
        logger.info("MongoDB connection active and indexes confirmed.")

    async def close(self) -> None:
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")

    async def register_user(self, user: User) -> None:
        await self.users.update_one(
            {"user_id": user.id},
            {
                "$set": {
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "updated_at": datetime.now(timezone.utc),
                },
                "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
            },
            upsert=True,
        )

    async def get_all_users(self) -> List[Dict[str, Any]]:
        cursor = self.users.find({}, {"_id": 0, "user_id": 1})
        return await cursor.to_list(length=100000)

    async def get_channel(self, channel_id: int) -> Optional[Dict[str, Any]]:
        return await self.channels.find_one({"channel_id": channel_id}, {"_id": 0})

    async def get_all_channels(self) -> List[Dict[str, Any]]:
        cursor = self.channels.find({}, {"_id": 0}).sort("channel_title", 1)
        return await cursor.to_list(length=10000)

    async def upsert_channel(
        self,
        channel_id: int,
        title: str,
        username: Optional[str],
        owner_id: Optional[int] = None,
    ) -> None:
        update_fields: Dict[str, Any] = {
            "channel_title": title,
            "channel_username": username,
            "updated_at": datetime.now(timezone.utc),
        }

        set_on_insert: Dict[str, Any] = {
            "channel_id": channel_id,
            "auto_delete_enabled": 1,
            "delete_mode": "all",
            "join_dm_enabled": 1,
            "custom_join_text": None,
            "buttons_json": None,
            "created_at": datetime.now(timezone.utc),
        }

        if owner_id and owner_id != 0:
            # Set owner if not previously set
            update_fields["owner_id"] = owner_id
        else:
            set_on_insert["owner_id"] = 0

        await self.channels.update_one(
            {"channel_id": channel_id},
            {"$set": update_fields, "$setOnInsert": set_on_insert},
            upsert=True,
        )

    async def set_channel_owner(self, channel_id: int, owner_id: int) -> None:
        await self.channels.update_one(
            {"channel_id": channel_id},
            {
                "$set": {
                    "owner_id": owner_id,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

    async def set_auto_delete(self, channel_id: int, enabled: bool) -> None:
        await self.channels.update_one(
            {"channel_id": channel_id},
            {
                "$set": {
                    "auto_delete_enabled": 1 if enabled else 0,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

    async def log_join_request(
        self,
        user_id: int,
        channel_id: int,
        channel_title: str,
        dm_status: str,
        approved: str = "NO",
        error_reason: Optional[str] = None,
    ) -> None:
        await self.logs.insert_one(
            {
                "user_id": user_id,
                "channel_id": channel_id,
                "channel_title": channel_title,
                "dm_status": dm_status,
                "approved": approved,
                "error_reason": error_reason,
                "created_at": datetime.now(timezone.utc),
            }
        )


db = MongoDatabase(MONGO_URI)

# ---------------------------------------------------------------------------
# PERMISSION AUDIT & ACCESS VERIFICATION
# ---------------------------------------------------------------------------


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def check_channel_permissions(
    client: Client, channel_id: int
) -> Tuple[bool, bool, Dict[str, bool], str]:
    """Requires: can_post_messages, can_edit_messages, can_delete_messages, can_invite_users."""
    perms = {"post": False, "edit": False, "delete": False, "invite": False}
    try:
        member: ChatMember = await client.get_chat_member(channel_id, "me")
        if member.status != ChatMemberStatus.ADMINISTRATOR:
            return False, False, perms, "Bot is not administrator"

        privs: Optional[ChatPrivileges] = member.privileges
        if not privs:
            return True, False, perms, "No privileges granted"

        perms["post"] = bool(privs.can_post_messages)
        perms["edit"] = bool(privs.can_edit_messages)
        perms["delete"] = bool(privs.can_delete_messages)
        perms["invite"] = bool(privs.can_invite_users)

        has_all_four = perms["post"] and perms["edit"] and perms["delete"] and perms["invite"]
        status_text = (
            "All 4 Permissions Active (Post, Edit, Delete, Invite)"
            if has_all_four
            else f"Missing: {', '.join([k.capitalize() for k, v in perms.items() if not v])}"
        )
        return True, has_all_four, perms, status_text
    except Exception as exc:
        return False, False, perms, str(exc)


async def can_user_manage_channel(client: Client, user_id: int, channel_id: int) -> bool:
    if is_admin(user_id):
        return True
    try:
        member = await client.get_chat_member(channel_id, user_id)
        if member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR):
            return True
        else:
            ch = await db.get_channel(channel_id)
            if ch and ch.get("owner_id") == user_id:
                await db.set_channel_owner(channel_id, 0)
            return False
    except Exception:
        return False


async def get_accessible_channels_for_user(client: Client, user_id: int) -> List[Dict[str, Any]]:
    all_channels = await db.get_all_channels()
    valid_channels = []

    for ch in all_channels:
        try:
            member = await client.get_chat_member(ch["channel_id"], user_id)
            if member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR):
                valid_channels.append(ch)
                if ch.get("owner_id") != user_id:
                    await db.set_channel_owner(ch["channel_id"], user_id)
            else:
                if ch.get("owner_id") == user_id:
                    await db.set_channel_owner(ch["channel_id"], 0)
        except Exception:
            continue

    return valid_channels


def format_template(
    template: str,
    user: Optional[User] = None,
    channel: Optional[Union[Chat, Dict[str, Any]]] = None,
) -> str:
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    u_id = str(user.id) if user else "123456789"
    first = html.escape(user.first_name) if user and user.first_name else "User"
    last = html.escape(user.last_name) if user and user.last_name else ""
    uname = f"@{html.escape(user.username)}" if user and user.username else "N/A"
    mention = user.mention if user else f'<a href="tg://user?id={u_id}">{first}</a>'

    if isinstance(channel, Chat):
        c_id = str(channel.id)
        c_name = html.escape(channel.title or "Channel")
        c_uname = f"@{channel.username}" if channel.username else "Private"
    elif isinstance(channel, dict):
        c_id = str(channel.get("channel_id", "-1000000000000"))
        c_name = html.escape(channel.get("channel_title") or "Channel")
        c_uname = (
            f"@{channel.get('channel_username')}"
            if channel.get("channel_username")
            else "Private"
        )
    else:
        c_id = "-1000000000000"
        c_name = "Target Channel"
        c_uname = "@channel"

    mapping = {
        "user_id": u_id,
        "first_name": first,
        "last_name": last,
        "username": uname,
        "mention": mention,
        "channel_id": c_id,
        "channel_name": c_name,
        "channel_username": c_uname,
        "request_time": now_utc,
        "bot_name": html.escape(BOT_NAME),
    }

    class SafeFormatDict(dict):
        def __missing__(self, key: str) -> str:
            return f"{{{key}}}"

    return template.format_map(SafeFormatDict(mapping))


def parse_buttons(raw_json: Optional[str]) -> Optional[InlineKeyboardMarkup]:
    if not raw_json:
        return None
    try:
        data = json.loads(raw_json)
        if not isinstance(data, list):
            return None
        keyboard: List[List[InlineKeyboardButton]] = []
        for row in data:
            if not isinstance(row, list):
                continue
            button_row: List[InlineKeyboardButton] = []
            for btn in row:
                if isinstance(btn, dict) and "text" in btn and "url" in btn:
                    button_row.append(
                        InlineKeyboardButton(
                            text=btn["text"],
                            url=btn["url"],
                            icon_custom_emoji_id=ICON_GLOBE,
                        )
                    )
            if button_row:
                keyboard.append(button_row)
        return InlineKeyboardMarkup(keyboard) if keyboard else None
    except Exception:
        return None


async def safe_edit_message(
    query: CallbackQuery, text: str, reply_markup: Optional[InlineKeyboardMarkup] = None
) -> None:
    try:
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    except MessageNotModified:
        pass
    except Exception as e:
        logger.warning(f"Error editing message: {e}")


# ---------------------------------------------------------------------------
# INTERFACE KEYBOARDS (PURE TEXT LABELS + NATIVE BUTTONSTYLE + ICONS)
# ---------------------------------------------------------------------------


def get_home_keyboard(is_superadmin: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text="My Channels",
                callback_data="channels_page_my_1",
                icon_custom_emoji_id=ICON_FOLDER,
                style=ButtonStyle.PRIMARY,
            ),
            InlineKeyboardButton(
                text="Link Channel",
                callback_data="prompt_add_channel",
                icon_custom_emoji_id=ICON_KEY,
                style=ButtonStyle.PRIMARY,
            ),
        ],
        [
            InlineKeyboardButton(
                text="How It Works",
                callback_data="nav_how_it_works",
                icon_custom_emoji_id=ICON_DOC,
                style=ButtonStyle.PRIMARY,
            ),
            InlineKeyboardButton(
                text="Support Hub",
                url=SUPPORT_URL,
                icon_custom_emoji_id=ICON_GLOBE,
            ),
        ],
    ]

    if is_superadmin:
        rows.append(
            [
                InlineKeyboardButton(
                    text="Global Channels",
                    callback_data="channels_page_all_1",
                    icon_custom_emoji_id=ICON_GLOBE,
                    style=ButtonStyle.PRIMARY,
                ),
                InlineKeyboardButton(
                    text="System Status",
                    callback_data="nav_status",
                    icon_custom_emoji_id=ICON_STATS,
                    style=ButtonStyle.PRIMARY,
                ),
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text="Admin Suite",
                    callback_data="cmd_admin",
                    icon_custom_emoji_id=ICON_CROWN,
                    style=ButtonStyle.PRIMARY,
                )
            ]
        )
    return InlineKeyboardMarkup(rows)


def get_link_channel_menu_keyboard() -> InlineKeyboardMarkup:
    protect_url = (
        f"https://t.me/{BOT_USERNAME}?startchannel=true&admin=post_messages+edit_messages+delete_messages+invite_users"
    )
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="Protect Channel",
                    url=protect_url,
                    icon_custom_emoji_id=ICON_SHIELD,
                )
            ],
            [
                InlineKeyboardButton(
                    text="Back to Menu",
                    callback_data="nav_home",
                    icon_custom_emoji_id=ICON_BACK,
                    style=ButtonStyle.DANGER,
                )
            ],
        ]
    )


def build_channel_pagination_keyboard(
    channels: List[Dict[str, Any]], page: int, scope: str
) -> InlineKeyboardMarkup:
    total_channels = len(channels)
    total_pages = max(1, (total_channels + CHANNELS_PER_PAGE - 1) // CHANNELS_PER_PAGE)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * CHANNELS_PER_PAGE
    end_idx = start_idx + CHANNELS_PER_PAGE
    page_channels = channels[start_idx:end_idx]

    kb: List[List[InlineKeyboardButton]] = []
    for ch in page_channels:
        kb.append(
            [
                InlineKeyboardButton(
                    text=ch["channel_title"],
                    callback_data=f"view_channel_{ch['channel_id']}_{scope}_{page}",
                    icon_custom_emoji_id=ICON_FOLDER,
                    style=ButtonStyle.PRIMARY,
                )
            ]
        )

    nav_row: List[InlineKeyboardButton] = []
    if page > 1:
        nav_row.append(
            InlineKeyboardButton(
                text="Prev",
                callback_data=f"channels_page_{scope}_{page - 1}",
                icon_custom_emoji_id=ICON_BACK,
                style=ButtonStyle.PRIMARY,
            )
        )
    nav_row.append(
        InlineKeyboardButton(
            text=f"{page}/{total_pages}",
            callback_data=f"channels_page_{scope}_{page}",
            icon_custom_emoji_id=ICON_STATS,
            style=ButtonStyle.PRIMARY,
        )
    )
    if page < total_pages:
        nav_row.append(
            InlineKeyboardButton(
                text="Next",
                callback_data=f"channels_page_{scope}_{page + 1}",
                icon_custom_emoji_id=ICON_NEXT,
                style=ButtonStyle.PRIMARY,
            )
        )

    kb.append(nav_row)
    kb.append(
        [
            InlineKeyboardButton(
                text="Refresh",
                callback_data=f"channels_page_{scope}_{page}",
                icon_custom_emoji_id=ICON_REFRESH,
                style=ButtonStyle.PRIMARY,
            ),
            InlineKeyboardButton(
                text="Main Menu",
                callback_data="nav_home",
                icon_custom_emoji_id=ICON_BACK,
                style=ButtonStyle.DANGER,
            ),
        ]
    )
    return InlineKeyboardMarkup(kb)


def get_channel_management_panel(
    channel_id: int, auto_delete: bool, scope: str = "my", page: int = 1
) -> InlineKeyboardMarkup:
    if auto_delete:
        ad_btn = InlineKeyboardButton(
            text="Auto-Delete: ON",
            callback_data=f"toggle_ad_off_{channel_id}_{scope}_{page}",
            icon_custom_emoji_id=ICON_CHECK,
            style=ButtonStyle.SUCCESS,
        )
    else:
        ad_btn = InlineKeyboardButton(
            text="Auto-Delete: OFF",
            callback_data=f"toggle_ad_on_{channel_id}_{scope}_{page}",
            icon_custom_emoji_id=ICON_CROSS,
            style=ButtonStyle.DANGER,
        )

    return InlineKeyboardMarkup(
        [
            [ad_btn],
            [
                InlineKeyboardButton(
                    text="Refresh Status",
                    callback_data=f"view_channel_{channel_id}_{scope}_{page}",
                    icon_custom_emoji_id=ICON_REFRESH,
                    style=ButtonStyle.PRIMARY,
                ),
                InlineKeyboardButton(
                    text="Channel List",
                    callback_data=f"channels_page_{scope}_{page}",
                    icon_custom_emoji_id=ICON_BACK,
                    style=ButtonStyle.PRIMARY,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Support Hub",
                    url=SUPPORT_URL,
                    icon_custom_emoji_id=ICON_GLOBE,
                )
            ],
        ]
    )


def get_admin_suite_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="Channel Broadcast",
                    callback_data="bc_menu_channels",
                    icon_custom_emoji_id=ICON_MEGAPHONE,
                    style=ButtonStyle.PRIMARY,
                ),
                InlineKeyboardButton(
                    text="User Broadcast",
                    callback_data="bc_menu_users",
                    icon_custom_emoji_id=ICON_USERS,
                    style=ButtonStyle.PRIMARY,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Global Broadcast (All)",
                    callback_data="bc_menu_global",
                    icon_custom_emoji_id=ICON_GLOBE,
                    style=ButtonStyle.PRIMARY,
                )
            ],
            [
                InlineKeyboardButton(
                    text="Global Channels",
                    callback_data="channels_page_all_1",
                    icon_custom_emoji_id=ICON_FOLDER,
                    style=ButtonStyle.PRIMARY,
                ),
                InlineKeyboardButton(
                    text="System Audit",
                    callback_data="nav_status",
                    icon_custom_emoji_id=ICON_STATS,
                    style=ButtonStyle.PRIMARY,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Support Hub",
                    url=SUPPORT_URL,
                    icon_custom_emoji_id=ICON_GLOBE,
                ),
                InlineKeyboardButton(
                    text="Main Menu",
                    callback_data="nav_home",
                    icon_custom_emoji_id=ICON_BACK,
                    style=ButtonStyle.DANGER,
                ),
            ],
        ]
    )


# ---------------------------------------------------------------------------
# CLIENT INSTANCE
# ---------------------------------------------------------------------------

app = Client(
    name="channel_guard_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    sleep_threshold=10,
)

# ---------------------------------------------------------------------------
# JOIN REQUEST DM ENGINE
# ---------------------------------------------------------------------------


@app.on_chat_join_request()
async def on_join_request(client: Client, request: ChatJoinRequest) -> None:
    user: User = request.from_user
    chat: Chat = request.chat

    await db.register_user(user)
    await db.upsert_channel(chat.id, chat.title, chat.username)

    channel_row = await db.get_channel(chat.id)
    join_dm_enabled = (
        bool(channel_row.get("join_dm_enabled"))
        if channel_row and "join_dm_enabled" in channel_row
        else True
    )

    if not join_dm_enabled:
        return

    template = (
        channel_row.get("custom_join_text")
        if channel_row and channel_row.get("custom_join_text")
        else DEFAULT_JOIN_REQUEST_TEXT
    )
    formatted_dm = format_template(template, user=user, channel=chat)
    keyboard = parse_buttons(
        channel_row.get("buttons_json") if channel_row else DEFAULT_BUTTONS_JSON
    )

    try:
        await client.send_message(
            chat_id=user.id,
            text=formatted_dm,
            reply_markup=keyboard,
        )
        logger.info(f"[JOIN_REQUEST] DM Sent to user {user.id} for channel {chat.id}.")
        await db.log_join_request(user.id, chat.id, chat.title, "SUCCESS", "NO", None)
    except UserIsBlocked:
        logger.warning(f"[JOIN_REQUEST] User {user.id} blocked the bot. Skipped.")
        await db.log_join_request(user.id, chat.id, chat.title, "FAILED", "NO", "USER_IS_BLOCKED")
    except Exception as exc:
        logger.error(f"[JOIN_REQUEST] DM delivery failure for {user.id}: {exc}")
        await db.log_join_request(user.id, chat.id, chat.title, "FAILED", "NO", str(exc))


# ---------------------------------------------------------------------------
# AUTO-DELETE ENGINE (STRICT 4-WAY REQUIRED RIGHTS)
# ---------------------------------------------------------------------------


async def process_channel_message_deletion(
    client: Client, message: Message, event_type: str = "POST"
) -> None:
    chat: Chat = message.chat

    sender_id = message.from_user.id if message.from_user else 0
    await db.upsert_channel(chat.id, chat.title, chat.username, owner_id=sender_id if sender_id else None)

    channel_row = await db.get_channel(chat.id)
    if not channel_row or not channel_row.get("auto_delete_enabled"):
        return

    # Check strict 4 rights (Post, Edit, Delete, Invite)
    is_adm, has_all_four, perms, status_text = await check_channel_permissions(client, chat.id)

    if not is_adm or not has_all_four:
        logger.warning(
            f"[AUTO_DELETE] Skipped {event_type} {message.id} in '{chat.title}' ({chat.id}) - "
            f"Requires Post, Edit, Delete & Invite permissions. Status: {status_text}"
        )
        return

    await asyncio.sleep(1.2)
    try:
        await message.delete()
        logger.info(f"[AUTO_DELETE] Purged {event_type} {message.id} from '{chat.title}'")
    except MessageDeleteForbidden:
        logger.warning(
            f"[AUTO_DELETE] Forbidden: Cannot delete {event_type} {message.id} in channel {chat.id}"
        )
    except FloodWait as flood:
        await asyncio.sleep(flood.value)
        try:
            await message.delete()
        except Exception:
            pass
    except Exception as exc:
        logger.error(f"[AUTO_DELETE] Deletion failure on {event_type} {message.id}: {exc}")


@app.on_message(filters.channel)
async def on_channel_new_message(client: Client, message: Message) -> None:
    await process_channel_message_deletion(client, message, event_type="POST")


@app.on_edited_message(filters.channel)
async def on_channel_edited_message(client: Client, message: Message) -> None:
    await process_channel_message_deletion(client, message, event_type="EDIT")


# ---------------------------------------------------------------------------
# COMMAND HANDLERS
# ---------------------------------------------------------------------------


@app.on_message(filters.command("start") & filters.private)
async def cmd_start_handler(client: Client, message: Message) -> None:
    user: User = message.from_user
    await db.register_user(user)

    is_super = is_admin(user.id)
    welcome_text = f"""┌────── ˹ {TG_SHIELD} <b>{html.escape(BOT_NAME)}</b> ˼ ─── ⏤‌●
┆
┆ {TG_KEY} ᴡᴇʟᴄᴏᴍᴇ, <b>{html.escape(user.first_name)}</b>
┆
┆ {TG_HAMMER} ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟs
┆ {TG_CHECK} sᴛʀɪᴄᴛ 4-ᴡᴀʏ ᴘᴇʀᴍɪssɪᴏɴ ɢᴜᴀʀᴅ
┆ {TG_SHIELD} ᴀᴜᴛᴏ-ᴘᴜʀɢᴇs ɴᴇᴡ & ᴇᴅɪᴛᴇᴅ ᴍᴇssᴀɢᴇs
┆
┆ sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ғʀᴏᴍ ᴛʜᴇ ᴍᴇɴᴜ ʙᴇʟᴏᴡ:
┆
└──────────────────●"""

    await message.reply_text(welcome_text, reply_markup=get_home_keyboard(is_superadmin=is_super))


@app.on_message(filters.command("admin") & filters.private)
async def cmd_admin_handler(client: Client, message: Message) -> None:
    user: User = message.from_user
    if not is_admin(user.id):
        await message.reply_text(f"{TG_CROSS} Access denied. Unauthorized administrator ID.")
        return

    admin_panel_text = f"""┌────── ˹ {TG_CROWN} <b>ᴇxᴇᴄᴜᴛɪᴠᴇ sᴜɪᴛᴇ</b> ˼ ─── ⏤‌●
┆
┆ {TG_MEGAPHONE} <b>ᴄʜᴀɴɴᴇʟ ʙʀᴏᴀᴅᴄᴀsᴛ :</b> ᴘᴜsʜ ᴛᴏ ᴀʟʟ ᴄʜᴀɴɴᴇʟs
┆ {TG_USERS} <b>ᴜsᴇʀ ʙʀᴏᴀᴅᴄᴀsᴛ :</b> ᴍᴇssᴀɢᴇ ᴀʟʟ ᴜsᴇʀs
┆ {TG_GLOBE} <b>ɢʟᴏʙᴀʟ ʙʀᴏᴀᴅᴄᴀsᴛ :</b> ʙᴏᴛʜ ᴜsᴇʀs & ᴄʜᴀɴɴᴇʟs
┆ {TG_STATS} <b>sʏsᴛᴇᴍ ᴀᴜᴅɪᴛ :</b> ʜᴇᴀʟᴛʜ & ᴘᴇʀᴍɪssɪᴏɴ ᴄʜᴇᴄᴋ
┆
┆ sᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴏᴘᴇʀᴀᴛɪᴏɴ :
┆
└──────────────────●"""

    await message.reply_text(admin_panel_text, reply_markup=get_admin_suite_keyboard())


# ---------------------------------------------------------------------------
# FORWARDED CHANNEL LINKING & BROADCAST DELIVERY
# ---------------------------------------------------------------------------


async def deliver_message(
    client: Client, target_id: int, message: Message, pin: bool = False, forward: bool = False
) -> bool:
    try:
        if forward:
            sent_msg = await message.forward(target_id)
        else:
            sent_msg = await client.copy_message(
                chat_id=target_id,
                from_chat_id=message.chat.id,
                message_id=message.id,
            )
        if pin:
            try:
                await sent_msg.pin(both_sides=True)
            except Exception:
                pass
        return True
    except FloodWait as flood:
        await asyncio.sleep(flood.value)
        return await deliver_message(client, target_id, message, pin, forward)
    except Exception:
        return False


@app.on_message(filters.private & ~filters.command(["start", "admin"]))
async def on_private_interactive_input(client: Client, message: Message) -> None:
    user_id = message.from_user.id
    state = USER_STATES.get(user_id, {})
    action = state.get("action")

    # Channel Linking via Forwarded Post or @Username / ID
    if action == "manual_add_channel" or message.forward_from_chat:
        target_chat_id: Optional[Union[int, str]] = None
        target_chat_title: Optional[str] = None
        target_chat_username: Optional[str] = None

        if message.forward_from_chat:
            if message.forward_from_chat.type != ChatType.CHANNEL:
                await message.reply_text(f"{TG_CROSS} That forwarded message is not from a Channel.")
                USER_STATES.pop(user_id, None)
                return
            target_chat_id = message.forward_from_chat.id
            target_chat_title = message.forward_from_chat.title
            target_chat_username = message.forward_from_chat.username
        elif message.text:
            query_val = message.text.strip()
            try:
                chat_obj: Chat = await client.get_chat(query_val)
                if chat_obj.type != ChatType.CHANNEL:
                    await message.reply_text(f"{TG_CROSS} That entity is not a Telegram Channel.")
                    USER_STATES.pop(user_id, None)
                    return
                target_chat_id = chat_obj.id
                target_chat_title = chat_obj.title
                target_chat_username = chat_obj.username
            except Exception as e:
                await message.reply_text(f"{TG_CROSS} Could not find channel: {e}")
                USER_STATES.pop(user_id, None)
                return

        if target_chat_id:
            try:
                member = await client.get_chat_member(target_chat_id, user_id)
                if member.status not in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR) and not is_admin(user_id):
                    await message.reply_text(f"{TG_CROSS} You are not an administrator in that channel.")
                    USER_STATES.pop(user_id, None)
                    return

                await db.upsert_channel(
                    target_chat_id,
                    target_chat_title or "Channel",
                    target_chat_username,
                    owner_id=user_id,
                )
                await db.set_channel_owner(target_chat_id, user_id)

                await message.reply_text(
                    f"{TG_CHECK} <b>Channel Linked Successfully!</b>\n\n"
                    f"{TG_DOC} <b>Title:</b> {html.escape(target_chat_title or 'Channel')}\n"
                    f"{TG_KEY} <b>ID:</b> <code>{target_chat_id}</code>\n\n"
                    f"You can now manage it under <b>My Channels</b>."
                )
            except Exception as exc:
                await message.reply_text(f"{TG_CROSS} Error verifying channel membership: {exc}")
            finally:
                USER_STATES.pop(user_id, None)
            return

    # Broadcast Flow (Admin Only)
    if not is_admin(user_id):
        return

    if action in ("broadcast_channels", "broadcast_users", "broadcast_global"):
        pin_it = state.get("pin", False)
        fwd_it = state.get("forward", False)

        targets_desc = {
            "broadcast_channels": "Channels",
            "broadcast_users": "Users",
            "broadcast_global": "Users + Channels",
        }[action]

        status_msg = await message.reply(f"{TG_SPARKLE} Dispatching broadcast to {targets_desc}...")
        sent, failed = 0, 0

        target_ids = []
        if action in ("broadcast_channels", "broadcast_global"):
            channels = await db.get_all_channels()
            target_ids.extend([ch["channel_id"] for ch in channels])

        if action in ("broadcast_users", "broadcast_global"):
            users = await db.get_all_users()
            target_ids.extend([u["user_id"] for u in users])

        for target_id in set(target_ids):
            ok = await deliver_message(client, target_id, message, pin_it, fwd_it)
            if ok:
                sent += 1
            else:
                failed += 1
            await asyncio.sleep(0.15)

        del USER_STATES[user_id]
        await status_msg.edit_text(
            f"┌────── ˹ {TG_CHECK} <b>ʙʀᴏᴀᴅᴄᴀsᴛ ᴅᴏɴᴇ</b> ˼ ─── ⏤‌●\n"
            f"┆\n"
            f"┆ {TG_DIAMOND} ᴛᴀʀɢᴇᴛ : <b>{targets_desc}</b>\n"
            f"┆ {TG_CHECK} ᴅᴇʟɪᴠᴇʀᴇᴅ : <b>{sent}</b>\n"
            f"┆ {TG_CROSS} ғᴀɪʟᴇᴅ : <b>{failed}</b>\n"
            f"┆\n"
            f"└──────────────────●"
        )


# ---------------------------------------------------------------------------
# CALLBACK QUERY ROUTING (PAGINATION & STRICT SECURITY)
# ---------------------------------------------------------------------------


@app.on_callback_query()
async def on_callback(client: Client, query: CallbackQuery) -> None:
    user_id = query.from_user.id
    data = query.data or ""

    if data == "nav_home":
        text = f"""┌────── ˹ {TG_SHIELD} <b>ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ</b> ˼ ─── ⏤‌‌●
┆
┆ {TG_KEY} ᴍᴀɪɴ ᴅᴀsʜʙᴏᴀʀᴅ
┆ sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ғʀᴏᴍ ᴛʜᴇ ᴍᴇɴᴜ :
┆
└──────────────────●"""
        await safe_edit_message(query, text, reply_markup=get_home_keyboard(is_superadmin=is_admin(user_id)))
        await query.answer()
        return

    if data == "prompt_add_channel":
        USER_STATES[user_id] = {"action": "manual_add_channel"}
        instructions = f"""┌────── ˹ {TG_KEY} <b>ʟɪɴᴋ ᴄʜᴀɴɴᴇʟ</b> ˼ ─── ⏤‌●
┆
┆ <b>Option 1 (One-Click Setup):</b>
┆ Tap <b>Protect Channel</b> below to add the bot with all 4 required rights pre-selected.
┆
┆ <b>Option 2 (Private & Public Channels):</b>
┆ Forward any message from your channel directly to this chat.
┆
┆ <b>Option 3 (Public Channels):</b>
┆ Send the channel <b>@username</b> or <b>Numeric ID</b> (e.g. <code>-100...</code>).
┆
└──────────────────●"""
        await safe_edit_message(query, instructions, reply_markup=get_link_channel_menu_keyboard())
        await query.answer()
        return

    if data == "cmd_admin":
        if not is_admin(user_id):
            await query.answer("Access denied.", show_alert=True)
            return
        admin_panel_text = f"""┌────── ˹ {TG_CROWN} <b>ᴇxᴇᴄᴜᴛɪᴠᴇ sᴜɪᴛᴇ</b> ˼ ─── ⏤‌●
┆
┆ {TG_MEGAPHONE} <b>ᴄʜᴀɴɴᴇʟ ʙʀᴏᴀᴅᴄᴀsᴛ :</b> ᴘᴜsʜ ᴛᴏ ᴀʟʟ ᴄʜᴀɴɴᴇʟs
┆ {TG_USERS} <b>ᴜsᴇʀ ʙʀᴏᴀᴅᴄᴀsᴛ :</b> ᴍᴇssᴀɢᴇ ᴀʟʟ ᴜsᴇʀs
┆ {TG_GLOBE} <b>ɢʟᴏʙᴀʟ ʙʀᴏᴀᴅᴄᴀsᴛ :</b> ʙᴏᴛʜ ᴜsᴇʀs & ᴄʜᴀɴɴᴇʟs
┆ {TG_STATS} <b>sʏsᴛᴇᴍ ᴀᴜᴅɪᴛ :</b> ʜᴇᴀʟᴛʜ & ᴘᴇʀᴍɪssɪᴏɴ ᴄʜᴇᴄᴋ
┆
┆ sᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴏᴘᴇʀᴀᴛɪᴏɴ :
┆
└──────────────────●"""
        await safe_edit_message(query, admin_panel_text, reply_markup=get_admin_suite_keyboard())
        await query.answer()
        return

    if data == "nav_how_it_works":
        text = f"""┌────── ˹ {TG_DOC} <b>ʜᴏᴡ ɪᴛ ᴡᴏʀᴋs</b> ˼ ─── ⏤‌‌●
┆
┆ {TG_CHECK} <b>sᴛʀɪᴄᴛ 4-ᴡᴀʏ ᴘᴇʀᴍɪssɪᴏɴs:</b>
┆ The bot works ONLY if all 4 permissions are granted:
┆ • <b>Post Messages</b>
┆ • <b>Edit Messages</b>
┆ • <b>Delete Messages</b>
┆ • <b>Invite Users via Link</b>
┆
┆ {TG_HAMMER} <b>ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛɪᴏɴ:</b>
┆ Purges new posts and edited messages within 2 seconds.
┆
└──────────────────●"""
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="My Channels",
                        callback_data="channels_page_my_1",
                        icon_custom_emoji_id=ICON_FOLDER,
                        style=ButtonStyle.PRIMARY,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Support Hub",
                        url=SUPPORT_URL,
                        icon_custom_emoji_id=ICON_GLOBE,
                    ),
                    InlineKeyboardButton(
                        text="Back",
                        callback_data="nav_home",
                        icon_custom_emoji_id=ICON_BACK,
                        style=ButtonStyle.DANGER,
                    ),
                ],
            ]
        )
        await safe_edit_message(query, text, reply_markup=kb)
        await query.answer()
        return

    # Dynamic Multi-Channel Pagination
    if data.startswith("channels_page_"):
        parts = data.split("_")
        scope = parts[2]
        page = int(parts[3])

        if scope == "all" and not is_admin(user_id):
            await query.answer("Access denied.", show_alert=True)
            return

        channels = (
            await db.get_all_channels()
            if scope == "all"
            else await get_accessible_channels_for_user(client, user_id)
        )

        if not channels:
            protect_url = (
                f"https://t.me/{BOT_USERNAME}?startchannel=true&admin=post_messages+edit_messages+delete_messages+invite_users"
            )
            text = (
                f"┌────── ˹ {TG_WARN} <b>ɴᴏ ᴄʜᴀɴɴᴇʟs ғᴏᴜɴᴅ</b> ˼ ─── ⏤‌‌●\n"
                f"┆\n"
                f"┆ <b>To link your channel:</b>\n"
                f"┆ 1. Tap <b>Protect Channel</b> to add bot with all rights.\n"
                f"┆ 2. Or forward any message from your channel here.\n"
                f"┆\n"
                f"└──────────────────●"
            )
            kb = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Protect Channel",
                            url=protect_url,
                            icon_custom_emoji_id=ICON_SHIELD,
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Link Channel",
                            callback_data="prompt_add_channel",
                            icon_custom_emoji_id=ICON_KEY,
                            style=ButtonStyle.PRIMARY,
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Check Again",
                            callback_data=f"channels_page_{scope}_1",
                            icon_custom_emoji_id=ICON_SEARCH,
                            style=ButtonStyle.PRIMARY,
                        ),
                        InlineKeyboardButton(
                            text="Back",
                            callback_data="nav_home",
                            icon_custom_emoji_id=ICON_BACK,
                            style=ButtonStyle.DANGER,
                        ),
                    ],
                ]
            )
            await safe_edit_message(query, text, reply_markup=kb)
            await query.answer()
            return

        scope_title = "ɢʟᴏʙᴀʟ ᴄʜᴀɴɴᴇʟs" if scope == "all" else "ᴍʏ ᴄʜᴀɴɴᴇʟs"
        text = (
            f"┌────── ˹ {TG_FOLDER} <b>{scope_title}</b> ˼ ─── ⏤‌●\n"
            f"┆\n"
            f"┆ sᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴄᴏɴғɪɢᴜʀᴇ :\n"
            f"┆\n"
            f"└──────────────────●"
        )
        kb = build_channel_pagination_keyboard(channels, page=page, scope=scope)
        await safe_edit_message(query, text, reply_markup=kb)
        await query.answer()
        return

    # System Status (Superadmin/Owner only)
    if data == "nav_status":
        if not is_admin(user_id):
            await query.answer("Access denied.", show_alert=True)
            return

        channels = await db.get_all_channels()
        all_users = await db.get_all_users()

        report = (
            f"┌────── ˹ {TG_STATS} <b>sʏsᴛᴇᴍ ᴀᴜᴅɪᴛ</b> ˼ ─── ⏤‌●\n"
            f"┆\n"
            f"┆ {TG_WIFI} ᴅᴀᴛᴀʙᴀsᴇ : {TG_CHECK} ᴏɴʟɪɴᴇ (ᴍᴏɴɢᴏᴅʙ)\n"
            f"┆ {TG_SHIELD} ᴘʀᴏᴛᴇᴄᴛᴇᴅ ᴄʜᴀɴɴᴇʟs : <b>{len(channels)}</b>\n"
            f"┆ {TG_USERS} ʀᴇɢɪsᴛᴇʀᴇᴅ ᴜsᴇʀs : <b>{len(all_users)}</b>\n"
            f"┆\n"
            f"┆ <b>ᴄʜᴀɴɴᴇʟ ʜᴇᴀʟᴛʜ [P / E / D / I]:</b>\n"
        )
        for ch in channels:
            is_adm, has_all_four, perms, _ = await check_channel_permissions(client, ch["channel_id"])
            p_icon = TG_CHECK if perms["post"] else TG_CROSS
            e_icon = TG_CHECK if perms["edit"] else TG_CROSS
            d_icon = TG_CHECK if perms["delete"] else TG_CROSS
            i_icon = TG_CHECK if perms["invite"] else TG_CROSS
            ad_icon = TG_CHECK if ch.get("auto_delete_enabled") else TG_CROSS

            report += f"┆ <b>{html.escape(ch['channel_title'])}:</b> [{p_icon}{e_icon}{d_icon}{i_icon}] | Purge: {ad_icon}\n"

        report += "┆\n└──────────────────●"

        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Refresh",
                        callback_data="nav_status",
                        icon_custom_emoji_id=ICON_REFRESH,
                        style=ButtonStyle.PRIMARY,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Back",
                        callback_data="nav_home",
                        icon_custom_emoji_id=ICON_BACK,
                        style=ButtonStyle.DANGER,
                    )
                ],
            ]
        )
        await safe_edit_message(query, report, reply_markup=kb)
        await query.answer()
        return

    if data.startswith("view_channel_"):
        parts = data.split("_")
        c_id = int(parts[2])
        scope = parts[3]
        page = int(parts[4])

        if not await can_user_manage_channel(client, user_id, c_id):
            await query.answer("Access revoked: You are no longer an administrator in this channel.", show_alert=True)
            channels = await get_accessible_channels_for_user(client, user_id)
            kb = build_channel_pagination_keyboard(channels, page=1, scope="my")
            await safe_edit_message(query, f"{TG_WARN} <b>Access Revoked. Updated channel list:</b>", reply_markup=kb)
            return

        await display_channel_controller(client, query, c_id, scope=scope, page=page)
        await query.answer()
        return

    if data.startswith("toggle_ad_"):
        parts = data.split("_")
        action = parts[2]
        c_id = int(parts[3])
        scope = parts[4]
        page = int(parts[5])

        if not await can_user_manage_channel(client, user_id, c_id):
            await query.answer("Access revoked: You are no longer an administrator in this channel.", show_alert=True)
            return

        await db.set_auto_delete(c_id, action == "on")
        await display_channel_controller(client, query, c_id, scope=scope, page=page)
        await query.answer(f"Auto-Delete {'ENABLED' if action == 'on' else 'DISABLED'}")
        return

    # Broadcast Menu Routing (Admin Only)
    if data == "bc_menu_channels":
        if not is_admin(user_id):
            await query.answer("Access denied.", show_alert=True)
            return
        text = (
            f"┌────── ˹ {TG_MEGAPHONE} <b>ᴄʜᴀɴɴᴇʟ ʙʀᴏᴀᴅᴄᴀsᴛ</b> ˼ ─── ⏤‌‌●\n"
            f"┆\n"
            f"┆ sᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴅᴇʟɪᴠᴇʀʏ ᴍᴏᴅᴇ :\n"
            f"┆\n"
            f"└──────────────────●"
        )
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Clean Copy",
                        callback_data="bc_opt_ch_clean",
                        icon_custom_emoji_id=ICON_OUTBOX,
                        style=ButtonStyle.PRIMARY,
                    ),
                    InlineKeyboardButton(
                        text="Post & Pin",
                        callback_data="bc_opt_ch_pin",
                        icon_custom_emoji_id=ICON_PIN,
                        style=ButtonStyle.PRIMARY,
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="Back",
                        callback_data="cmd_admin",
                        icon_custom_emoji_id=ICON_BACK,
                        style=ButtonStyle.DANGER,
                    )
                ],
            ]
        )
        await safe_edit_message(query, text, reply_markup=kb)
        await query.answer()
        return

    if data == "bc_menu_users":
        if not is_admin(user_id):
            await query.answer("Access denied.", show_alert=True)
            return
        text = (
            f"┌────── ˹ {TG_USERS} <b>ᴜsᴇʀ ʙʀᴏᴀᴅᴄᴀsᴛ</b> ˼ ─── ⏤‌●\n"
            f"┆\n"
            f"┆ sᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴅᴇʟɪᴠᴇʀʏ ᴍᴏᴅᴇ :\n"
            f"┆\n"
            f"└──────────────────●"
        )
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Clean Copy",
                        callback_data="bc_opt_usr_clean",
                        icon_custom_emoji_id=ICON_OUTBOX,
                        style=ButtonStyle.PRIMARY,
                    ),
                    InlineKeyboardButton(
                        text="Forwarded Post",
                        callback_data="bc_opt_usr_forward",
                        icon_custom_emoji_id=ICON_NEXT,
                        style=ButtonStyle.PRIMARY,
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="Back",
                        callback_data="cmd_admin",
                        icon_custom_emoji_id=ICON_BACK,
                        style=ButtonStyle.DANGER,
                    )
                ],
            ]
        )
        await safe_edit_message(query, text, reply_markup=kb)
        await query.answer()
        return

    if data == "bc_menu_global":
        if not is_admin(user_id):
            await query.answer("Access denied.", show_alert=True)
            return
        text = (
            f"┌────── ˹ {TG_GLOBE} <b>ɢʟᴏʙᴀʟ ʙʀᴏᴀᴅᴄᴀsᴛ</b> ˼ ─── ⏤‌‌●\n"
            f"┆\n"
            f"┆ ʙᴏᴛʜ ᴜsᴇʀs & ᴄʜᴀɴɴᴇʟs :\n"
            f"┆\n"
            f"└──────────────────●"
        )
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Clean Copy",
                        callback_data="bc_opt_glob_clean",
                        icon_custom_emoji_id=ICON_OUTBOX,
                        style=ButtonStyle.PRIMARY,
                    ),
                    InlineKeyboardButton(
                        text="Forwarded Post",
                        callback_data="bc_opt_glob_forward",
                        icon_custom_emoji_id=ICON_NEXT,
                        style=ButtonStyle.PRIMARY,
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="Back",
                        callback_data="cmd_admin",
                        icon_custom_emoji_id=ICON_BACK,
                        style=ButtonStyle.DANGER,
                    )
                ],
            ]
        )
        await safe_edit_message(query, text, reply_markup=kb)
        await query.answer()
        return

    if data.startswith("bc_opt_"):
        if not is_admin(user_id):
            await query.answer("Access denied.", show_alert=True)
            return

        opt = data.replace("bc_opt_", "")
        if opt == "ch_clean":
            USER_STATES[user_id] = {"action": "broadcast_channels", "pin": False, "forward": False}
        elif opt == "ch_pin":
            USER_STATES[user_id] = {"action": "broadcast_channels", "pin": True, "forward": False}
        elif opt == "usr_clean":
            USER_STATES[user_id] = {"action": "broadcast_users", "pin": False, "forward": False}
        elif opt == "usr_forward":
            USER_STATES[user_id] = {"action": "broadcast_users", "pin": False, "forward": True}
        elif opt == "glob_clean":
            USER_STATES[user_id] = {"action": "broadcast_global", "pin": False, "forward": False}
        elif opt == "glob_forward":
            USER_STATES[user_id] = {"action": "broadcast_global", "pin": False, "forward": True}

        await query.message.reply(
            f"{TG_INBOX} <b>Send the message or media to broadcast now:</b>\n"
            f"<i>(All premium emojis and formatting are preserved)</i>"
        )
        await query.answer()
        return


async def display_channel_controller(
    client: Client, query: CallbackQuery, channel_id: int, scope: str = "my", page: int = 1
) -> None:
    ch = await db.get_channel(channel_id)
    if not ch:
        text = f"{TG_WARN} Channel record not found."
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Channels",
                        callback_data=f"channels_page_{scope}_{page}",
                        icon_custom_emoji_id=ICON_BACK,
                        style=ButtonStyle.PRIMARY,
                    )
                ]
            ]
        )
        await safe_edit_message(query, text, reply_markup=kb)
        return

    is_adm, has_all_four, perms, status_note = await check_channel_permissions(client, channel_id)

    bot_badge = f"{TG_CHECK} Admin" if is_adm else f"{TG_CROSS} Not Admin"
    p_badge = f"{TG_CHECK} Post" if perms["post"] else f"{TG_CROSS} Post"
    e_badge = f"{TG_CHECK} Edit" if perms["edit"] else f"{TG_CROSS} Edit"
    d_badge = f"{TG_CHECK} Delete" if perms["delete"] else f"{TG_CROSS} Delete"
    i_badge = f"{TG_CHECK} Invite" if perms["invite"] else f"{TG_CROSS} Invite"
    overall_guard = f"{TG_CHECK} READY" if has_all_four else f"{TG_CROSS} INCOMPLETE"

    panel_text = f"""┌────── ˹ {TG_HAMMER} <b>ᴄʜᴀɴɴᴇʟ ᴄᴏɴᴛʀᴏʟ</b> ˼ ─── ⏤‌●
┆
┆ {TG_DOC} <b>ᴄʜᴀɴɴᴇʟ :</b> {html.escape(ch.get('channel_title', 'Channel'))}
┆ {TG_KEY} <b>ɪᴅ :</b> <code>{ch.get('channel_id')}</code>
┆
┆ {TG_CHECK} <b>ʙᴏᴛ sᴛᴀᴛᴜs :</b> {bot_badge}
┆ {TG_SHIELD} <b>ɢᴜᴀʀᴅ sᴛᴀᴛᴜs :</b> {overall_guard}
┆
┆ <b>4-Way Required Rights:</b>
┆ • {p_badge}
┆ • {e_badge}
┆ • {d_badge}
┆ • {i_badge}
┆
┆ {TG_DIAMOND} <b>ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ :</b> {'ENABLED' if ch.get('auto_delete_enabled') else 'DISABLED'}
┆
┆ <i>{status_note}</i>
┆
└──────────────────●"""

    await safe_edit_message(
        query,
        panel_text,
        reply_markup=get_channel_management_panel(
            channel_id=channel_id,
            auto_delete=bool(ch.get("auto_delete_enabled")),
            scope=scope,
            page=page,
        ),
    )


# ---------------------------------------------------------------------------
# BUILT-IN PYTHON ASYNCIO HEALTHCHECK HTTP SERVER (24/7 RENDER KEEP-ALIVE)
# ---------------------------------------------------------------------------


async def handle_http_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        await reader.read(1024)
        body = b"OK - Channel Guard Bot is running 24/7 with MongoDB"
        response = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n"
            b"Content-Length: " + str(len(body)).encode("ascii") + b"\r\n"
            b"Connection: close\r\n\r\n" + body
        )
        writer.write(response)
        await writer.drain()
    except Exception:
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def start_built_in_server() -> asyncio.AbstractServer:
    server = await asyncio.start_server(handle_http_connection, "0.0.0.0", PORT)
    logger.info(f"Built-in healthcheck webserver listening on port {PORT} for Render.")
    return server


# ---------------------------------------------------------------------------
# APPLICATION ENTRYPOINT & LIFECYCLE
# ---------------------------------------------------------------------------


async def main() -> None:
    global BOT_USERNAME
    logger.info("Starting Telegram Channel Guard Bot (MongoDB)...")
    await db.connect()

    server = await start_built_in_server()

    await app.start()
    me = await app.get_me()
    BOT_USERNAME = me.username
    logger.info(f"Bot connected: @{me.username} (ID: {me.id})")
    logger.info(f"Authorized Superadmins: {list(ADMIN_IDS)}")

    await idle()
    await app.stop()
    server.close()
    await server.wait_closed()
    await db.close()


if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot shutting down safely.")
    except Exception as exc:
        logger.critical(f"Fatal error: {exc}", exc_info=True)
