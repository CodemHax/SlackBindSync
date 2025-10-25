TG_TAG = "[TG]"
DC_TAG = "[DC]"


def istg(text):
    return text.startswith(TG_TAG)


def isdd(text):
    return text.startswith(DC_TAG)


def tgformat(username, text):
    return f"{TG_TAG} {username}: {text}"


def ddformat(display_name, text):
    return f"{DC_TAG} {display_name}: {text}"


async def fwd_to_dd(dbot, channel_id, message):
    channel = dbot.get_channel(channel_id)
    if not channel:
        print(f"Discord channel not found: {channel_id}")
        return
    await channel.send(message)


async def fwd_tg(tbot, chat_id, message):
    await tbot.bot.send_message(chat_id=chat_id, text=message)


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


async def fwd_to_tg_rply(tbot, chat_id, message, msg_id=None):
    sent = await tbot.bot.send_message(
        chat_id=chat_id,
        text=message,
        reply_to_message_id=msg_id,
    )
    return getattr(sent, "message_id", None)
