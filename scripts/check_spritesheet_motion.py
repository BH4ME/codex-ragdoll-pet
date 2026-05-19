#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


EXPECTED_SIZE = (1536, 1872)
GRID = (8, 9)
FRAME_SIZE = (192, 208)


def visible_mean_luma(image: Image.Image, box: tuple[int, int, int, int]) -> float:
    region = image.crop(box).convert("RGBA")
    pixels = [pixel for pixel in region.getdata() if pixel[3] > 80]
    if not pixels:
        raise ValueError(f"no visible pixels in region {box}")
    return sum(0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b, _ in pixels) / len(pixels)


def frame_difference(a: Image.Image, b: Image.Image) -> float:
    diff = ImageChops.difference(a, b)
    stat = ImageStat.Stat(diff)
    return sum(stat.mean) / len(stat.mean)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spritesheet", nargs="?", default="pet/ragdoll-cat/spritesheet.png")
    parser.add_argument("--min-row-diff", type=float, default=0.2)
    parser.add_argument("--min-moving-rows", type=int, default=7)
    args = parser.parse_args()

    path = Path(args.spritesheet)
    image = Image.open(path).convert("RGBA")
    if image.size != EXPECTED_SIZE:
        raise SystemExit(f"expected {EXPECTED_SIZE}, got {image.size}")

    frame_w = image.width // GRID[0]
    frame_h = image.height // GRID[1]
    moving_rows = 0
    row_scores: list[float] = []

    for row in range(GRID[1]):
        frames = [
            image.crop((col * frame_w, row * frame_h, (col + 1) * frame_w, (row + 1) * frame_h))
            for col in range(GRID[0])
        ]
        score = max(frame_difference(frames[col], frames[col + 1]) for col in range(GRID[0] - 1))
        row_scores.append(score)
        if score >= args.min_row_diff:
            moving_rows += 1

    print("row max diffs:", " ".join(f"{score:.3f}" for score in row_scores))
    if moving_rows < args.min_moving_rows:
        raise SystemExit(
            f"not enough animated rows: {moving_rows}/{GRID[1]} "
            f"(need at least {args.min_moving_rows})"
        )

    first_frame = image.crop((0, 0, FRAME_SIZE[0], FRAME_SIZE[1]))
    viewer_left_face = visible_mean_luma(first_frame, (58, 66, 88, 112))
    viewer_right_face = visible_mean_luma(first_frame, (104, 66, 140, 116))
    print(
        "face luma:",
        f"viewer-left={viewer_left_face:.1f}",
        f"viewer-right={viewer_right_face:.1f}",
    )
    if viewer_right_face > viewer_left_face - 18:
        raise SystemExit(
            "reference-style face check failed: viewer-right face patch should be visibly darker "
            "than viewer-left face"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
