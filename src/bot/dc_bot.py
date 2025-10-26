import discord
from src.utils.bridge import istg, isslack, ddformat
from src.database import store_functions

class DiscordBot:
    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.client = None
        self.forward_to_telegram = None
        self.forward_to_slack = None
        self.map_tg_to_dc = {}
        self.map_dc_to_tg = {}
        self.map_slack_to_dc = {}
        self.map_dc_to_slack = {}
        self.intents = discord.Intents.default()
        self.intents.message_content = True

    def set_forward_callbacks(self, telegram_callback=None, slack_callback=None):
        self.forward_to_telegram = telegram_callback
        self.forward_to_slack = slack_callback

    def set_message_maps(self, tg_to_dc, dc_to_tg, slack_to_dc, dc_to_slack):
        self.map_tg_to_dc = tg_to_dc
        self.map_dc_to_tg = dc_to_tg
        self.map_slack_to_dc = slack_to_dc
        self.map_dc_to_slack = dc_to_slack

    async def on_ready(self):
       if self.client.get_channel(self.channel_id):
           print("Connected to Discord channel")
       else :
           print("Discord: channel not found")

    async def on_message(self, message):
        if message.author == self.client.user:
            return
        if message.channel.id != self.channel_id:
            return
        if istg(message.content or "") or isslack(message.content or ""):
            return

        msg = ddformat(message.author.display_name, message.content or "")

        rly_tg_message_id = None
        rly_slack_ts = None
        reply_to_internal_id = None
        reply_to_dc_id = None
        ref = getattr(message, 'reference', None)
        if ref and getattr(ref, 'message_id', None):
            reply_to_dc_id = ref.message_id
            rly_tg_message_id = self.map_dc_to_tg.get(ref.message_id)
            rly_slack_ts = self.map_dc_to_slack.get(ref.message_id)
            try:
                m = await store_functions.find_by_dc_id(ref.message_id)
                reply_to_internal_id = m["id"] if m else None
            except Exception:
                reply_to_internal_id = None

        dc_msg_id = message.id
        await store_functions.add_message(
            source='discord',
            text=message.content or "",
            username=message.author.display_name,
            dc_msg_id=dc_msg_id,
            reply_to_dc_id=reply_to_dc_id,
            reply_to_tg_id=rly_tg_message_id,
            reply_to_slack_ts=rly_slack_ts,
            reply_to_id=reply_to_internal_id,
        )


        if self.forward_to_telegram:
            tg_msg_id = await self.forward_to_telegram(msg, reply_to_telegram_message_id=rly_tg_message_id)
            if tg_msg_id:
                self.map_dc_to_tg[dc_msg_id] = tg_msg_id
                self.map_tg_to_dc[tg_msg_id] = dc_msg_id
                await store_functions.set_tg_id_for_dc(dc_msg_id, int(tg_msg_id))


        if self.forward_to_slack:
            slack_ts = await self.forward_to_slack(msg, reply_to_slack_ts=rly_slack_ts)
            if slack_ts:
                self.map_dc_to_slack[dc_msg_id] = slack_ts
                self.map_slack_to_dc[slack_ts] = dc_msg_id
                await store_functions.set_slack_ts_for_dc(dc_msg_id, slack_ts)

    def create_client(self):
        self.client = discord.Client(intents=self.intents)

        self.client.event(self.on_ready)
        self.client.event(self.on_message)

        return self.client

    def get_client(self):
        return self.client if self.client else self.create_client()

