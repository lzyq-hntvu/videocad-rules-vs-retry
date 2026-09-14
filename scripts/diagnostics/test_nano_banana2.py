#!/usr/bin/env python3
"""
测试 Nano Banana2 API Key 是否有效
使用 laozhang.ai 的图像生成服务
"""

import requests
import json
import re
import base64
from pathlib import Path

# API 配置
API_KEY = "sk-CsD4FRRiJeiIlBraFb4bF4Ad4d624297B4C9B3A847EfA6Ea"
API_URL = "https://api.laozhang.ai/v1/chat/completions"

def test_image_generation():
    """测试图像生成功能"""
    print("=" * 60)
    print("🧪 测试 Nano Banana2 图像生成 API")
    print("=" * 60)
    print()

    # 请求参数
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
                "content": "A simple academic diagram showing three boxes connected by arrows, blue color scheme, clean professional style, white background, minimal design"
            }
        ]
    }

    print(f"📡 API 端点: {API_URL}")
    print(f"🔑 API Key: {API_KEY[:10]}...{API_KEY[-4:]}")
    print(f"🤖 模型: gemini-3.1-flash-image-preview")
    print()
    print("⏳ 正在发送请求，请等待...")
    print()

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=120
        )

        print(f"📊 HTTP 状态码: {response.status_code}")
        print()

        if response.status_code == 200:
            data = response.json()

            # 检查响应内容
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]

                # 尝试提取 base64 图片
                match = re.search(r'!\[.*?\]\((data:image/png;base64,.*?)\)', content)

                if match:
                    print("✅ API Key 有效！图像生成成功！")
                    print()

                    # 保存图片
                    base64_data = match.group(1)
                    image_data = base64.b64decode(base64_data.split(',')[1])

                    output_path = Path(__file__).parent / "test_output.png"
                    with open(output_path, 'wb') as f:
                        f.write(image_data)

                    print(f"💾 测试图片已保存: {output_path}")
                    print(f"📐 图片大小: {len(image_data)} bytes")
                    return True

                else:
                    print("⚠️ 响应中没有找到图片，返回内容:")
                    print(content[:500])
                    return False
            else:
                print("⚠️ 响应格式异常:")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
                return False

        elif response.status_code == 401:
            print("❌ API Key 无效！")
            print("请检查:")
            print("1. API Key 是否正确")
            print("2. 是否已从 laozhang.ai 充值")
            print("3. API Key 是否已过期")
            return False

        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text[:500]}")
            return False

    except requests.exceptions.Timeout:
        print("⏰ 请求超时（120秒）")
        print("可能原因: 网络问题或服务繁忙")
        return False

    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")
        return False


def test_simple_chat():
    """测试简单的对话功能（不生成图像，仅验证 key）"""
    print()
    print("=" * 60)
    print("🧪 测试 API Key 连通性（简单对话）")
    print("=" * 60)
    print()

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # 使用普通模型测试连通性
    payload = {
        "model": "gpt-4o-mini",
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": "Hello, are you working?"
            }
        ]
    }

    try:
        response = requests.post(
            "https://api.laozhang.ai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            print("✅ API Key 有效，服务连通正常！")
            data = response.json()
            if "choices" in data:
                content = data["choices"][0]["message"]["content"]
                print(f"📝 模型回复: {content[:100]}...")
            return True
        else:
            print(f"❌ 连通性测试失败: {response.status_code}")
            print(f"错误: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ 连接错误: {str(e)}")
        return False


def main():
    """主函数"""
    print("\n" + "🍌" * 30)
    print()

    # 先测试连通性
    chat_ok = test_simple_chat()

    if chat_ok:
        print()
        print("-" * 60)
        print()
        # 再测试图像生成
        image_ok = test_image_generation()

        print()
        print("=" * 60)
        print("📋 测试结果汇总")
        print("=" * 60)
        print(f"对话连通性: {'✅ 通过' if chat_ok else '❌ 失败'}")
        print(f"图像生成: {'✅ 通过' if image_ok else '❌ 失败'}")

        if chat_ok and image_ok:
            print()
            print("🎉 所有测试通过！API Key 配置正确！")
            print()
            print("现在可以配置 PaperBanana 使用此 API:")
            print("1. model_name: gemini-3.1-flash-image-preview")
            print("2. 使用 OpenAI 格式调用")
        else:
            print()
            print("⚠️ 部分测试失败，请检查配置")
    else:
        print()
        print("❌ API Key 无效或网络问题")
        print()
        print("建议:")
        print("1. 登录 https://laozhang.ai 检查 API Key")
        print("2. 确认账户有余额")
        print("3. 检查网络连接")


if __name__ == "__main__":
    main()
