"""图片信息读取与编辑。运行 python image_tool.py --help 查看用法。"""

import argparse
from pathlib import Path
import sys
import warnings

from PIL import Image, UnidentifiedImageError


class ImageToolError(Exception):
    """可直接展示给使用者的错误。"""


def load_image(path):
    """在文件关闭前完成解码，避免把损坏图片误当作可用图片。"""
    path = Path(path)
    if not path.is_file():
        raise ImageToolError(f"图片文件不存在或不是普通文件：{path}")
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(path) as opened:
            opened.load()
            image = opened.copy()
            image.format = opened.format
            return image


def image_info(path, image):
    size = Path(path).stat().st_size
    size_text = f"{size / 1024:.2f} KB"
    if size >= 1024 * 1024:
        size_text = f"{size / (1024 * 1024):.2f} MB"
    modes = {"L": "灰度", "1": "黑白", "P": "调色板"}
    mode = image.mode
    if mode in modes:
        mode += f"（{modes[mode]}）"
    return "\n".join([
        f"文件名：{Path(path).name}",
        f"图片格式：{image.format or '未知'}",
        f"宽度：{image.width} 像素",
        f"高度：{image.height} 像素",
        f"颜色模式：{mode}",
        f"文件大小：{size_text}",
    ])


def build_parser():
    parser = argparse.ArgumentParser(description="读取图片信息和进行简单编辑（保留原图）")
    commands = parser.add_subparsers(dest="command", required=True)
    info = commands.add_parser("info", help="显示图片基础信息")
    info.add_argument("input", help="输入图片路径，有空格时请加双引号")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        with load_image(args.input) as image:
            print(image_info(args.input, image))
        return 0
    except ImageToolError as error:
        print(f"错误：{error}", file=sys.stderr)
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        print("错误：图片像素过大，请先使用较小图片。", file=sys.stderr)
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, EOFError) as error:
        print(f"错误：图片无法读取或处理，请检查文件、权限和参数。详情：{error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
