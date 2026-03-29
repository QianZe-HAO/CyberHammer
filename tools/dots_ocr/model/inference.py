import requests
from tools.dots_ocr.utils.image_utils import PILimage_to_base64
from openai import OpenAI
import os
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException),
    reraise=True,
)
def inference_with_pai(
    image,
    prompt,
    temperature=0.1,
    top_p=0.9,
    max_completion_tokens=32768,
    model_name="dots.ocr",
):
    load_dotenv()
    OCR_API_KEY = os.getenv("OCR_API_KEY")
    OCR_BASE_URL = os.getenv("OCR_BASE_URL")

    if not OCR_API_KEY or not OCR_BASE_URL:
        raise ValueError("OCR_API_KEY or OCR_BASE_URL not set in .env file")

    client = OpenAI(api_key=OCR_API_KEY, base_url=OCR_BASE_URL)
    messages = []
    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": PILimage_to_base64(image)},
                },
                {
                    "type": "text",
                    "text": f"<|img|><|imgpad|><|endofimg|>{prompt}",
                },
            ],
        }
    )
    try:
        response = client.chat.completions.create(
            messages=messages,
            model=model_name,
            max_completion_tokens=max_completion_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        response = response.choices[0].message.content
        return response
    except requests.exceptions.RequestException as e:
        print(f"request error: {e}")
        return None
