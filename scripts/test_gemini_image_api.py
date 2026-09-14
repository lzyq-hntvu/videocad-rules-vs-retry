#!/usr/bin/env python3
"""
最小化测试 Google Gemini 图像模型连通性。

用途：
1. 不经过 PaperBanana 全流程；
2. 直接用当前配置文件中的 Google API key；
3. 验证 gemini-3.1-flash-image-preview 是否可正常返回图片。

使用：
    venv/bin/python scripts/test_gemini_image_api.py
"""

import asyncio
import base64
from io import BytesIO
from pathlib import Path

import yaml
from PIL import Image
from google import genai
from google.genai import types


def load_config():
    config_path = Path("paperbanana/configs/model_config.yaml")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    defaults = data.get("defaults", {})
    api_keys = data.get("api_keys", {})
    return {
        "model_name": defaults.get("image_model_name") or defaults.get("model_name"),
        "google_api_key": api_keys.get("google_api_key", ""),
    }


async def main():
    cfg = load_config()
    model_name = cfg["model_name"]
    api_key = cfg["google_api_key"]

    if not api_key:
        raise RuntimeError("Missing google_api_key in paperbanana/configs/model_config.yaml")

    client = genai.Client(api_key=api_key)

    prompt = (
        "Create a clean academic methodology diagram with three blocks from left to right, "
        "minimal text, blue-gray palette, white background, clear arrows, publication style."
    )

    print(f"[info] model: {model_name}")
    print("[info] sending minimal image generation request...")

    response = await client.aio.models.generate_content(
        model=model_name,
        contents=[types.Part.from_text(text=prompt)],
        config=types.GenerateContentConfig(
            temperature=0.7,
            candidate_count=1,
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="16:9",
                image_size="1k",
            ),
        ),
    )

    if not response.candidates or not response.candidates[0].content.parts:
        raise RuntimeError("No candidates returned")

    image_bytes = None
    for part in response.candidates[0].content.parts:
        if getattr(part, "inline_data", None):
            image_bytes = part.inline_data.data
            break

    if not image_bytes:
        raise RuntimeError("No inline image data returned")

    img = Image.open(BytesIO(image_bytes))
    out = Path("figures/raw/test_gemini_direct.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)

    print(f"[ok] saved: {out}")
    print(f"[ok] size: {img.size}")


if __name__ == "__main__":
    asyncio.run(main())
