from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.web.async_client import AsyncWebClient
from src.database import store_functions
from src.utils.bridge import isdd, istg


class SlackBot:
    def __init__(self, channel_id, bot_token, app_token):
        self.channel_id = channel_id
        self.bot_token = bot_token
        self.app_token = app_token
        self.client = None
        self.socket_client = None
        self.forward_to_discord = None
        self.forward_to_telegram = None
        self.map_slack_to_dc = {}
        self.map_slack_to_tg = {}
        self.map_dc_to_slack = {}
        self.map_tg_to_slack = {}
        self.bot_user_id = None

    def set_forward_callbacks(self, forward_to_discord=None, forward_to_telegram=None):
        self.forward_to_discord = forward_to_discord
        self.forward_to_telegram = forward_to_telegram

    def set_message_maps(self, slack_to_dc, slack_to_tg, dc_to_slack, tg_to_slack):
        self.map_slack_to_dc = slack_to_dc
        self.map_slack_to_tg = slack_to_tg
        self.map_dc_to_slack = dc_to_slack
        self.map_tg_to_slack = tg_to_slack

    async def process_message(self, event):
        if event.get("type") != "message":
            return

        if event.get("subtype") in ["bot_message", "message_changed"]:
            return

        if event.get("user") == self.bot_user_id:
            return

        if event.get("channel") != self.channel_id:
            return

        text = event.get("text", "")

        if isdd(text) or istg(text):
            return
        user_id = event.get("user")
        username = await self.get_username(user_id)
        slack_ts = event.get("ts")
        thread_ts = event.get("thread_ts")

        msg_dc = f"[SK] {username}: {text}"
        msg_tg = f"[SK] {username}: {text}"
        reply_to_dc_id = None
        reply_to_tg_id = None
        reply_to_internal_id = None
        reply_to_slack_ts = None
        if thread_ts and thread_ts != slack_ts:
            reply_to_slack_ts = thread_ts
            reply_to_dc_id = self.map_slack_to_dc.get(thread_ts)
            reply_to_tg_id = self.map_slack_to_tg.get(thread_ts)

            try:
                m = await store_functions.find_by_slack_ts(thread_ts)
                reply_to_internal_id = m["id"] if m else None
            except Exception:
                reply_to_internal_id = None

        # Store message in database
        await store_functions.add_message(
            source='slack',
            text=text,
            username=username,
            slack_ts=slack_ts,
            reply_to_slack_ts=reply_to_slack_ts,
            reply_to_tg_id=reply_to_tg_id,
            reply_to_id=reply_to_internal_id,
        )

        # Forward to Discord
        if self.forward_to_discord:
            dc_msg_id = await self.forward_to_discord(msg_dc, reply_to_discord_message_id=reply_to_dc_id)
            if dc_msg_id:
                self.map_slack_to_dc[slack_ts] = dc_msg_id
                self.map_dc_to_slack[dc_msg_id] = slack_ts
                await store_functions.set_dc_id_for_slack(slack_ts, int(dc_msg_id))

        if self.forward_to_telegram:
            tg_msg_id = await self.forward_to_telegram(msg_tg, reply_to_telegram_message_id=reply_to_tg_id)
            if tg_msg_id:
                self.map_slack_to_tg[slack_ts] = tg_msg_id
                self.map_tg_to_slack[tg_msg_id] = slack_ts
                await store_functions.set_tg_id_for_slack(slack_ts, int(tg_msg_id))

    async def get_username(self, user_id):
        try:
            response = await self.client.users_info(user=user_id)
            if response["ok"]:
                user = response["user"]
                return user.get("real_name") or user.get("name", "Unknown")
        except Exception as e:
            print(f"Error fetching user info: {e}")
        return "Unknown"

    async def handle_socket_mode_request(self, client: SocketModeClient, req: SocketModeRequest):
        if req.type == "events_api":
            # Acknowledge the request
            response = SocketModeResponse(envelope_id=req.envelope_id)
            await client.send_socket_mode_response(response)

            # Process the event
            event = req.payload.get("event", {})
            await self.process_message(event)

    async def send_message(self, text, reply_to_slack_ts=None):
        try:
            kwargs = {
                "channel": self.channel_id,
                "text": text,
            }

            if reply_to_slack_ts:
                kwargs["thread_ts"] = reply_to_slack_ts

            response = await self.client.chat_postMessage(**kwargs)

            if response["ok"]:
                return response["ts"]
        except Exception as e:
            print(f"Error sending Slack message: {e}")
        return None

    async def create_client(self):
        self.client = AsyncWebClient(token=self.bot_token)

        try:
            auth_response = await self.client.auth_test()
            if auth_response["ok"]:
                self.bot_user_id = auth_response["user_id"]
                print(f"Slack bot user ID: {self.bot_user_id}")
        except Exception as e:
            print(f"Error getting bot user ID: {e}")

        self.socket_client = SocketModeClient(
            app_token=self.app_token,
            auto_reconnect_enabled=True,
            trace_enabled=False,
            ping_interval=30,
            web_client=self.client,
        )

        self.socket_client.socket_mode_request_listeners.append(
            self.handle_socket_mode_request
        )
        return self.socket_client

    def get_client(self):
        return self.socket_client if self.socket_client else None

