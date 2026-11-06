"""生成无外部版权素材的小型示例；默认只创建缺失文件。"""

from pathlib import Path

from PIL import Image, ImageDraw


def main():
    directory = Path(__file__).resolve().parent / "examples"
    directory.mkdir(exist_ok=True)
    path = directory / "demo.png"
    if not path.exists():
        with Image.new("RGB", (640, 480), "#e8f0fa") as image:
            draw = ImageDraw.Draw(image)
            draw.rectangle((30, 30, 300, 220), fill="#2364aa")
            draw.ellipse((350, 80, 590, 320), fill="#ffba49")
            draw.polygon([(80, 420), (270, 250), (440, 420)], fill="#dc4c46")
            draw.text((35, 12), "TOP LEFT - Python Image Tool", fill="black")
            image.save(path)
    path = directory / "transparent.png"
    if not path.exists():
        with Image.new("RGBA", (320, 240), (0, 0, 0, 0)) as image:
            draw = ImageDraw.Draw(image)
            draw.rectangle((40, 40, 150, 190), fill=(35, 100, 170, 255))
            draw.ellipse((120, 60, 280, 220), fill=(220, 76, 70, 128))
            image.save(path)
    print(f"示例图片已就绪：{directory}")


if __name__ == "__main__":
    main()
