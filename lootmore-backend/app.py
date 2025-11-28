import base64
import binascii
import logging
import os
import time
from datetime import datetime
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import openai
from pydantic import BaseModel
from sqlalchemy.orm import Session

from admin import router as admin_router
from database import get_db
from models import ApiUsageLog
from security import verify_token

logger = logging.getLogger("lootmore.callout")
logging.basicConfig(level=logging.INFO)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(admin_router, prefix="/admin")

DEFAULT_CALLOUT = "Callout unavailable right now. Backend wired up."


class CalloutRequest(BaseModel):
    image_b64: str
    game: str


class CalloutResponse(BaseModel):
    text: str
    audio_b64: str


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"error": "Invalid JSON"})


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


def _parse_raw_token(auth_header: str | None) -> str:
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    return token


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/callout", response_model=CalloutResponse)
async def callout(
    callout_request: CalloutRequest,
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    raw_token = _parse_raw_token(authorization)
    token = verify_token(raw_token, db)
    if not token:
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    success = False
    callout_text = None
    start_time = time.perf_counter()
    response_payload: dict[str, Any] | JSONResponse | None = None

    try:
        try:
            image_bytes = base64.b64decode(callout_request.image_b64)
        except (binascii.Error, ValueError) as exc:  # noqa: B905
            raise HTTPException(status_code=400, detail="Invalid image_b64") from exc

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not set")
            raise HTTPException(status_code=500, detail="Missing OpenAI API key")

        client = openai.OpenAI(api_key=api_key)
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")

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

        callout_text = _extract_text(completion.choices[0].message)
        if not callout_text:
            callout_text = DEFAULT_CALLOUT

        logger.info("Callout generated: %s", callout_text)

        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=callout_text,
        ) as speech_response:
            audio_bytes = speech_response.read()

        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        response_payload = {"text": callout_text, "audio_b64": audio_b64}
        success = True
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
        logger.exception("Callout generation failed")
        response_payload = JSONResponse(status_code=500, content={"error": "AI processing failed"})
    finally:
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        try:
            log = ApiUsageLog(
                token_id=token.id,
                timestamp=datetime.utcnow(),
                request_ip=request.client.host if request.client else None,
                latency_ms=latency_ms,
                text_length=len(callout_text or ""),
                success=success,
            )
            db.add(log)
            db.commit()
        except Exception:  # noqa: BLE001
            logger.exception("Failed to log API usage")
            db.rollback()

    return response_payload
