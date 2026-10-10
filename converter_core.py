"""Convert each image subfolder to a separate PDF."""

from __future__ import annotations

import errno
import os
import re
import shutil
import tempfile
import threading
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import img2pdf
from PIL import Image, ImageOps

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}
NATIVE = {".jpg", ".jpeg", ".png"}
COMPRESS_PRESETS = {
    "None": (None, None),
    "Low": (85, 3000),
    "Medium": (65, 2000),
    "High": (40, 1200),
}


@dataclass(frozen=True)
class ConversionResult:
    status: str
    folder_name: str
    output_name: str = ""
    page_count: int = 0
    skipped_images: int = 0
    detail: str = ""


def natural_sort_key(name: str):
    parts = re.split(r"(\d+)", Path(name).stem.casefold())
    return tuple((1, int(p)) if p.isdecimal() else (0, p) for p in parts), name.casefold()


def clean_filename(name: str) -> str:
    normalized = unicodedata.normalize("NFKC", name)
    cleaned = "".join(c for c in normalized if c.isalnum() or c in " ._-()[]")
    return cleaned.strip(" .")[:100].rstrip(" .") or "folder"


def list_subfolders(input_path: str) -> list[str]:
    with os.scandir(input_path) as entries:
        folders = [e.path for e in entries
                   if not e.name.startswith(".") and e.is_dir(follow_symlinks=False)]
    return sorted(folders, key=lambda p: natural_sort_key(os.path.basename(p)))


def get_images(folder_path: str) -> list[str]:
    with os.scandir(folder_path) as entries:
        images = [e.path for e in entries
                  if not e.name.startswith(".")
                  and Path(e.name).suffix.lower() in SUPPORTED
                  and e.is_file(follow_symlinks=False)]
    return sorted(images, key=lambda p: natural_sort_key(os.path.basename(p)))


def _readable_image(path: str) -> bool:
    try:
        with Image.open(path) as image:
            image.verify()
        return True
    except (OSError, ValueError, SyntaxError):
        return False


def _flatten_rgb(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    if image.mode in ("RGBA", "LA") or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")


def _prepare_image(source: str, destination: str, quality: int | None, max_res: int | None):
    with Image.open(source) as original:
        if quality is None:
            ImageOps.exif_transpose(original).save(destination, "PNG")
            return
        image = _flatten_rgb(original)
        if max_res and max(image.size) > max_res:
            image.thumbnail((max_res, max_res), Image.Resampling.LANCZOS)
        image.save(destination, "JPEG", quality=quality, optimize=True)


def _publish_pdf(temp_path: str, output_dir: str, folder_name: str) -> str:
    base = clean_filename(folder_name)
    for number in range(1, 10001):
        name = f"{base}.pdf" if number == 1 else f"{base} ({number}).pdf"
        try:
            os.link(temp_path, os.path.join(output_dir, name))
            return name
        except FileExistsError:
            continue
    raise OSError(errno.EEXIST, "Too many PDFs with the same name")


def convert_folder(folder_path: str, output_dir: str, preset: str,
                   cancel_event: threading.Event) -> ConversionResult:
    folder_name = os.path.basename(os.path.normpath(folder_path))
    if cancel_event.is_set():
        return ConversionResult("cancelled", folder_name)
    if preset not in COMPRESS_PRESETS:
        return ConversionResult("failed", folder_name, detail="Unknown compression preset")

    temp_pdf = None
    temp_dir = None
    try:
        images = get_images(folder_path)
        if not images:
            return ConversionResult("skipped", folder_name, detail="no images")
        valid = [p for p in images if _readable_image(p)]
        if not valid:
            return ConversionResult("skipped", folder_name, detail="no readable images")
        quality, max_res = COMPRESS_PRESETS[preset]
        sources = []
        for index, path in enumerate(valid):
            if cancel_event.is_set():
                return ConversionResult("cancelled", folder_name)
            if quality is None and Path(path).suffix.lower() in NATIVE:
                sources.append(path)
                continue
            if temp_dir is None:
                temp_dir = tempfile.mkdtemp(prefix="pdf-batch-images-")
            suffix = "png" if quality is None else "jpg"
            destination = os.path.join(temp_dir, f"{index:06d}.{suffix}")
            _prepare_image(path, destination, quality, max_res)
            sources.append(destination)

        if cancel_event.is_set():
            return ConversionResult("cancelled", folder_name)
        with tempfile.NamedTemporaryFile(mode="w+b", suffix=".pdf", prefix=".pdf-batch-",
                                         dir=output_dir, delete=False) as handle:
            temp_pdf = handle.name
            img2pdf.convert(sources, outputstream=handle)
        if cancel_event.is_set():
            return ConversionResult("cancelled", folder_name)
        output_name = _publish_pdf(temp_pdf, output_dir, folder_name)
        return ConversionResult("ok", folder_name, output_name, len(valid), len(images) - len(valid))
    except OSError as exc:
        detail = "disk full" if exc.errno == errno.ENOSPC else str(exc)
        return ConversionResult("failed", folder_name, detail=detail)
    except Exception as exc:
        return ConversionResult("failed", folder_name, detail=str(exc))
    finally:
        if temp_pdf:
            try:
                os.unlink(temp_pdf)
            except FileNotFoundError:
                pass
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
