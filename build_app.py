"""Create the macOS app bundle with a generated icon."""

from pathlib import Path
import os

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
os.environ["PYINSTALLER_CONFIG_DIR"] = str(ROOT / "build" / "cache")

from PyInstaller.__main__ import run


def make_icon(destination: Path) -> None:
    size = 1024
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((56, 56, 968, 968), radius=218, fill="#2467D9")
    draw.rounded_rectangle((116, 116, 908, 908), radius=172, fill="#438BFC")
    draw.rounded_rectangle((254, 177, 771, 855), radius=56, fill="#E8F1FF")
    draw.polygon([(633, 177), (771, 315), (633, 315)], fill="#B8D3FF")
    draw.polygon([(633, 177), (633, 315), (771, 315)], outline="#92BAF5", width=6)
    draw.rounded_rectangle((328, 418, 697, 465), radius=20, fill="#2467D9")
    draw.rounded_rectangle((328, 516, 697, 563), radius=20, fill="#2467D9")
    draw.rounded_rectangle((328, 614, 588, 661), radius=20, fill="#2467D9")

    ASSETS.mkdir(exist_ok=True)
    image.save(ASSETS / "app_icon.png", format="PNG")
    image.save(destination, format="ICNS")


if __name__ == "__main__":
    build = ROOT / "build"
    build.mkdir(exist_ok=True)
    icon = build / "AppIcon.icns"
    make_icon(icon)
    run([
        str(ROOT / "pdfconverter.py"),
        "--name=PDF Batch Converter",
        "--windowed",
        "--onedir",
        "--osx-bundle-identifier=io.github.jordanalfarishy.pdfbatchconverter",
        f"--icon={icon}",
        f"--distpath={ROOT / 'dist'}",
        f"--workpath={build / 'pyinstaller'}",
        f"--specpath={build}",
        "--noconfirm",
        "--clean",
    ])
