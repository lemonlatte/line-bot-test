import json
import os
import sys

from fastapi import Depends, FastAPI, HTTPException, Request, Response
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
from linebot.v3.webhooks import Event, PostbackEvent

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


async def get_line_events(
    line_signature: str = Depends(get_line_signature),
    request_bytes: bytes = Depends(get_body_bytes),
) -> list[Event]:
    print("line_signature", line_signature)
    print("body", request_bytes.decode())
    print(
        f"""curl -X POST -H 'Content-Type: application/json' -H 'X-Line-Signature: {line_signature}' -d '{request_bytes.decode()}' """
        f"""http://localhost:8000/webhook/line"""
    )
    try:
        return parser.parse(request_bytes.decode(), line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")


@app.post("/api/webhook/zendesk")
async def zendesk_webhook(
    request_bytes: bytes = Depends(get_body_bytes),
) -> Response:
    print("zendesk webhook body", request_bytes.decode())

    return Response(status_code=204)


@app.post("/api/webhook/line")
async def line_webhook(
    events: list[Event] = Depends(get_line_events),
) -> JSONResponse:
    for event in events:
        print("event", event.json())

        if not isinstance(event, PostbackEvent):
            continue

        if event.source.type != "user":
            continue

        user_id: str = event.source.user_id
        print("user_id", user_id)
        print("event.reply_token,", event.reply_token)

        # TODO: query mbs login to get mbs user
        # TODO: get_wallet
        # TODO: get_near_expire_balance

    return Response(status_code=204)
