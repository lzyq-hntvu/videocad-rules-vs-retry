#!/usr/bin/env python3
"""
PaperBanana 调用脚本 - 生成概念框架图

使用前请确保:
1. 已克隆 PaperBanana 仓库到 paperbanana/ 目录
2. 已在 paperbanana/configs/model_config.yaml 中配置 API key
3. 已安装依赖: pip install google-genai streamlit pillow numpy matplotlib pyyaml

使用方法:
    python scripts/generate_framework.py
"""

import sys
import os
from pathlib import Path

# 添加 PaperBanana 到路径（可选）
PAPERBANANA_PATH = Path(__file__).parent.parent / 'paperbanana'
PAPERBANANA_AVAILABLE = PAPERBANANA_PATH.exists()
if PAPERBANANA_AVAILABLE:
    sys.path.insert(0, str(PAPERBANANA_PATH))

# PaperBanana prompts
FIGURE_PROMPTS = {
    "framework": """
Title: Research Framework for Visual Reliability in Complex GUI Multi-step Tasks

Content Structure:
1. Left side: GUI scenario representation (multiple windows, UI controls, toolbars)
2. Center: Error propagation chain diagram showing "Input → Propagation → Threshold → Suppression"
3. Right side: Three hypotheses H1, H2, H3 with their relationships

H1 (Perceptual Error Input): Shows robust feature representation resisting domain perturbation
H2 (Rule Suppression): Demonstrates how minimum rule set suppresses cascade failures
H3 (Threshold Formation): Illustrates error propagation threshold varying by complexity

Style Requirements:
- Academic paper figure style, clean and professional
- Light gray background (#FAFAFA)
- Blue primary color scheme (#2E5C8A, #4A90D9)
- Black text for readability
- Clear visual hierarchy with arrows connecting components
- Suitable for NSFC (National Natural Science Foundation of China) proposal

Layout: Horizontal flow from left (input) to right (mechanisms)
Quality: High-resolution, publication-ready
""",

    "roadmap": """
Title: Research Technical Roadmap - Four-Step Research Plan

Step 1: Task Chain Representation and Complexity Stratification
- Multi-step GUI task modeling
- Complexity metrics and layer division (Low/Medium/High)
- 44,291 action chains from VideoCAD dataset

Step 2: Perceptual Error Modeling and Robust Representation
- Controlled domain perturbation experiments
- Baseline vs Robust feature comparison
- H1 validation: Error input modeling

Step 3: Execution Chain Propagation Modeling and Threshold Estimation
- Error propagation mechanism analysis
- Threshold ε* estimation by complexity
- H3 validation: Threshold formation

Step 4: Rule Constraints and Suppression Mechanism
- Minimum rule set design
- Cascade failure suppression
- H2 validation: Rule suppression effectiveness

Style Requirements:
- Horizontal flowchart layout
- Arrow connections between steps
- Step numbers clearly marked
- Brief description for each step
- Blue gradient color scheme
- Professional academic style
- Suitable for NSFC proposal

Quality: High-resolution, publication-ready
""",

    "data_platform": """
Title: Data Platform Overview - VideoCAD Experimental Foundation

Content:
- Total: 44,291 action chains
- Complexity Distribution:
  * Low complexity: 14,616 chains
  * Medium complexity: 15,059 chains
  * High complexity: 14,616 chains
- Image-Action Paired Samples: 135 (linkable pool)
- CAD Images Total: 236,321
- Overlapping Samples: 12,145

Visual Elements:
- Hierarchical data structure diagram
- Statistics displayed prominently
- Database/storage icon suggestions
- Connection lines showing relationships

Style Requirements:
- Information graphic style
- Blue color scheme (#2E5C8A, #4A90D9, #5DADE2)
- Clean data visualization
- Professional academic appearance
- Suitable for NSFC proposal

Quality: High-resolution, publication-ready
""",

    "error_propagation": """
Title: Error Propagation Mechanism in Multi-step GUI Tasks

Content Structure:
1. Single-step error: Perceptual noise ε affecting visual understanding
2. Multi-step propagation: Error accumulation and cascade effects
3. Illegal state diffusion: How small errors lead to invalid action chains
4. Threshold phenomenon: Success rate drops sharply beyond ε*
5. Complexity factor: Higher complexity → lower threshold

Visual Elements:
- Before/After comparison
- Error propagation pathway arrows
- Cascade failure illustration
- Threshold crossing visualization
- Three complexity levels (Low/Medium/High) shown side by side

Style Requirements:
- Mechanism diagram style
- Red for error/danger states
- Green for safe/success states
- Blue for neutral process
- Clear directional flow
- Professional academic style
- Suitable for NSFC proposal

Quality: High-resolution, publication-ready
"""
}


def check_paperbanana_setup():
    """检查 PaperBanana 配置"""
    if not PAPERBANANA_PATH.exists():
        return False
    config_path = PAPERBANANA_PATH / 'configs' / 'model_config.yaml'
    return config_path.exists()


def generate_figure(figure_type: str, output_dir: Path = None):
    """生成指定类型的图"""
    if figure_type not in FIGURE_PROMPTS:
        print(f"Error: Unknown figure type '{figure_type}'")
        print(f"Available types: {list(FIGURE_PROMPTS.keys())}")
        return

    # 仅检查 PaperBanana 配置（用于后续实际生成）
    has_paperbanana = check_paperbanana_setup()
    if not has_paperbanana:
        print("\nNote: PaperBanana not configured yet. Prompts will still be generated.")
        print("Configure PaperBanana to use actual generation features.\n")

    # 这里应该调用 PaperBanana 的生成函数
    # 由于 PaperBanana 是交互式工具，这里提供 prompt 供用户复制使用

    prompt = FIGURE_PROMPTS[figure_type]

    print(f"\n{'='*60}")
    print(f"Figure Type: {figure_type}")
    print(f"{'='*60}")
    print("\nPrompt for PaperBanana:\n")
    print(prompt)
    print(f"\n{'='*60}")

    # 保存 prompt 到文件
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / 'figures' / 'raw'
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt_file = output_dir / f"{figure_type}_prompt.txt"
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)
    print(f"\nPrompt saved to: {prompt_file}")


def generate_all():
    """生成所有概念图 prompt"""
    output_dir = Path(__file__).parent.parent / 'figures' / 'raw'

    for figure_type in FIGURE_PROMPTS.keys():
        generate_figure(figure_type, output_dir)
        print("\n" + "-"*60 + "\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate prompts for PaperBanana framework figures'
    )
    parser.add_argument(
        'figure_type',
        nargs='?',
        choices=list(FIGURE_PROMPTS.keys()) + ['all'],
        help='Type of figure to generate (or "all")'
    )

    args = parser.parse_args()

    if args.figure_type == 'all' or args.figure_type is None:
        generate_all()
    else:
        generate_figure(args.figure_type)


if __name__ == '__main__':
    main()
