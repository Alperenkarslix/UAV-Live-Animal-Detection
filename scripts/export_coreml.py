#!/usr/bin/env python
"""Export Ultralytics YOLO weights to a CoreML .mlpackage.

Usage:
    uv run python scripts/export_coreml.py [model_path]

Defaults to the fine-tuned safari weights. Output is written next to the
input weights (e.g. `best.pt` → `best.mlpackage`). Apple Neural Engine
delivers the best latency on M-series Macs; PyTorch MPS is the fallback.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Export YOLO weights to CoreML.")
    parser.add_argument(
        "model",
        nargs="?",
        default="yolomodel/yolo26_animals/weights/best.pt",
        help="Path to .pt weights",
    )
    parser.add_argument("--imgsz", type=int, default=640, help="Inference image size")
    parser.add_argument("--half", action="store_true", help="FP16 (smaller, faster)")
    parser.add_argument(
        "--int8",
        action="store_true",
        help="INT8 quantisation (smaller still, slight accuracy hit)",
    )
    parser.add_argument("--no-nms", dest="nms", action="store_false", help="Disable embedded NMS")
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.is_file():
        print(f"error: {model_path} not found", file=sys.stderr)
        return 1

    if sys.platform != "darwin":
        print("warn: CoreML export is only useful on macOS — continuing anyway")

    from ultralytics import YOLO

    print(f"[export] loading {model_path}")
    model = YOLO(str(model_path))

    print(
        f"[export] CoreML export imgsz={args.imgsz} half={args.half} "
        f"int8={args.int8} nms={args.nms}"
    )
    t0 = time.perf_counter()
    out = model.export(
        format="coreml",
        imgsz=args.imgsz,
        half=args.half,
        int8=args.int8,
        nms=args.nms,
    )
    dt = time.perf_counter() - t0
    print(f"[export] done in {dt:.1f}s → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
