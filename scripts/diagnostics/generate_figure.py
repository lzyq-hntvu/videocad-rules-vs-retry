#!/usr/bin/env python3
"""
直接生成国自然研究框架图
"""

import asyncio
import sys
import base64
from pathlib import Path
from io import BytesIO
from PIL import Image

# 添加 paperbanana 到路径
sys.path.insert(0, str(Path.cwd() / "paperbanana"))

from utils import config
from agents.planner_agent import PlannerAgent
from agents.visualizer_agent import VisualizerAgent

# 国自然研究框架图的 prompt
PROMPT = """Title: Research Framework for Visual Reliability in Complex GUI Multi-step Tasks

Content Structure:
1. Left side: GUI scenario with multiple windows, toolbars, and UI controls
2. Center: Error propagation chain showing four stages - "Input → Propagation → Threshold → Suppression"
3. Right side: Three research hypotheses H1, H2, H3 with connections

H1 (Perceptual Error Input): Robust feature representation resists domain perturbation
H2 (Rule Suppression): Minimum rule set suppresses cascade failures
H3 (Threshold Formation): Error propagation threshold varies by task complexity

Style Requirements:
- Academic paper figure style, clean and professional
- Light gray background (#FAFAFA)
- Blue primary color scheme (#2E5C8A, #4A90D9)
- Black text for readability
- Clear visual hierarchy with arrows
- Suitable for NSFC proposal

Layout: Horizontal flow from left to right
Quality: High-resolution, publication-ready"""

async def generate():
    print("🎨 正在生成国自然研究框架图...")
    print("=" * 60)

    # 创建配置
    exp_config = config.ExpConfig(
        dataset_name="Demo",
        split_name="demo",
        exp_mode="dev_planner_critic",
        retrieval_setting="auto",
        model_name="gemini-3-pro-image-preview",
        work_dir=Path.cwd() / "paperbanana",
    )

    # 准备输入数据
    input_data = {
        "filename": "nsfc_framework",
        "caption": "复杂GUI多步骤任务视觉可靠性研究框架",
        "content": PROMPT,
        "visual_intent": "研究框架图，展示三条假设的逻辑关系",
        "additional_info": {"rounded_ratio": "16:9"},
        "max_critic_rounds": 2
    }

    print("📝 Step 1: Planner 规划...")
    planner = PlannerAgent(exp_config=exp_config)
    data = await planner.process(input_data)
    print("✅ 规划完成")

    print("🎨 Step 2: Visualizer 生成图像...")
    print("⏳ 这可能需要 30-60 秒，请等待...")
    visualizer = VisualizerAgent(exp_config=exp_config)
    data = await visualizer.process(data)
    print("✅ 图像生成完成")

    # 保存图像
    img_key = "target_diagram_desc0_base64_jpg"
    if img_key in data and data[img_key]:
        img_data = base64.b64decode(data[img_key])
        img = Image.open(BytesIO(img_data))

        output_path = Path("figures/raw/fig1_framework_generated.png")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path)

        print(f"💾 图像已保存: {output_path}")
        print(f"📐 尺寸: {img.size}")
        return output_path
    else:
        print("❌ 未找到生成的图像")
        return None

if __name__ == "__main__":
    result = asyncio.run(generate())
    if result:
        print("\n🎉 生成成功！")
        print(f"查看图片: {result}")
    else:
        print("\n❌ 生成失败")
