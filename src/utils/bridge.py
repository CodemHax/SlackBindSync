from src.utils.misc import TG_TAG, DC_TAG, SLACK_TAG


def istg(text):
    return text.startswith(TG_TAG)


def isdd(text):
    return text.startswith(DC_TAG)


def isslack(text):
    return text.startswith(SLACK_TAG)

def issk(text):
    return text.startswith(SLACK_TAG)


def tgformat(username, text):
    return f"{TG_TAG} {username}: {text}"


def ddformat(display_name, text):
    return f"{DC_TAG} {display_name}: {text}"


def slackformat(username, text):
    return f"{SLACK_TAG} {username}: {text}"

def skformat(username, text):
    return f"{SLACK_TAG} {username}: {text}"


async def fwd_to_dd(dbot, channel_id, message):
    channel = dbot.get_channel(channel_id)
    if not channel:
        print(f"Discord channel not found: {channel_id}")
        return
    await channel.send(message)


async def fwd_tg(tg_client, chat_id, message):
    """Send message to Telegram using Telethon client"""
    await tg_client.send_message(chat_id, message)


async def fwd_dd_with_reply(dbot, channel_id, message, message_id=None):
    channel = dbot.get_channel(channel_id)
    if not channel:
        print(f"Discord channel not found: {channel_id}")
        return None

    if message_id:
        try:
            ref_msg = await channel.fetch_message(message_id)
            sent = await ref_msg.reply(message)
        except:
            sent = await channel.send(message)
    else:
        sent = await channel.send(message)
    return getattr(sent, "id", None)


async def fwd_to_tg_rply(tg_client, chat_id, message, msg_id=None):
    """Send message to Telegram with optional reply using Telethon client"""
    sent = await tg_client.send_message(
        chat_id,
        message,
        reply_to=msg_id,
    )
    return sent.id if sent else None


async def fwd_to_slack(slack_bot, message, slack_ts=None):
    return await slack_bot.send_message(message, reply_to_slack_ts=slack_ts)

