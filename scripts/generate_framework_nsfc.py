#!/usr/bin/env python3
"""
为国自然申报书生成专用的 PaperBanana 配图 prompts。

设计原则：
1. 少文字：只保留短标签与结构指令，避免让图像模型直接渲染长文本。
2. 强结构：优先生成分区、箭头、容器、层次关系。
3. 易后修：为后续在 PPT / draw.io 中手工替换中文文字预留空位。

使用方法：
    python scripts/generate_framework_nsfc.py
    python scripts/generate_framework_nsfc.py framework
"""

from pathlib import Path


NSFC_PROMPTS = {
    "framework": """
Task: Create a publication-style methodology diagram for a Chinese NSFC proposal.

Goal:
Generate a clean conceptual framework diagram with strong layout and minimal embedded text.

Layout:
- Horizontal layout, left to right, ratio 16:9
- Three large zones with clear spacing
- Zone A (left): GUI task scene container
- Zone B (center): mechanism chain container
- Zone C (right): three hypothesis modules

Zone A:
- Show a simplified browser-based CAD / GUI scene
- Include abstract UI blocks only: toolbar, panel, canvas, small controls
- No dense screenshots, no realistic text
- Use this zone as "problem context"

Zone B:
- Show a clear four-step mechanism chain
- Four rounded rectangular modules in sequence
- Use only short labels: Input, Propagation, Threshold, Suppression
- Use thick clean arrows between modules
- Keep enough blank space inside each module for later manual relabeling

Zone C:
- Show three stacked or triangular hypothesis blocks
- Use only short labels: H1, H2, H3
- H1 linked to Input
- H3 linked to Threshold
- H2 linked to Suppression
- Add one feedback arrow from H2 back toward the chain

Style:
- Academic scientific figure, not poster style
- Light background, very pale blue / light gray zones
- Medium blue as primary highlight color
- Dark gray lines, no heavy black borders
- Rounded rectangles, soft geometry
- Clean whitespace, strong alignment, minimal decorative icons
- No cartoon characters, no excessive gradients

Hard constraints:
- Do not render long sentences
- Do not fill boxes with illegible small text
- Prioritize layout fidelity over typography
- Leave visible empty label space for later manual editing
""",

    "roadmap": """
Task: Create a technical roadmap figure for a Chinese NSFC proposal.

Goal:
Generate a rigorous research roadmap with milestone-style structure, not a flashy infographic.

Layout:
- Horizontal 16:9 layout
- Four sequential stages from left to right
- Each stage as one large rounded block
- A thin timeline or directional flow line underneath
- Leave a narrow bottom band for later manual year labels

Stage blocks:
- Stage 1 label only: WP1
- Stage 2 label only: WP2
- Stage 3 label only: WP3
- Stage 4 label only: Integration

Inside each stage:
- Use 2-3 abstract sub-blocks only
- No paragraph text
- Use short placeholders only: Data, Model, Rules, Eval, Merge
- Leave empty space for later Chinese annotations

Semantic hints:
- WP1 focuses on perceptual error input
- WP2 focuses on rule suppression
- WP3 focuses on threshold estimation
- Integration focuses on unified mechanism evidence

Style:
- Clean academic roadmap
- White or very pale background
- Soft blue-gray palette
- Thin but clear arrows
- Professional, restrained, publication-ready
- No decorative 3D effects

Hard constraints:
- No dense text
- No colorful dashboard style
- Do not turn it into a business process chart
- Keep the structure formal, stable, and easy to annotate manually
""",

    "data_platform": """
Task: Create a data foundation / experimental base diagram for a Chinese NSFC proposal.

Goal:
Generate a structured data-base figure showing experimental foundation and sample stratification.

Layout:
- 4:3 ratio
- Top: one source data container
- Middle: one processing pipeline band
- Bottom: three stratified sample groups

Top container:
- One large data source block
- Include abstract data icons only
- Show two subtypes visually: action chain files and image files
- No detailed filenames in the image

Middle pipeline:
- Three processing nodes connected left to right
- Use only short labels: Parse, Pair, Stratify
- Optional small side node: Pool

Bottom:
- Three aligned sample groups
- Use only short labels: Low, Medium, High
- Each group displayed as a compact stack or card cluster
- One small linked subset node for multimodal pool

Visual intent:
- Show that a reproducible experimental base already exists
- Emphasize hierarchy, processing, and stratified outputs
- Keep statistics as visual placeholders only; exact numbers will be added manually

Style:
- Clean academic information diagram
- Soft blue and pale cyan blocks
- Subtle dashed borders for logical groups
- Clear alignment, no visual clutter
- Suitable for proposal body figure

Hard constraints:
- No large numeric paragraphs rendered into the image
- No crowded database infographic style
- Prioritize structure and grouping over text
""",

    "error_propagation": """
Task: Create a mechanism diagram for error propagation and threshold formation in complex GUI multi-step tasks.

Goal:
Generate a visually clear mechanism figure for a Chinese NSFC proposal, emphasizing process and threshold behavior.

Layout:
- Horizontal 16:9 layout
- Left: local perceptual error source
- Center: propagation chain and cascade expansion
- Right: threshold drop and comparison by complexity

Left section:
- One input disturbance node
- Use short label only: e
- Connect to a small GUI state block

Center section:
- Show a multi-step chain of 4-5 states
- Early states mostly stable, then instability spreads
- Use a mix of neutral and warning colors
- Add one dashed branch to indicate illegal diffusion
- Keep arrows clear and directional

Right section:
- Show a threshold concept visually
- One curve panel or slope panel
- Three simple level indicators labeled only: Low, Medium, High
- Make High appear to fail earlier than Low
- Add a small rule-shift cue showing threshold can move rightward

Style:
- Mechanism figure, not a data-heavy chart
- White / pale background
- Blue-gray for normal states
- Red reserved for failure / threshold crossing
- Green can be used sparingly for suppressed / recovered state
- Strong visual hierarchy, minimal text

Hard constraints:
- No long labels
- No tiny illegible annotations
- Keep the figure readable after manual relabeling
- Focus on causal flow and threshold intuition
""",
}


def write_prompt(name: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{name}_nsfc_prompt.txt"
    path.write_text(NSFC_PROMPTS[name].strip() + "\n", encoding="utf-8")
    return path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate NSFC-optimized prompts for PaperBanana"
    )
    parser.add_argument(
        "figure_type",
        nargs="?",
        choices=list(NSFC_PROMPTS.keys()) + ["all"],
        default="all",
        help="Prompt type to generate",
    )
    args = parser.parse_args()

    output_dir = Path(__file__).parent.parent / "figures" / "raw"
    if args.figure_type == "all":
        for name in NSFC_PROMPTS:
            path = write_prompt(name, output_dir)
            print(f"[ok] {name}: {path}")
    else:
        path = write_prompt(args.figure_type, output_dir)
        print(f"[ok] {args.figure_type}: {path}")


if __name__ == "__main__":
    main()
