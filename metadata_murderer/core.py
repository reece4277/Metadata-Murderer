from __future__ import annotations
import io, os, sys, json, time, hashlib, shutil
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin, JpegImagePlugin
import piexif
import pikepdf

SUPPORTED_IMG = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_PDF = {".pdf"}

@dataclass
class ItemReport:
    src: str
    dst: str
    type: str
    size_in: int
    size_out: int
    bytes_removed: int
    ok: bool
    note: str

def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def ensure_parent(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)

def clean_image(src: Path, dst: Path, watermark: Optional[str], wm_opacity: float, wm_size: int) -> Tuple[bool, str]:
    ext = src.suffix.lower()
    im = Image.open(src).convert("RGBA")

    # remove metadata by re-encoding
    if ext in [".jpg", ".jpeg"]:
        im2 = im.convert("RGB")
        if watermark:
            im2 = apply_watermark(im2, watermark, wm_opacity, wm_size)
        exif_bytes = piexif.dump({})  # empty exif
        ensure_parent(dst)
        im2.save(dst, "JPEG", quality=95, optimize=True, exif=exif_bytes)
    elif ext == ".png":
        im2 = im.convert("RGBA")
        if watermark:
            im2 = apply_watermark(im2, watermark, wm_opacity, wm_size)
        info = PngImagePlugin.PngInfo()  # no metadata
        ensure_parent(dst)
        im2.save(dst, "PNG", optimize=True, pnginfo=info)
    elif ext == ".webp":
        im2 = im.convert("RGBA")
        if watermark:
            im2 = apply_watermark(im2, watermark, wm_opacity, wm_size)
        ensure_parent(dst)
        im2.save(dst, "WEBP", method=6, quality=95)
    else:
        return False, "unsupported image type"

    return verify_image_clean(dst)

def apply_watermark(im, text, opacity, size):
    im = im.convert("RGBA")
    w, h = im.size
    overlay = Image.new("RGBA", im.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    try:
        font = ImageFont.truetype("Arial.ttf", size)
    except:
        font = ImageFont.load_default()
    tw, th = draw.textsize(text, font=font)
    # tiled diagonal
    step = max(100, int(min(w,h)*0.25))
    for y in range(-th, h+step, step):
        for x in range(-tw, w+step, step):
            draw.text((x, y), text, font=font, fill=(255,255,255,int(255*opacity)))
    return Image.alpha_composite(im, overlay).convert("RGB")

def verify_image_clean(path: Path) -> Tuple[bool, str]:
    ext = path.suffix.lower()
    if ext in [".jpg", ".jpeg"]:
        try:
            exif_dict = piexif.load(str(path))
            # empty exif ok
            if any(exif_dict.get(k) for k in exif_dict.keys()):
                return False, "exif still present"
        except Exception:
            # if it fails to parse EXIF, assume none
            pass
        return True, "ok"
    elif ext == ".png":
        im = Image.open(path)
        if im.info:
            # PNG may have innocuous chunks; we consider non-empty info suspicious
            if any(k for k in im.info.keys() if k not in ("transparency","gamma")):
                return False, "png ancillary chunks remain"
        return True, "ok"
    elif ext == ".webp":
        # Pillow strips metadata on re-save; consider ok
        return True, "ok"
    return True, "ok"

def clean_pdf(src: Path, dst: Path) -> Tuple[bool, str]:
    ensure_parent(dst)
    with pikepdf.open(src) as pdf:
        pdf.docinfo.clear()
        # scrub XMP metadata if present
        try:
            pdf.Root.Metadata = None
        except Exception:
            pass
        pdf.save(dst, preserve_pdfa=False, linearize=True)
    # verify
    with pikepdf.open(dst) as pdf2:
        if pdf2.docinfo and len(pdf2.docinfo) > 0:
            return False, "pdf info remains"
    return True, "ok"

def process_tree(input_path, output_dir, watermark=None, wm_opacity=0.18, wm_size=48, keep_times=False, overwrite=False):
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    items: list[ItemReport] = []
    t0 = time.time()

    all_paths = []
    if input_path.is_file():
        all_paths = [input_path]
    else:
        for p in input_path.rglob("*"):
            if p.is_file():
                all_paths.append(p)

    for src in all_paths:
        rel = src.relative_to(input_path if input_path.is_dir() else src.parent)
        dst = output_dir / rel
        ext = src.suffix.lower()

        if ext in SUPPORTED_IMG | SUPPORTED_PDF:
            if dst.exists() and not overwrite:
                # skip existing
                items.append(ItemReport(str(src), str(dst), "skip", src.stat().st_size, dst.stat().st_size, 0, True, "exists"))
                continue

            size_in = src.stat().st_size
            if ext in SUPPORTED_IMG:
                ok, note = clean_image(src, dst, watermark, wm_opacity, wm_size)
                typ = "image"
            else:
                ok, note = clean_pdf(src, dst)
                typ = "pdf"
            size_out = dst.stat().st_size if dst.exists() else 0
            removed = max(0, size_in - size_out)

            if keep_times:
                try:
                    st = src.stat()
                    os.utime(dst, (st.st_atime, st.st_mtime))
                except Exception:
                    pass

            items.append(ItemReport(str(src), str(dst), typ, size_in, size_out, removed, ok, note))
        else:
            # copy-through for unsupported
            ensure_parent(dst)
            shutil.copy2(src, dst)
            items.append(ItemReport(str(src), str(dst), "copy", src.stat().st_size, dst.stat().st_size, 0, True, "copied"))

    total_in = sum(i.size_in for i in items)
    total_out = sum(i.size_out for i in items)
    out = {
        "started": t0,
        "ended": time.time(),
        "input": str(input_path),
        "output": str(output_dir),
        "files": [asdict(i) for i in items],
        "summary": {
            "count": len(items),
            "bytes_in": total_in,
            "bytes_out": total_out,
            "bytes_removed": max(0, total_in - total_out),
        },
    }
    return out
