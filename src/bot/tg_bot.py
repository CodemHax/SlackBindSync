from telethon import TelegramClient, events
from src.utils.bridge import isdd, isslack, tgformat
from src.database import store_functions


class TelegramBot:
    def __init__(self, chat_id, api_id, api_hash, bot_token=None, phone=None):
        self.chat_id = int(chat_id)
        self.api_id = api_id
        self.api_hash = api_hash
        self.bot_token = bot_token
        self.phone = phone
        self.client = None
        self.forward_to_discord = None
        self.forward_to_slack = None
        self.map_tg_to_dc = {}
        self.map_dc_to_tg = {}
        self.map_tg_to_slack = {}
        self.map_slack_to_tg = {}

    def set_forward_callbacks(self, discord_callback=None, slack_callback=None):
        self.forward_to_discord = discord_callback
        self.forward_to_slack = slack_callback

    def set_message_maps(self, tg_to_dc, dc_to_tg, tg_to_slack, slack_to_tg):
        self.map_tg_to_dc = tg_to_dc
        self.map_dc_to_tg = dc_to_tg
        self.map_tg_to_slack = tg_to_slack
        self.map_slack_to_tg = slack_to_tg

    async def handle_message(self, event):
        if not event.message or not event.message.text:
            return

        # Check if message is from the correct chat
        if event.chat_id != self.chat_id:
            return

        if isdd(event.message.text) or isslack(event.message.text):
            return

        sender = await event.get_sender()
        username = sender.first_name if hasattr(sender, 'first_name') else 'Unknown'
        if hasattr(sender, 'last_name') and sender.last_name:
            username += f" {sender.last_name}"

        msg = tgformat(username, event.message.text)

        reply_to_discord_message_id = None
        reply_to_slack_ts = None
        reply_to_internal_id = None
        reply_to_tg_id = None

        if event.message.reply_to_msg_id:
            replied_tg_id = event.message.reply_to_msg_id
            reply_to_tg_id = replied_tg_id
            reply_to_discord_message_id = self.map_tg_to_dc.get(replied_tg_id)
            reply_to_slack_ts = self.map_tg_to_slack.get(replied_tg_id)
            try:
                m = await store_functions.find_by_tg_id(replied_tg_id)
                reply_to_internal_id = m["id"] if m else None
            except Exception:
                reply_to_internal_id = None

        tg_msg_id = event.message.id
        await store_functions.add_message(
            source='telegram',
            text=event.message.text,
            username=username,
            tg_msg_id=tg_msg_id,
            reply_to_tg_id=reply_to_tg_id,
            reply_to_dc_id=reply_to_discord_message_id,
            reply_to_slack_ts=reply_to_slack_ts,
            reply_to_id=reply_to_internal_id,
        )

        if self.forward_to_discord:
            dc_msg_id = await self.forward_to_discord(msg, reply_to_discord_message_id=reply_to_discord_message_id)
            if dc_msg_id:
                self.map_tg_to_dc[tg_msg_id] = dc_msg_id
                self.map_dc_to_tg[dc_msg_id] = tg_msg_id
                await store_functions.set_dc_id_for_tg(tg_msg_id, int(dc_msg_id))

        if self.forward_to_slack:
            slack_ts = await self.forward_to_slack(msg, reply_to_slack_ts=reply_to_slack_ts)
            if slack_ts:
                self.map_tg_to_slack[tg_msg_id] = slack_ts
                self.map_slack_to_tg[slack_ts] = tg_msg_id
                await store_functions.set_slack_ts_for_tg(tg_msg_id, slack_ts)

    async def start(self):
        """Start the Telegram client"""
        if self.bot_token:
            self.client = TelegramClient('bot_session', self.api_id, self.api_hash)
            await self.client.start(bot_token=self.bot_token)
        else:
            self.client = TelegramClient('user_session', self.api_id, self.api_hash)
            await self.client.start(phone=self.phone)

        # Register event handler for new messages
        @self.client.on(events.NewMessage(chats=self.chat_id))
        async def message_handler(event):
            await self.handle_message(event)

        return self.client

    def get_client(self):
        return self.client

