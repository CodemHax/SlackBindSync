from telegram.ext import Application, MessageHandler, filters
from src.utils.bridge import isdd, tgformat
from src.database import store_functions


class TelegramBot:
    def __init__(self, chat_id, token):
        self.chat_id = chat_id
        self.token = token
        self.app = None
        self.forward_to_discord = None
        self.map_tg_to_dc = {}
        self.map_dc_to_tg = {}

    def set_forward_callback(self, callback):
        self.forward_to_discord = callback

    def set_message_maps(self, tg_to_dc, dc_to_tg):
        self.map_tg_to_dc = tg_to_dc
        self.map_dc_to_tg = dc_to_tg

    async def handle_message(self, update, context):
        if not update.message or not update.message.text or update.message.chat_id != self.chat_id:
            return
        if isdd(update.message.text):
            return

        username = update.message.from_user.full_name
        msg = tgformat(username, update.message.text)

        if not self.forward_to_discord:
            return

        reply_to_discord_message_id = None
        reply_to_internal_id = None
        reply_to_tg_id = None

        if update.message.reply_to_message:
            replied_tg_id = update.message.reply_to_message.message_id
            reply_to_tg_id = replied_tg_id
            reply_to_discord_message_id = self.map_tg_to_dc.get(replied_tg_id)
            try:
                m = await store_functions.find_by_tg_id(replied_tg_id)
                reply_to_internal_id = m["id"] if m else None
            except Exception:
                reply_to_internal_id = None

        tg_msg_id = update.message.message_id
        await store_functions.add_message(
            source='telegram',
            text=update.message.text,
            username=username,
            tg_msg_id=tg_msg_id,
            reply_to_tg_id=reply_to_tg_id,
            reply_to_dc_id=reply_to_discord_message_id,
            reply_to_id=reply_to_internal_id,
        )

        dc_msg_id = await self.forward_to_discord(msg, reply_to_discord_message_id=reply_to_discord_message_id)
        if dc_msg_id:
            self.map_tg_to_dc[tg_msg_id] = dc_msg_id
            self.map_dc_to_tg[dc_msg_id] = tg_msg_id
            await store_functions.set_dc_id_for_tg(tg_msg_id, int(dc_msg_id))

    def create_application(self):
        self.app = Application.builder().token(self.token).build()
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        return self.app

    def get_application(self):
        return self.app if self.app else self.create_application()


