#!/usr/bin/env python
"""Benchmark inference latency on a video file.

Usage:
    uv run python scripts/benchmark.py [video] [--frames N] [--device mps|cpu|coreml]

Reports mean / p50 / p95 / p99 ms-per-frame and effective FPS. Useful for
comparing CoreML (.mlpackage) vs PyTorch MPS vs CPU on the same Mac.
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

import cv2

from uav.core.config import get_settings


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="YOLO inference benchmark")
    parser.add_argument("video", nargs="?", default=settings.video_path)
    parser.add_argument("--model", default=settings.model_path)
    parser.add_argument("--imgsz", type=int, default=settings.img_size)
    parser.add_argument("--conf", type=float, default=settings.confidence)
    parser.add_argument("--device", default=settings.device or "")
    parser.add_argument("--frames", type=int, default=200, help="Frames to time")
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument(
        "--track",
        action="store_true",
        help="Use ByteTrack (model.track) instead of plain inference",
    )
    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.is_file():
        print(f"error: video not found: {video_path}", file=sys.stderr)
        return 1

    from ultralytics import YOLO

    print(f"[bench] loading {args.model}")
    model = YOLO(args.model)
    if args.device:
        try:
            model.to(args.device)
        except Exception as exc:
            print(f"[bench] could not move model to {args.device}: {exc}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"error: cannot open video: {video_path}", file=sys.stderr)
        return 1

    timings: list[float] = []
    frame_count = 0

    print(
        f"[bench] warmup={args.warmup} measured={args.frames} imgsz={args.imgsz} conf={args.conf}"
    )
    while frame_count < args.warmup + args.frames:
        ok, frame = cap.read()
        if not ok:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = cap.read()
            if not ok:
                break

        t0 = time.perf_counter()
        if args.track:
            model.track(frame, conf=args.conf, imgsz=args.imgsz, persist=True, verbose=False)
        else:
            model(frame, conf=args.conf, imgsz=args.imgsz, verbose=False)
        dt = (time.perf_counter() - t0) * 1000.0

        if frame_count >= args.warmup:
            timings.append(dt)
        frame_count += 1

    cap.release()

    if not timings:
        print("error: no frames processed", file=sys.stderr)
        return 1

    timings_sorted = sorted(timings)
    p50 = statistics.median(timings_sorted)
    p95 = timings_sorted[int(len(timings_sorted) * 0.95)]
    p99 = timings_sorted[int(len(timings_sorted) * 0.99)]
    mean = statistics.fmean(timings)
    fps = 1000.0 / mean

    print()
    print(f"  frames measured : {len(timings)}")
    print(f"  mean           : {mean:7.2f} ms")
    print(f"  p50            : {p50:7.2f} ms")
    print(f"  p95            : {p95:7.2f} ms")
    print(f"  p99            : {p99:7.2f} ms")
    print(f"  effective FPS  : {fps:7.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
