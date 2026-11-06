"""图片信息读取与编辑。运行 python image_tool.py --help 查看用法。"""

import argparse
from pathlib import Path
import sys
import warnings

from PIL import Image, UnidentifiedImageError


class ImageToolError(Exception):
    """可直接展示给使用者的错误。"""


MAX_OUTPUT_PIXELS = 40_000_000


def positive_int(text):
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError("宽高必须是正整数") from None
    if value <= 0:
        raise argparse.ArgumentTypeError("宽高必须大于 0")
    return value


def resize_image(image, width=None, height=None):
    if width is None and height is None:
        raise ImageToolError("缩放时至少指定 --width 或 --height 中的一项。")
    if (width is not None and width <= 0) or (height is not None and height <= 0):
        raise ImageToolError("宽高必须大于 0。")
    # 像素数只能取整数；窄边至少保留 1 像素。
    if width is None:
        width = max(1, round(image.width * height / image.height))
    if height is None:
        height = max(1, round(image.height * width / image.width))
    if width * height > MAX_OUTPUT_PIXELS:
        raise ImageToolError("缩放结果超过 4000 万像素，请减小宽高。")
    # 调色板图片先转色，以便使用高质量的重采样并保留透明度。
    if image.mode == "P":
        image = image.convert("RGBA" if "transparency" in image.info else "RGB")
    return image.resize((width, height), Image.Resampling.LANCZOS)


def crop_image(image, box):
    left, top, right, bottom = box
    if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
        raise ImageToolError(
            f"裁剪区域不合法或越界：需要 0 ≤ 左 < 右 ≤ {image.width}，"
            f"0 ≤ 上 < 下 ≤ {image.height}。"
        )
    return image.crop((left, top, right, bottom))


def save_result(image, source, output, operation):
    """以独占创建方式写入：即使存在同名文件，也不会覆盖。"""
    if output:
        target = Path(output).expanduser().resolve()
    else:
        directory = Path.cwd() / "results"
        target = directory / f"{Path(source).stem}_{operation}.png"
        number = 1
        while target.exists():
            target = directory / f"{Path(source).stem}_{operation}_{number}.png"
            number += 1
    if target.resolve() == Path(source).resolve():
        raise ImageToolError("输出路径不能与原图相同，请指定新文件。")
    formats = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG"}
    suffix = target.suffix.lower()
    if suffix not in formats:
        raise ImageToolError("输出文件扩展名仅支持 .png、.jpg 或 .jpeg。")
    target.parent.mkdir(parents=True, exist_ok=True)
    # JPEG 不支持透明通道：先在白色背景上合成，再转成 RGB。
    if suffix in (".jpg", ".jpeg"):
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", image.size, "white")
        image = Image.alpha_composite(background, rgba).convert("RGB")
    elif image.mode not in ("1", "L", "LA", "P", "RGB", "RGBA", "I", "I;16"):
        image = image.convert("RGBA")
    try:
        stream = target.open("xb")
    except FileExistsError:
        raise ImageToolError(f"输出文件已存在，不会覆盖：{target}。请换一个文件名。") from None
    try:
        with stream:
            image.save(stream, format=formats[suffix])
    except (OSError, ValueError):
        # 保存失败时只清理本次刚创建的不完整文件。
        target.unlink(missing_ok=True)
        raise
    return target.resolve()


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
    resize = commands.add_parser("resize", help="缩放；只给宽或高则保持比例")
    resize.add_argument("input", help="输入图片路径")
    resize.add_argument("--width", type=positive_int, help="目标宽度，正整数")
    resize.add_argument("--height", type=positive_int, help="目标高度，正整数")
    resize.add_argument("-o", "--output", help="新文件路径，默认保存到 results")
    crop = commands.add_parser("crop", help="裁剪，坐标从左上角 (0, 0) 开始")
    crop.add_argument("input", help="输入图片路径")
    crop.add_argument("--box", nargs=4, type=int, required=True,
                      metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"), help="左 上 右 下")
    crop.add_argument("-o", "--output", help="新文件路径，默认保存到 results")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        with load_image(args.input) as image:
            if args.command == "info":
                print(image_info(args.input, image))
            else:
                if args.command == "resize":
                    result = resize_image(image, args.width, args.height)
                else:
                    result = crop_image(image, args.box)
                with result:
                    path = save_result(result, args.input, args.output, args.command)
                    print(f"处理完成：{result.width} × {result.height} 像素")
                    print(f"保存位置：{path}")
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
