# Python 图片处理工具

这是一个中文命令行图片处理程序，使用 Python 和 Pillow 实现图片信息读取、缩放、裁剪、旋转、翻转、灰度化及 PNG/JPG 格式转换。编辑结果保存为新文件，并显示完整保存路径。

## 环境要求和安装

需要 Python 3.10 或更新版本。开发与测试环境为 Windows、Python 3.14.7、Pillow 12.3.0。依赖版本固定在 `requirements.txt` 中。

先打开 PowerShell，进入包含本 README 的项目目录，再执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

下面直接调用虚拟环境中的 Python，无需激活环境。Linux/macOS 将 `.\.venv\Scripts\python.exe` 替换为 `./.venv/bin/python`。

## 启动和查看帮助

```powershell
.\.venv\Scripts\python.exe image_tool.py --help
.\.venv\Scripts\python.exe image_tool.py resize --help
```

总帮助会列出 `info`、`resize`、`crop`、`rotate`、`flip`、`gray`、`convert` 七个子命令。

仓库附带两张由 `make_examples.py` 生成的小图片：`examples/demo.png`（640×480、RGB）和 `examples/transparent.png`（320×240、RGBA）。如图片缺失，可运行：

```powershell
.\.venv\Scripts\python.exe make_examples.py
```

## 读取图片信息

```powershell
.\.venv\Scripts\python.exe image_tool.py info examples/demo.png
```

预期输出如下，文件大小取决于图片的实际字节数：

```text
文件名：demo.png
图片格式：PNG
宽度：640 像素
高度：480 像素
颜色模式：RGB
文件大小：5.35 KB
```

程序根据实际文件内容识别图片格式。颜色模式可能显示 RGB、RGBA、L（灰度）、P（调色板）等。文件达到 1 MB 时显示 MB，大小始终保留两位小数。

## 缩放

```powershell
# 只指定宽度，按比例得到 320×240。
.\.venv\Scripts\python.exe image_tool.py resize examples/demo.png --width 320
# 只指定高度，按比例得到 160×120。
.\.venv\Scripts\python.exe image_tool.py resize examples/demo.png --height 120
# 同时指定宽高，得到 300×200，可能改变比例。
.\.venv\Scripts\python.exe image_tool.py resize examples/demo.png --width 300 --height 200
```

成功时输出处理后的宽高和保存位置。宽高必须为正整数，至少提供其中一个。按比例计算后的像素数取整，最小为 1；缩放结果上限为 4000 万像素。

## 裁剪

```powershell
.\.venv\Scripts\python.exe image_tool.py crop examples/demo.png --box 30 30 300 220
```

预期得到 270×190 的图片，并显示保存位置。四个坐标依次为左、上、右、下。原点位于左上角，右边界、下边界不包含在结果中，因此宽度为“右−左”，高度为“下−上”。

要求 `0 ≤ 左 < 右 ≤ 图片宽度`，`0 ≤ 上 < 下 ≤ 图片高度`。以下命令超出示例图边界，预期显示“裁剪区域不合法或越界”，且不保存结果：

```powershell
.\.venv\Scripts\python.exe image_tool.py crop examples/demo.png --box 0 0 999 999
```

## 旋转

```powershell
.\.venv\Scripts\python.exe image_tool.py rotate examples/demo.png --degrees 90
.\.venv\Scripts\python.exe image_tool.py rotate examples/demo.png --degrees 180
.\.venv\Scripts\python.exe image_tool.py rotate examples/demo.png --degrees 270
```

方向为逆时针。90°和270°的结果为 480×640，180°的结果为 640×480。图像完整保留，输出保存位置。

## 翻转

```powershell
# 水平翻转：左右交换。
.\.venv\Scripts\python.exe image_tool.py flip examples/demo.png --direction horizontal
# 垂直翻转：上下交换。
.\.venv\Scripts\python.exe image_tool.py flip examples/demo.png --direction vertical
```

预期得到 640×480 的图片，并显示保存位置。

## 灰度化

```powershell
.\.venv\Scripts\python.exe image_tool.py gray examples/demo.png
.\.venv\Scripts\python.exe image_tool.py info results/demo_gray.png
```

第一条命令生成 640×480 的灰度图；第二条查看结果，颜色模式为 `L（灰度）`。灰度化会移除透明通道。

## 格式转换

```powershell
# 透明 PNG 转 JPG。
.\.venv\Scripts\python.exe image_tool.py convert examples/transparent.png --format jpg
# 将上一步的 JPG 转回 PNG。
.\.venv\Scripts\python.exe image_tool.py convert results/transparent_convert.jpg --format png
```

第一条生成 `results/transparent_convert.jpg`（320×240、JPEG、RGB），第二条生成 `results/transparent_convert_convert.png`（320×240、PNG、RGB）。

JPEG 无法保留透明通道，程序先将透明图像合成到白色背景，再转换为 RGB 保存。由此生成的 JPG 再转为 PNG，也不会恢复原来的透明度。JPG 是有损格式，像素颜色可能有轻微变化。

## 保存路径与同名文件保护

默认在当前工作目录的 `results` 文件夹保存结果。通常使用 PNG，`convert` 则使用指定格式。默认命名为“原文件名_操作名.扩展名”；重复运行会添加 `_1`、`_2` 等编号。

所有编辑命令都支持 `-o` 或 `--output` 指定新路径：

```powershell
.\.venv\Scripts\python.exe image_tool.py resize examples/demo.png --width 320 -o "results/my_small.png"
```

预期生成 320×240 图片，并显示 `results/my_small.png` 的绝对路径。新目录会自动创建。指定的文件若已存在，程序明确提示并退出，不覆盖原图或已有结果。再次尝试时请更换输出文件名。

仅支持输出 `.png`、`.jpg`、`.jpeg`。`convert` 的输出扩展名必须与 `--format` 一致；其他编辑命令由输出扩展名决定保存格式，默认 PNG。上述固定文件名示例以首次运行时为准；重复运行后请使用程序实际显示的路径。

输入可为 Pillow 能解码的常见图片，例如 PNG、JPEG、BMP。对于 GIF、TIFF 等多帧图片只处理第一帧，不处理动画；不保证保留原图的 EXIF 等元数据，也不会自动按 EXIF 方向旋转。

## 错误处理与测试

文件不存在、内容不是有效图片、损坏图片、裁剪越界、非法宽高、非法旋转角度、输出格式不匹配、文件权限等错误会显示提示。成功退出码为 0，处理错误为 1，命令参数错误为 2。超大输入图片使用 Pillow 的安全检查拒绝处理。

可亲手尝试：

```powershell
.\.venv\Scripts\python.exe image_tool.py info missing.png
.\.venv\Scripts\python.exe image_tool.py resize examples/demo.png --width 0
```

预期分别提示文件不存在、宽高必须大于 0，不出现 Python 异常堆栈。

运行自动测试：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

包含 21 项测试方法及多组参数用例，覆盖编辑后的尺寸与像素位置、等比例缩放、透明图转换、无效输入、中文路径、原图保护和同名文件保护。通过时最后显示 `Ran 21 tests` 和 `OK`。测试只使用临时目录，不改动用户图片。

## 文件结构与代码阅读

```text
image_tool/
├── image_tool.py       主程序
├── make_examples.py    示例图片生成脚本
├── examples/           小型示例图片
├── tests/              自动测试
├── requirements.txt    依赖与版本
├── .gitignore          排除虚拟环境、缓存和结果
└── README.md           使用说明
```

阅读代码建议从 `main()` 开始：解析命令 → `load_image()` 读取 → `image_info()` 展示信息或 `edit_image()` 选择编辑函数 → `save_result()` 保存新文件。`resize_image()`、`crop_image()`、`rotate_image()`、`flip_image()`、`grayscale_image()` 各自负责一项操作。

图像坐标和像素数由 Python 计算，像素变换由 Pillow 完成。本作业推荐 OpenCV 但未强制，因此本项目选择 Pillow；依赖使用 venv 和 pip 管理。

## Git 与 Agent 开发记录

项目初始化在 main，功能开发及验证在 dev，最终将 dev 合并到 main。可以查看实际历史：

```powershell
git branch
git log --graph --oneline --all
git status
```

各次提交分别对应初始化、图片信息、缩放裁剪、其余编辑、测试及说明完善。`.gitignore` 排除 `.venv`、`__pycache__`、`results` 和 `my_images` 等目录；个人练习图片可放入 `my_images`，仓库仅保留小型演示素材。

本项目由使用者提出作业要求，Agent 协助需求拆解、编码、调试、测试和文档编写。运行验证及代码理解仍需使用者亲自完成。作业需要的 Agent 记录应使用真实对话截图或完整会话导出；本 README 不能代替这些附件。

## 参考文档

- [Pillow 图像接口](https://pillow.readthedocs.io/en/stable/reference/Image.html)
- [Pillow 图片格式说明](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html)
