import base64
import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException, UploadFile
import openai
from pydantic import BaseModel

logger = logging.getLogger("lootmore.callout")
logging.basicConfig(level=logging.INFO)

app = FastAPI()

DEFAULT_CALLOUT = "Callout unavailable right now. Backend wired up."


class CalloutResult(BaseModel):
    callout: str
    error: str | None = None


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


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/callout", response_model=CalloutResult)
async def callout(image: UploadFile):
    # Read image from the POST request
    img_bytes = await image.read()
    logger.info("Callout request received: bytes=%s filename=%s", len(img_bytes), image.filename)

    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set; returning placeholder callout")
        return CalloutResult(callout=DEFAULT_CALLOUT, error="missing_api_key")

    client = openai.OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are the Lootmore tactical AI."},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_image",
                            "image_url": f"data:image/png;base64,{img_b64}",
                        },
                        {"type": "text", "text": "Give tactical callout."},
                    ],
                },
            ],
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Callout generation failed")
        raise HTTPException(status_code=502, detail="Callout generation failed") from exc

    callout_text = _extract_text(response.choices[0].message)
    logger.info("Callout generated: %s", callout_text)

    return CalloutResult(callout=callout_text)
