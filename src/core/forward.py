import logging
import asyncio
import uvicorn
from src.bot.tg_bot import TelegramBot
from src.bot.dc_bot import DiscordBot
from src.bot.sk_bot import SlackBot
from src.config import load_config
from src.database import database, store_functions
from src.api.server import app, set_runtime
from src.utils.bridge import (
    fwd_dd_with_reply as util_forward_dc_reply,
    fwd_to_tg_rply as util_forward_tg_reply,
    fwd_to_slack as util_forward_slack,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bridge.log'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

async def main():
    cfg = load_config()

    await database.init_db(cfg["mongo_uri"], cfg["mongo_db"])
    await store_functions.configure()
    logger.info("Connected to MongoDB")

    map_tg_to_dc = {}
    map_dc_to_tg = {}
    map_slack_to_dc = {}
    map_slack_to_tg = {}
    map_dc_to_slack = {}
    map_tg_to_slack = {}

    tg_bot = TelegramBot(
        chat_id=cfg["telegram_chat_id"],
        api_id=cfg["telegram_api_id"],
        api_hash=cfg["telegram_api_hash"],
        bot_token=cfg["telegram_token"],
        phone=cfg["telegram_phone"]
    )
    dc_bot = DiscordBot(channel_id=cfg["discord_channel_id"])
    slack_bot = SlackBot(
        channel_id=cfg["slack_channel_id"],
        bot_token=cfg["slack_bot_token"],
        app_token=cfg["slack_app_token"]
    )

    tg_client = await tg_bot.start()
    dbot = dc_bot.create_client()
    slack_client = await slack_bot.create_client()

    async def fwd_to_dd(message, reply_to_discord_message_id=None):
        return await util_forward_dc_reply(
            dbot,
            cfg["discord_channel_id"],
            message,
            message_id=reply_to_discord_message_id,
        )

    async def forward_to_telegram(message, reply_to_telegram_message_id=None):
        return await util_forward_tg_reply(
            tg_client,
            cfg["telegram_chat_id"],
            message,
            msg_id=reply_to_telegram_message_id,
        )

    async def forward_to_slack(message, reply_to_slack_ts=None):
        return await util_forward_slack(
            slack_bot,
            message,
            slack_ts=reply_to_slack_ts,
        )

    tg_bot.set_forward_callbacks(
        discord_callback=fwd_to_dd,
        slack_callback=forward_to_slack
    )
    tg_bot.set_message_maps(map_tg_to_dc, map_dc_to_tg, map_tg_to_slack, map_slack_to_tg)

    dc_bot.set_forward_callbacks(
        telegram_callback=forward_to_telegram,
        slack_callback=forward_to_slack
    )
    dc_bot.set_message_maps(map_tg_to_dc, map_dc_to_tg, map_slack_to_dc, map_dc_to_slack)

    slack_bot.set_forward_callbacks(
        forward_to_discord=fwd_to_dd,
        forward_to_telegram=forward_to_telegram
    )
    slack_bot.set_message_maps(map_slack_to_dc, map_slack_to_tg, map_dc_to_slack, map_tg_to_slack)

    set_runtime(tg_client, dbot, slack_bot, cfg, map_tg_to_dc, map_dc_to_tg, map_slack_to_dc, map_slack_to_tg, map_dc_to_slack, map_tg_to_slack)

    config = uvicorn.Config(app, host=cfg["api_host"], port=cfg["api_port"], log_level="info")
    server = uvicorn.Server(config)
    api_task = asyncio.create_task(server.serve())

    logger.info("Telegram client started and listening...")

    logger.info("Starting Discord bot...")
    discord_task = asyncio.create_task(dbot.start(cfg["discord_token"]))

    logger.info("Starting Slack bot...")
    try:
        slack_task = asyncio.create_task(slack_client.connect())
    except Exception as e:
        logger.error(f"Failed to start Slack bot: {e}")
        slack_task = None

    logger.info("Running Telegram client...")
    tg_task = asyncio.create_task(tg_client.run_until_disconnected())

    tasks = [api_task, discord_task, tg_task]
    if slack_task:
        tasks.append(slack_task)

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await tg_client.disconnect()
