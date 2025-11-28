import base64
import binascii
import logging
import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException
import openai
from pydantic import BaseModel

logger = logging.getLogger("lootmore.callout")
logging.basicConfig(level=logging.INFO)

app = FastAPI()

DEFAULT_CALLOUT = "Callout unavailable right now. Backend wired up."


class CalloutRequest(BaseModel):
    image_b64: str
    game: str


class CalloutResponse(BaseModel):
    text: str
    audio_b64: str


def _extract_text(message: Any) -> str:
    """Best effort extraction of model text content."""
    content = None
    if isinstance(message, dict):
        content = message.get("content")
    else:
        content = getattr(message, "content", None)

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            text = None
            if isinstance(item, dict):
                text = item.get("text")
            else:
                text = getattr(item, "text", None)
            if text:
                parts.append(text)
        if parts:
            return "\n".join(parts)

    return DEFAULT_CALLOUT


def _validate_auth_token(auth_header: str | None) -> None:
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing or invalid token")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/callout", response_model=CalloutResponse)
async def callout(request: CalloutRequest, authorization: str | None = Header(default=None)):
    _validate_auth_token(authorization)

    try:
        image_bytes = base64.b64decode(request.image_b64)
    except (binascii.Error, ValueError) as exc:  # noqa: B905
        raise HTTPException(status_code=400, detail="Invalid image_b64") from exc

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not set")
        raise HTTPException(status_code=500, detail="Missing OpenAI API key")

    client = openai.OpenAI(api_key=api_key)

    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "system",
                    "content": "You are the Lootmore tactical AI. Respond with a single short tactical callout.",
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_image",
                            "image_url": f"data:image/png;base64,{encoded_image}",
                        },
                        {"type": "text", "text": "Give tactical callout."},
                    ],
                },
            ],
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Callout generation failed")
        raise HTTPException(status_code=500, detail="Callout generation failed") from exc

    callout_text = _extract_text(completion.choices[0].message)
    if not callout_text:
        callout_text = DEFAULT_CALLOUT

    logger.info("Callout generated: %s", callout_text)

    try:
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=callout_text,
        ) as response:
            audio_bytes = response.read()
    except Exception as exc:  # noqa: BLE001
        logger.exception("TTS generation failed")
        raise HTTPException(status_code=500, detail="Audio generation failed") from exc

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    return {"text": callout_text, "audio_b64": audio_b64}
