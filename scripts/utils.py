#!/usr/bin/env python3
"""
NSFC 配图公共样式配置
统一配色、字体和图形规范
"""

from matplotlib import rcParams

# 国自然申报书配色方案
COLORS = {
    # 主色调
    'primary': '#2E5C8A',           # 深蓝
    'primary_light': '#4A90D9',     # 浅蓝
    'primary_lighter': '#5DADE2',   # 中蓝
    'primary_lightest': '#85C1E9',  # 淡蓝

    # 强调色
    'accent_orange': '#E67E22',     # 橙色（对比强调）
    'accent_red': '#C0392B',        # 红色（警告/无规则）
    'accent_green': '#27AE60',      # 绿色（成功/有规则）

    # 中性色
    'text': '#333333',              # 主要文字
    'text_secondary': '#666666',    # 次要文字
    'grid': '#E8E8E8',              # 网格线
    'background': '#FAFAFA',        # 背景
    'white': '#FFFFFF',

    # 复杂度分层色
    'low': '#4A90D9',               # 低复杂度
    'medium': '#5DADE2',            # 中复杂度
    'high': '#85C1E9',              # 高复杂度

    # 方法对比色
    'baseline': '#2E5C8A',          # Baseline方法
    'robust': '#E67E22',            # Robust方法
    'no_rule': '#C0392B',           # 无规则
    'min_rule': '#27AE60',          # 最小规则集
}

# 图表尺寸规范（英寸）
FIGURE_SIZES = {
    'single_column': (8, 6),        # 单栏图
    'double_column': (16, 6),       # 双栏图
    'full_page': (16, 10),          # 整页大图
    'mechanism': (12, 8),           # 机制示意图
}

# DPI设置
DPI = {
    'screen': 150,
    'print': 300,
    'publication': 600,
}


def setup_chinese_font():
    """配置中文字体支持"""
    rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
    rcParams['axes.unicode_minus'] = False


def setup_nsfc_style():
    """设置国自然图表统一样式"""
    setup_chinese_font()

    # 坐标轴样式
    rcParams['axes.edgecolor'] = COLORS['text']
    rcParams['axes.labelcolor'] = COLORS['text']
    rcParams['axes.linewidth'] = 1.0
    rcParams['axes.spines.top'] = False
    rcParams['axes.spines.right'] = False

    # 网格样式
    rcParams['grid.color'] = COLORS['grid']
    rcParams['grid.linestyle'] = '--'
    rcParams['grid.alpha'] = 0.5

    # 刻度样式
    rcParams['xtick.color'] = COLORS['text']
    rcParams['ytick.color'] = COLORS['text']
    rcParams['xtick.direction'] = 'out'
    rcParams['ytick.direction'] = 'out'

    # 图例样式
    rcParams['legend.frameon'] = True
    rcParams['legend.framealpha'] = 0.9
    rcParams['legend.edgecolor'] = COLORS['grid']

    # 文字大小
    rcParams['font.size'] = 10
    rcParams['axes.titlesize'] = 12
    rcParams['axes.labelsize'] = 11
    rcParams['xtick.labelsize'] = 9
    rcParams['ytick.labelsize'] = 9
    rcParams['legend.fontsize'] = 9


def get_output_path(filename, format='png'):
    """获取输出文件路径"""
    from pathlib import Path
    output_dir = Path(__file__).parent.parent / 'figures'
    output_dir.mkdir(exist_ok=True)
    return output_dir / f"{filename}.{format}"


def save_figure(fig, filename, formats=None):
    """保存图表为多种格式"""
    from pathlib import Path

    if formats is None:
        formats = ['png', 'pdf']

    output_dir = Path(__file__).parent.parent / 'figures'
    output_dir.mkdir(exist_ok=True)

    saved_paths = []
    for fmt in formats:
        path = output_dir / f"{filename}.{fmt}"
        dpi = DPI['print'] if fmt == 'png' else None
        fig.savefig(path, dpi=dpi, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        saved_paths.append(path)
        print(f"Saved to: {path}")

    return saved_paths
