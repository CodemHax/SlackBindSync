import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass


def load_config():
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    tg_chat = int(os.getenv("TELEGRAM_CHAT_ID", "0"))
    dc_token = os.getenv("DISCORD_BOT_TOKEN", "")
    dc_channel = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
    mongo_uri = os.getenv("MONGO_URI", "")
    mongo_db = os.getenv("MONGO_DB", "")
    api_host = os.getenv("API_HOST", "localhost")
    api_port = int(os.getenv("API_PORT", "000"))

    missing = []
    if not tg_token:
        missing.append("TELEGRAM_TOKEN|TELEGRAM_BOT_TOKEN")
    if tg_chat == 0:
        missing.append("TELEGRAM_CHAT_ID")
    if not dc_token:
        missing.append("DISCORD_TOKEN|DISCORD_BOT_TOKEN")
    if dc_channel == 0:
        missing.append("DISCORD_CHANNEL_ID")
    if not mongo_uri:
        missing.append("MONGO_URI")
    if not mongo_db:
        missing.append("MONGO_DB")
    if missing:
        raise ValueError("Missing environment variables: " + ", ".join(missing))

    return {
        "telegram_token": tg_token,
        "telegram_chat_id": tg_chat,
        "discord_token": dc_token,
        "discord_channel_id": dc_channel,
        "mongo_uri": mongo_uri,
        "mongo_db": mongo_db,
        "api_host": api_host,
        "api_port": api_port,
    }
