import os, json, io
from pathlib import Path
from PIL import Image
import piexif
from metadata_murderer.core import process_tree

def make_jpeg_with_exif(path: Path):
    im = Image.new("RGB", (64,64), color=(120,20,200))
    exif_dict = {"0th": {piexif.ImageIFD.Make: u"DramaCam"}}
    exif_bytes = piexif.dump(exif_dict)
    im.save(path, "JPEG", exif=exif_bytes)

def test_strip_jpeg(tmp_path: Path):
    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir()
    out.mkdir()
    f = src / "test.jpg"
    make_jpeg_with_exif(f)
    rep = process_tree(src, out, watermark="KING", wm_opacity=0.1)
    clean = out / "test.jpg"
    assert clean.exists()
    data = json.loads((out / "mdm-report.json").read_text()) if (out / "mdm-report.json").exists() else rep
    assert data["summary"]["count"] >= 1

def test_copy_other(tmp_path: Path):
    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir(); out.mkdir()
    other = src / "note.txt"
    other.write_text("hello")
    rep = process_tree(src, out)
    assert (out/ "note.txt").exists()
