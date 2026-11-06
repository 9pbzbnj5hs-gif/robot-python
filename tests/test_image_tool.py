"""通过真实命令行验证输出图片与失败行为；测试文件在临时目录自动清理。"""

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image


SCRIPT = Path(__file__).resolve().parents[1] / "image_tool.py"


class ImageToolTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / "中文 示例.png"
        # 不对称图案用于识别旋转和翻转方向。
        self.pixels = [(x * 50, y * 80, 30) for y in range(3) for x in range(4)]
        with Image.new("RGB", (4, 3)) as image:
            image.putdata(self.pixels)
            image.save(self.source)
        self.original_hash = hashlib.sha256(self.source.read_bytes()).hexdigest()

    def run_cli(self, *args, success=True):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)], cwd=self.root,
            capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=20,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.original_hash)
        return result

    def assert_output(self, name, size, mode=None, format=None):
        with Image.open(self.root / name) as image:
            image.load()
            self.assertEqual(image.size, size)
            if mode:
                self.assertEqual(image.mode, mode)
            if format:
                self.assertEqual(image.format, format)

    def test_information_and_unicode_path(self):
        result = self.run_cli("info", self.source)
        for expected in ("中文 示例.png", "PNG", "宽度：4", "高度：3", "RGB"):
            self.assertIn(expected, result.stdout)
        self.assertRegex(result.stdout, r"文件大小：\d+\.\d{2} KB")

    def test_resize_width_only(self):
        self.run_cli("resize", self.source, "--width", 8, "-o", "width.png")
        self.assert_output("width.png", (8, 6))

    def test_resize_height_only(self):
        self.run_cli("resize", self.source, "--height", 6, "-o", "height.png")
        self.assert_output("height.png", (8, 6))

    def test_resize_both_dimensions(self):
        self.run_cli("resize", self.source, "--width", 7, "--height", 5, "-o", "both.png")
        self.assert_output("both.png", (7, 5))

    def test_resize_invalid_arguments(self):
        for args in ([], ["--width", "0"], ["--height", "-2"], ["--width", "abc"],
                     ["--width", "1.5"], ["--width", "100000", "--height", "100000"],
                     ["--width", "9" * 500]):
            with self.subTest(args=args):
                self.run_cli("resize", self.source, *args, success=False)

    def test_crop_content_and_boundary(self):
        self.run_cli("crop", self.source, "--box", 1, 0, 4, 2, "-o", "crop.png")
        self.assert_output("crop.png", (3, 2))
        with Image.open(self.root / "crop.png") as image:
            self.assertEqual(image.getpixel((0, 0)), self.pixels[1])
            self.assertEqual(image.getpixel((2, 1)), self.pixels[7])
        self.run_cli("crop", self.source, "--box", 0, 0, 4, 3, "-o", "full.png")
        self.assert_output("full.png", (4, 3))

    def test_crop_invalid_regions(self):
        for box in ((-1, 0, 2, 2), (0, 0, 5, 3), (2, 0, 1, 2), (0, 0, 0, 2),
                    (0, 0, 4, 4), (0, 2, 2, 1)):
            with self.subTest(box=box):
                result = self.run_cli("crop", self.source, "--box", *box, success=False)
                self.assertIn("裁剪区域", result.stderr)

    def test_rotation_dimensions_and_pixels(self):
        # 逆时针旋转后，左上角分别来自原图右上、右下、左下。
        for degrees, size, pixel in ((90, (3, 4), self.pixels[3]),
                                     (180, (4, 3), self.pixels[11]),
                                     (270, (3, 4), self.pixels[8])):
            with self.subTest(degrees=degrees):
                output = f"rotate_{degrees}.png"
                self.run_cli("rotate", self.source, "--degrees", degrees, "-o", output)
                self.assert_output(output, size)
                with Image.open(self.root / output) as image:
                    self.assertEqual(image.getpixel((0, 0)), pixel)

    def test_flip_directions(self):
        for direction, pixel in (("horizontal", self.pixels[3]), ("vertical", self.pixels[8])):
            with self.subTest(direction=direction):
                output = f"{direction}.png"
                self.run_cli("flip", self.source, "--direction", direction, "-o", output)
                self.assert_output(output, (4, 3))
                with Image.open(self.root / output) as image:
                    self.assertEqual(image.getpixel((0, 0)), pixel)

    def test_grayscale(self):
        self.run_cli("gray", self.source, "-o", "gray.png")
        self.assert_output("gray.png", (4, 3), "L")
        with Image.open(self.root / "gray.png") as image:
            self.assertLess(image.getpixel((0, 0)), image.getpixel((3, 2)))

    def test_png_jpeg_roundtrip(self):
        self.run_cli("convert", self.source, "--format", "jpg", "-o", "out.JPG")
        self.assert_output("out.JPG", (4, 3), "RGB", "JPEG")
        self.run_cli("convert", "out.JPG", "--format", "png", "-o", "back.png")
        self.assert_output("back.png", (4, 3), "RGB", "PNG")

    def test_transparent_png_to_jpeg(self):
        path = self.root / "alpha.png"
        with Image.new("RGBA", (8, 8), (255, 0, 0, 0)) as image:
            image.save(path)
        self.run_cli("convert", path, "--format", "jpeg", "-o", "alpha.jpeg")
        self.assert_output("alpha.jpeg", (8, 8), "RGB", "JPEG")
        with Image.open(self.root / "alpha.jpeg") as image:
            self.assertEqual(image.getpixel((0, 0)), (255, 255, 255))

    def test_palette_transparency_to_jpeg(self):
        path = self.root / "palette.png"
        with Image.new("P", (8, 8), 0) as image:
            image.putpalette([255, 0, 0] + [0] * 765)
            image.save(path, transparency=0)
        self.run_cli("convert", path, "--format", "jpg", "-o", "palette.jpg")
        with Image.open(self.root / "palette.jpg") as image:
            self.assertEqual(image.getpixel((0, 0)), (255, 255, 255))

    def test_missing_file(self):
        result = self.run_cli("info", "missing.png", success=False)
        self.assertIn("不存在", result.stderr)

    def test_non_image_and_corrupt_image(self):
        for name, content in (("text.png", b"not an image"),
                              ("broken.png", self.source.read_bytes()[:45])):
            with self.subTest(name=name):
                (self.root / name).write_bytes(content)
                self.run_cli("info", name, success=False)

    def test_original_cannot_be_output(self):
        result = self.run_cli("gray", self.source, "-o", self.source, success=False)
        self.assertIn("原图", result.stderr)

    def test_existing_output_not_overwritten(self):
        target = self.root / "keep.png"
        target.write_bytes(b"keep me")
        result = self.run_cli("gray", self.source, "-o", target, success=False)
        self.assertIn("已存在", result.stderr)
        self.assertEqual(target.read_bytes(), b"keep me")

    def test_default_output_unique_names(self):
        self.run_cli("gray", self.source)
        first = self.root / "results" / "中文 示例_gray.png"
        first_bytes = first.read_bytes()
        self.run_cli("gray", self.source)
        self.assertTrue((self.root / "results" / "中文 示例_gray_1.png").is_file())
        self.assertEqual(first.read_bytes(), first_bytes)

    def test_output_subdirectory_created(self):
        self.run_cli("gray", self.source, "-o", "新的目录/结果.png")
        self.assert_output("新的目录/结果.png", (4, 3), "L")

    def test_invalid_format_extension_and_enums(self):
        for args in (("convert", "--format", "jpg", "-o", "bad.png"),
                     ("gray", "-o", "bad.gif"),
                     ("rotate", "--degrees", "45"),
                     ("flip", "--direction", "diagonal")):
            with self.subTest(args=args):
                self.run_cli(args[0], self.source, *args[1:], success=False)

    def test_help(self):
        result = self.run_cli("--help")
        for command in ("info", "resize", "crop", "rotate", "flip", "gray", "convert"):
            self.assertIn(command, result.stdout)


if __name__ == "__main__":
    unittest.main()
