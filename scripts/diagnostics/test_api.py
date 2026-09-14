import requests
import json
import base64
import re

API_KEY = "sk-CsD4FRRiJeiIlBraFb4bF4Ad4d624297B4C9B3A847EfA6Ea"

# 测试图像生成
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "gemini-3.1-flash-image-preview",
    "stream": False,
    "messages": [
        {
            "role": "user",
            "content": "A blue academic diagram with 3 boxes"
        }
    ]
}

print("Testing Nano Banana2 image generation...")
print(f"URL: https://api.laozhang.ai/v1/chat/completions")
print()

resp = requests.post(
    "https://api.laozhang.ai/v1/chat/completions",
    headers=headers,
    json=payload,
    timeout=120
)

print(f"Status: {resp.status_code}")
print()

if resp.status_code == 200:
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    
    # 提取图片
    match = re.search(r'!\[.*?\]\((data:image/png;base64,.*?)\)', content)
    if match:
        print("✅ Success! Image generated.")
        b64 = match.group(1).split(',')[1]
        img = base64.b64decode(b64)
        with open('test_image.png', 'wb') as f:
            f.write(img)
        print(f"✅ Saved: test_image.png ({len(img)} bytes)")
    else:
        print("⚠️ No image in response:")
        print(content[:500])
else:
    print(f"❌ Failed: {resp.text[:500]}")
