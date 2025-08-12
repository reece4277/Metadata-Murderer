# Metadata Murderer

No explanations. Just run it.

## Install
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Use
```bash
# clean everything in a folder to ./clean
mdm run --input ./samples --out ./clean

# add a watermark
mdm run --input ./samples --out ./clean --watermark "KING" --wm-opacity 0.18
```
