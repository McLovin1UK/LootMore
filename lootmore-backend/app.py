from fastapi import FastAPI, UploadFile, Form
import openai
import base64

app = FastAPI()

@app.post("/callout")
async def callout(image: UploadFile):
    # Read image from the POST request
    img_bytes = await image.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    # Call OpenAI (this key will ONLY live on the VPS)
    client = openai.OpenAI(api_key="YOUR_SECRET_KEY_HERE")

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "You are the Lootmore tactical AI."},
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{img_b64}"
                    },
                    {"type": "text", "text": "Give tactical callout."}
                ]
            }
        ]
    )

    callout_text = response.choices[0].message["content"]
    return {"callout": callout_text}
