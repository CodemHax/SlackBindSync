import os
import aiohttp

original_ping = aiohttp.ClientWebSocketResponse.ping

async def patched_ping(self, message=b''):
    if isinstance(message, str):
        message = message.encode('utf-8')
    return await original_ping(self, message)

aiohttp.ClientWebSocketResponse.ping = patched_ping


def get_root():
    current_file = os.path.abspath(__file__)
    api_dir = os.path.dirname(current_file)
    src_dir = os.path.dirname(api_dir)
    return os.path.dirname(src_dir)



TG_TAG = "[TG]"
DC_TAG = "[DC]"
SLACK_TAG = "[SK]"
