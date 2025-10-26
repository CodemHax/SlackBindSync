import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass


def load_config():
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    tg_api_id = os.getenv("TELEGRAM_API_ID", "")
    tg_api_hash = os.getenv("TELEGRAM_API_HASH", "")
    tg_phone = os.getenv("TELEGRAM_PHONE", "")  # Optional, for user account
    tg_chat = int(os.getenv("TELEGRAM_CHAT_ID", "0"))
    dc_token = os.getenv("DISCORD_BOT_TOKEN", "")
    dc_channel = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
    slack_bot_token = os.getenv("SLACK_BOT_TOKEN", "")
    slack_app_token = os.getenv("SLACK_APP_TOKEN", "")
    slack_channel = os.getenv("SLACK_CHANNEL_ID", "")
    mongo_uri = os.getenv("MONGO_URI", "")
    mongo_db = os.getenv("MONGO_DB", "")
    api_host = os.getenv("API_HOST", "localhost")
    api_port = int(os.getenv("API_PORT", "000"))


    missing = []
    if not tg_api_id:
        missing.append("TELEGRAM_API_ID")
    if not tg_api_hash:
        missing.append("TELEGRAM_API_HASH")
    if not tg_token and not tg_phone:
        missing.append("TELEGRAM_BOT_TOKEN or TELEGRAM_PHONE")
    if tg_chat == 0:
        missing.append("TELEGRAM_CHAT_ID")
    if not dc_token:
        missing.append("DISCORD_TOKEN|DISCORD_BOT_TOKEN")
    if dc_channel == 0:
        missing.append("DISCORD_CHANNEL_ID")
    if not slack_bot_token:
        missing.append("SLACK_BOT_TOKEN")
    if not slack_app_token:
        missing.append("SLACK_APP_TOKEN")
    if not slack_channel:
        missing.append("SLACK_CHANNEL_ID")
    if not mongo_uri:
        missing.append("MONGO_URI")
    if not mongo_db:
        missing.append("MONGO_DB")
    if missing:
        raise ValueError("Missing environment variables: " + ", ".join(missing))

    return {
        "telegram_token": tg_token,
        "telegram_api_id": tg_api_id,
        "telegram_api_hash": tg_api_hash,
        "telegram_phone": tg_phone,
        "telegram_chat_id": tg_chat,
        "discord_token": dc_token,
        "discord_channel_id": dc_channel,
        "slack_bot_token": slack_bot_token,
        "slack_app_token": slack_app_token,
        "slack_channel_id": slack_channel,
        "mongo_uri": mongo_uri,
        "mongo_db": mongo_db,
        "api_host": api_host,
        "api_port": api_port,
    }
