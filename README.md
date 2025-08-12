# Metadata Murderer

**You ready to vanish your drip?**
This tool *obliterates EXIF and metadata from your images & PDFs* and optionally watermarks with sass. No finger-pointing, no explanations—just chaos. 🙅‍♀️

---

## Quickshit setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

---

## Use It Down

**Strip everything from `./samples` into `./clean`**
```bash
mdm run --input ./samples --out ./clean
```

**Add a watermark (optional)**
```bash
mdm run \
  --input ./samples \
  --out ./clean \
  --watermark "KING" \
  --wm-opacity 0.18
```

---

## Why? Because I said so.

- **No spying**—It’s offline and only touches files you own.  
- **No apologies**—All the metadata is gone. You’re untraceable.  
- **No mercy**—The watermark option isn’t subtle. Own it.

---

## Want more flavor?

- Drop a `samples/` folder with your own pics so the showcase isn’t dead content.  
- Add badges for PyPI, CI status, etc. If it’s working, flex it.  
- Need a drag-and-drop UI or desktop app next? Say the word, and I’ll dress it up in satin—

---

*No lawyering here: this tool is for personal use only. I am not responsible for any misuse. Play hard, not illegal.*
