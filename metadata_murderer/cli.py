import argparse, os, sys, json, hashlib, shutil, datetime
from pathlib import Path
from .core import process_tree

def app():
    p = argparse.ArgumentParser(prog="mdm")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run")
    r.add_argument("--input", required=True, help="file or folder")
    r.add_argument("--out", required=True, help="output folder")
    r.add_argument("--watermark", default=None, help="text watermark")
    r.add_argument("--wm-opacity", type=float, default=0.18)
    r.add_argument("--wm-size", type=int, default=48)
    r.add_argument("--keep-times", action="store_true", help="preserve mtime/atime")
    r.add_argument("--overwrite", action="store_true")
    args = p.parse_args()

    inp = Path(args.input).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    report = process_tree(
        inp,
        out,
        watermark=args.watermark,
        wm_opacity=args.wm_opacity,
        wm_size=args.wm_size,
        keep_times=args.keep_times,
        overwrite=args.overwrite,
    )
    rep_path = out / "mdm-report.json"
    rep_path.write_text(json.dumps(report, indent=2))
    print(f"Done. Report: {rep_path}")
