#!/usr/bin/env python3
"""
检查 NSFC 配图项目配置状态
"""

import json
import sys
from pathlib import Path

# 颜色输出
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def check_item(name, condition, ok_msg, fail_msg, optional=False):
    """检查单项并输出结果"""
    icon = "✅" if condition else "⚠️" if optional else "❌"
    color = GREEN if condition else YELLOW if optional else RED
    msg = ok_msg if condition else fail_msg
    print(f"{icon} {color}{name}: {msg}{RESET}")
    return condition

def main():
    print("=" * 60)
    print("NSFC 配图项目配置检查")
    print("=" * 60)
    print()

    base_path = Path(__file__).parent

    # 检查虚拟环境
    venv_exists = (base_path / "venv").exists()
    check_item("虚拟环境", venv_exists,
               "已创建 (venv/)",
               "未创建，请运行: python -m venv venv")

    # 检查依赖
    try:
        import matplotlib
        import PIL
        deps_ok = True
    except ImportError:
        deps_ok = False
    check_item("Python 依赖", deps_ok,
               "已安装 (matplotlib, pillow, 等)",
               "未安装，请激活虚拟环境后运行: pip install -r requirements.txt")

    # 检查 PaperBanana
    pb_exists = (base_path / "paperbanana").exists()
    check_item("PaperBanana", pb_exists,
               "已克隆 (paperbanana/)",
               "未克隆，请运行: git clone https://github.com/dwzhu-pku/PaperBanana.git paperbanana")

    # 检查 API Key 配置
    config_file = base_path / "paperbanana" / "configs" / "model_config.yaml"
    api_configured = False
    if config_file.exists():
        content = config_file.read_text()
        api_configured = 'google_api_key: ""' not in content and 'google_api_key:' in content

    check_item("API Key", api_configured,
               "已配置",
               f"未配置，请编辑: {config_file}",
               optional=True)

    # 检查预实验数据
    data_file = base_path / "data" / "preliminary_results.json"
    data_exists = data_file.exists()
    check_item("预实验数据", data_exists,
               f"已创建 ({data_file})",
               f"未创建")

    # 检查已生成图表
    figures = list((base_path / "figures").glob("fig*.png"))
    check_item("数据图表", len(figures) > 0,
               f"已生成 {len(figures)} 张",
               "未生成，请运行: python scripts/plot_h1_results.py",
               optional=True)

    print()
    print("=" * 60)

    # 下一步建议
    if not api_configured:
        print()
        print("📋 下一步操作:")
        print()
        print("1. 访问 https://laozhang.ai 注册账号")
        print("2. 获取 Google API Key")
        print("3. 编辑 paperbanana/configs/model_config.yaml:")
        print("   将 google_api_key: \"\" 改为 google_api_key: \"your-api-key\"")
        print("4. 启动 PaperBanana:")
        print("   source activate_venv.sh")
        print("   streamlit run paperbanana/main.py")
        print()

    # 检查 prompts
    prompts = list((base_path / "figures" / "raw").glob("*_prompt.txt"))
    if prompts:
        print(f"📝 已生成的 Prompts ({len(prompts)} 个):")
        for p in prompts:
            print(f"   - figures/raw/{p.name}")
        print()

if __name__ == "__main__":
    main()
