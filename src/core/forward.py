import logging
import asyncio
import uvicorn
from src.bot.tg_bot import TelegramBot
from src.bot.dc_bot import DiscordBot
from src.config import load_config
from src.database import database, store_functions
from src.api.server import app, set_runtime
from src.utils.bridge import (
    fwd_dd_with_reply as util_forward_dc_reply,
    fwd_to_tg_rply as util_forward_tg_reply,
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

    tg_bot = TelegramBot(chat_id=cfg["telegram_chat_id"], token=cfg["telegram_token"])
    dc_bot = DiscordBot(channel_id=cfg["discord_channel_id"])

    tbot = tg_bot.create_application()
    dbot = dc_bot.create_client()

    async def fwd_to_dd(message, reply_to_discord_message_id=None):
        return await util_forward_dc_reply(
            dbot,
            cfg["discord_channel_id"],
            message,
            message_id=reply_to_discord_message_id,
        )

    async def forward_to_telegram(message, reply_to_telegram_message_id=None):
        return await util_forward_tg_reply(
            tbot,
            cfg["telegram_chat_id"],
            message,
            msg_id=reply_to_telegram_message_id,
        )

    tg_bot.set_forward_callback(fwd_to_dd)
    tg_bot.set_message_maps(map_tg_to_dc, map_dc_to_tg)

    dc_bot.set_forward_callback(forward_to_telegram)
    dc_bot.set_message_maps(map_tg_to_dc, map_dc_to_tg)

    set_runtime(tbot, dbot, cfg, map_tg_to_dc, map_dc_to_tg)

    config = uvicorn.Config(app, host=cfg["api_host"], port=cfg["api_port"], log_level="info")
    server = uvicorn.Server(config)
    api_task = asyncio.create_task(server.serve())

    async with tbot, dbot:
        logger.info("Starting Telegram bot polling...")
        await tbot.initialize()
        await tbot.start()
        logger.info("Starting Discord bot...")
        discord_task = asyncio.create_task(dbot.start(cfg["discord_token"]))
        polling_task = asyncio.create_task(tbot.updater.start_polling())
        await asyncio.gather(api_task, discord_task, polling_task)
