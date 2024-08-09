import os
import sys

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhook import WebhookParser
from linebot.v3.webhooks import PostbackEvent

app = FastAPI()

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
if channel_secret is None:
    print("Specify LINE_CHANNEL_SECRET as environment variable.")
    sys.exit(1)
if channel_access_token is None:
    print("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")
    sys.exit(1)

configuration = Configuration(access_token=channel_access_token)

async_api_client = AsyncApiClient(configuration)
line_bot_api = AsyncMessagingApi(async_api_client)
parser = WebhookParser(channel_secret)


@app.get("/api/python")
def hello_world():
    return {"message": "Hello World"}


async def get_body_bytes(request: Request) -> bytes:
    data: bytes = await request.body()
    return data


async def get_line_signature(request: Request) -> str:
    signature: str = request.headers.get("X-Line-Signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Invalid signature.")
    return signature


@app.post("/api/line/webhook")
async def webhook(
    line_signature: str = Depends(get_line_signature),
    request_bytes: bytes = Depends(get_body_bytes),
) -> JSONResponse:
    # get request body as text
    body = request_bytes.decode()

    try:
        events = parser.parse(body, line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    print("events", events)

    for event in events:
        if not isinstance(event, PostbackEvent):
            continue

        if event.source.type != "user":
            continue

        user_id: str = event.source.user_id
        print("user_id", user_id)
        # TODO: query mbs login to get mbs user
        # TODO: get_wallet
        # TODO: get_near_expire_balance

        await line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=user_id)],
            )
        )

    return JSONResponse(status_code=200, content={"message": "OK"})
