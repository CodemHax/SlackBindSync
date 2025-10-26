from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Optional, Dict, Any
import os
from src.core.models import MessageCreate, MessageReply
from src.database import store_functions
from src.utils.bridge import fwd_to_tg_rply, fwd_dd_with_reply, fwd_to_slack
from src.auth import auth_manager
from src.api.admin_routes import router as admin_router
from src.utils.misc import get_root

app = FastAPI(
    title="BindSync",
    version="4.0.0"
)

app.include_router(admin_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tg_client = None
dbot = None
slack_bot = None
cfg = None
map_tg_to_dc = None
map_dc_to_tg = None
map_slack_to_dc = None
map_slack_to_tg = None
map_dc_to_slack = None
map_tg_to_slack = None


def set_runtime(tb, db, sb, config, tg_dc_map, dc_tg_map, slack_dc_map, slack_tg_map, dc_slack_map, tg_slack_map):
    global tg_client, dbot, slack_bot, cfg, map_tg_to_dc, map_dc_to_tg, map_slack_to_dc, map_slack_to_tg, map_dc_to_slack, map_tg_to_slack
    tg_client = tb
    dbot = db
    slack_bot = sb
    cfg = config
    map_tg_to_dc = tg_dc_map
    map_dc_to_tg = dc_tg_map
    map_slack_to_dc = slack_dc_map
    map_slack_to_tg = slack_tg_map
    map_dc_to_slack = dc_slack_map
    map_tg_to_slack = tg_slack_map


async def verify_api_token(x_api_token: Optional[str] = Header(None)):
    if not x_api_token:
        raise HTTPException(status_code=401, detail="API token required in X-API-Token header")

    if not await auth_manager.verify_token(x_api_token):
        raise HTTPException(status_code=401, detail="Invalid or expired API token")

    return x_api_token



@app.get("/messages", dependencies=[Depends(verify_api_token)])
async def get_messages(limit: int = 100, offset: int = 0):
    limit = max(1, min(200, limit))
    offset = max(0, offset)
    messages = await store_functions.list_messages(limit=limit, offset=offset)
    print(messages)
    return {"messages": messages}


@app.get("/messages/{message_id}", dependencies=[Depends(verify_api_token)])
async def get_message(message_id: str):
    message = await store_functions.get_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@app.post("/messages", dependencies=[Depends(verify_api_token)])
async def create_message(msg: MessageCreate):
    msg_id = await store_functions.add_message(
        source='api',
        text=msg.text,
        username=msg.username,
        reply_to_id=msg.reply_to_id
    )

    reply_to_tg_id = None
    reply_to_dc_id = None
    reply_to_slack_ts = None

    if msg.reply_to_id:
        orig_msg = await store_functions.get_message(msg.reply_to_id)
        if orig_msg:
            reply_to_tg_id = orig_msg.get("tg_msg_id")
            reply_to_dc_id = orig_msg.get("dc_msg_id")
            reply_to_slack_ts = orig_msg.get("slack_ts")

    formatted_msg = f"[API] {msg.username}: {msg.text}"

    tg_msg_id = None
    dc_msg_id = None
    slack_ts = None

    if (msg.target is None or msg.target == 'telegram') and tg_client and cfg and "telegram_chat_id" in cfg:
        tg_msg_id = await fwd_to_tg_rply(
            tg_client, cfg["telegram_chat_id"], formatted_msg,
            msg_id=reply_to_tg_id
        )
        if tg_msg_id:
            await store_functions.set_tg_msg_id(msg_id, int(tg_msg_id))

    
    if (msg.target is None or msg.target == 'discord') and dbot and cfg and "discord_channel_id" in cfg:
        dc_msg_id = await fwd_dd_with_reply(
            dbot, cfg["discord_channel_id"], formatted_msg,
            message_id=reply_to_dc_id
        )
        if dc_msg_id:
            await store_functions.set_dc_msg_id(msg_id, int(dc_msg_id))


    if (msg.target is None or msg.target == 'slack') and slack_bot and cfg and "slack_channel_id" in cfg:
        slack_ts = await fwd_to_slack(
            slack_bot, formatted_msg,
            slack_ts=reply_to_slack_ts
        )
        if slack_ts:
            await store_functions.set_slack_ts_for_dc(msg_id, slack_ts)


    if tg_msg_id and dc_msg_id and map_tg_to_dc is not None and map_dc_to_tg is not None:
        map_tg_to_dc[int(tg_msg_id)] = int(dc_msg_id)
        map_dc_to_tg[int(dc_msg_id)] = int(tg_msg_id)

    if tg_msg_id and slack_ts and map_tg_to_slack is not None and map_slack_to_tg is not None:
        map_tg_to_slack[int(tg_msg_id)] = slack_ts
        map_slack_to_tg[slack_ts] = int(tg_msg_id)

    if dc_msg_id and slack_ts and map_dc_to_slack is not None and map_slack_to_dc is not None:
        map_dc_to_slack[int(dc_msg_id)] = slack_ts
        map_slack_to_dc[slack_ts] = int(dc_msg_id)

    return {"id": msg_id, "tg_msg_id": tg_msg_id, "dc_msg_id": dc_msg_id, "slack_ts": slack_ts}


@app.post("/messages/{message_id}/reply", dependencies=[Depends(verify_api_token)])
async def reply_to_message(message_id: str, reply: MessageReply):
    orig_msg = await store_functions.get_message(message_id)
    if not orig_msg:
        raise HTTPException(status_code=404, detail="Original message not found")

    reply_id = await store_functions.add_message(
        source='api_reply',
        text=reply.text,
        username=reply.username,
        reply_to_id=message_id
    )

    formatted_reply = f"[API] {reply.username}: {reply.text}"

    tg_msg_id = None
    dc_msg_id = None
    slack_ts = None


    if (reply.target is None or reply.target == 'telegram') and tg_client and cfg and "telegram_chat_id" in cfg and orig_msg.get("tg_msg_id"):
        tg_msg_id = await fwd_to_tg_rply(
            tg_client, cfg["telegram_chat_id"], formatted_reply,
            msg_id=orig_msg.get("tg_msg_id")
        )
        if tg_msg_id:
            await store_functions.set_tg_msg_id(reply_id, int(tg_msg_id))


    if (reply.target is None or reply.target == 'discord') and dbot and cfg and "discord_channel_id" in cfg and orig_msg.get("dc_msg_id"):
        dc_msg_id = await fwd_dd_with_reply(
            dbot, cfg["discord_channel_id"], formatted_reply,
            message_id=orig_msg.get("dc_msg_id")
        )
        if dc_msg_id:
            await store_functions.set_dc_msg_id(reply_id, int(dc_msg_id))


    if (reply.target is None or reply.target == 'slack') and slack_bot and cfg and "slack_channel_id" in cfg and orig_msg.get("slack_ts"):
        slack_ts = await fwd_to_slack(
            slack_bot, formatted_reply,
            slack_ts=orig_msg.get("slack_ts")
        )
        if slack_ts:
            await store_functions.set_slack_ts_for_dc(reply_id, slack_ts)


    if tg_msg_id and dc_msg_id and map_tg_to_dc is not None and map_dc_to_tg is not None:
        map_tg_to_dc[int(tg_msg_id)] = int(dc_msg_id)
        map_dc_to_tg[int(dc_msg_id)] = int(tg_msg_id)

    if tg_msg_id and slack_ts and map_tg_to_slack is not None and map_slack_to_tg is not None:
        map_tg_to_slack[int(tg_msg_id)] = slack_ts
        map_slack_to_tg[slack_ts] = int(tg_msg_id)

    if dc_msg_id and slack_ts and map_dc_to_slack is not None and map_slack_to_dc is not None:
        map_dc_to_slack[int(dc_msg_id)] = slack_ts
        map_slack_to_dc[slack_ts] = int(dc_msg_id)

    return {"id": reply_id, "tg_msg_id": tg_msg_id, "dc_msg_id": dc_msg_id, "slack_ts": slack_ts}


@app.get("/admin")
async def admin_panel():
    admin_panel_path = os.path.join(get_root(), "admin", "login.html")
    if os.path.exists(admin_panel_path):
        return FileResponse(admin_panel_path)
    else:
        raise HTTPException(status_code=404, detail="Admin panel not found")


@app.get("/admin/dashboard")
async def dashboard():
    dashboard_path = os.path.join(get_root(), "admin", "dashboard.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    else:
        raise HTTPException(status_code=404, detail="Dashboard not found")


@app.get("/admin/login")
async def serve_login():
    login_path = os.path.join(get_root(), "admin", "login.html")
    if os.path.exists(login_path):
        return FileResponse(login_path)
    else:
        raise HTTPException(status_code=404, detail="Login page not found")


@app.get("/")
async def mainRoot():
    landing_path = os.path.join(get_root(), "admin", "index.html")
    if os.path.exists(landing_path):
        return FileResponse(landing_path)
    else:
        raise HTTPException(status_code=404, detail="Landing page not found")
