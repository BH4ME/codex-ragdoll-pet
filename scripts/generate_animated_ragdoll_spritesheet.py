#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageOps


FRAME_W = 192
FRAME_H = 208
COLS = 8
ROWS = 9
SHEET_SIZE = (FRAME_W * COLS, FRAME_H * ROWS)


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("source image has no visible pixels")
    return bbox


def crop_subject(image: Image.Image) -> Image.Image:
    left, top, right, bottom = alpha_bbox(image)
    pad = 4
    return image.crop(
        (
            max(0, left - pad),
            max(0, top - pad),
            min(image.width, right + pad),
            min(image.height, bottom + pad),
        )
    )


def scale_subject(subject: Image.Image, scale: float) -> Image.Image:
    width = max(1, round(subject.width * scale))
    height = max(1, round(subject.height * scale))
    return subject.resize((width, height), Image.Resampling.LANCZOS)


def tint_alpha(subject: Image.Image, color: tuple[int, int, int], opacity: int) -> Image.Image:
    alpha = subject.getchannel("A")
    fill = Image.new("RGBA", subject.size, (*color, 0))
    fill.putalpha(alpha.point(lambda value: min(opacity, value)))
    return fill


def squash(subject: Image.Image, sx: float, sy: float) -> Image.Image:
    width = max(1, round(subject.width * sx))
    height = max(1, round(subject.height * sy))
    return subject.resize((width, height), Image.Resampling.BICUBIC)


def rotate(subject: Image.Image, degrees: float) -> Image.Image:
    return subject.rotate(degrees, resample=Image.Resampling.BICUBIC, expand=True)


def brightness(subject: Image.Image, factor: float) -> Image.Image:
    return ImageEnhance.Brightness(subject).enhance(factor)


def paste_centered(
    canvas: Image.Image,
    subject: Image.Image,
    center_x: float,
    baseline_y: float,
) -> None:
    x = round(center_x - subject.width / 2)
    y = round(baseline_y - subject.height)
    canvas.alpha_composite(subject, (x, y))


def draw_motion_lines(canvas: Image.Image, direction: str, amount: int) -> None:
    if amount <= 0:
        return
    draw = ImageDraw.Draw(canvas)
    color = (180, 150, 118, 70)
    if direction == "right":
        for idx in range(3):
            y = 72 + idx * 24
            draw.line((20, y, 54 + amount, y - 8), fill=color, width=3)
    elif direction == "left":
        for idx in range(3):
            y = 72 + idx * 24
            draw.line((172, y, 138 - amount, y - 8), fill=color, width=3)


def make_frame(
    source: Image.Image,
    *,
    phase: float,
    x: float = 96,
    baseline: float = 184,
    scale: float = 1.0,
    sx: float = 1.0,
    sy: float = 1.0,
    angle: float = 0.0,
    flip: bool = False,
    shade: float = 1.0,
    ghost: tuple[float, str] | None = None,
    paw: bool = False,
    sleep: bool = False,
    spark: bool = False,
) -> Image.Image:
    canvas = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    subject = source
    if flip:
        subject = ImageOps.mirror(subject)
    subject = scale_subject(subject, scale)
    subject = squash(subject, sx, sy)
    if angle:
        subject = rotate(subject, angle)
    if shade != 1.0:
        subject = brightness(subject, shade)

    bob = math.sin(phase * math.tau) * 3
    sway = math.sin(phase * math.tau) * 3

    if ghost:
        offset, direction = ghost
        ghost_subject = tint_alpha(subject, (120, 95, 82), 48)
        ghost_x = x - offset if direction == "right" else x + offset
        paste_centered(canvas, ghost_subject, ghost_x, baseline + 2)
        draw_motion_lines(canvas, direction, round(offset))

    paste_centered(canvas, subject, x + sway, baseline + bob)
    draw = ImageDraw.Draw(canvas)

    if paw:
        paw_x = x + 34 * (-1 if flip else 1) + math.sin(phase * math.tau) * 4
        paw_y = baseline - 72 + math.cos(phase * math.tau) * 10
        draw.ellipse((paw_x - 7, paw_y - 7, paw_x + 9, paw_y + 9), fill=(74, 45, 33, 215))
        draw.arc((paw_x + 8, paw_y - 18, paw_x + 32, paw_y + 10), 190, 300, fill=(111, 75, 54, 150), width=3)

    if sleep:
        z_x = x + 48
        z_y = baseline - 134 - 8 * math.sin(phase * math.tau)
        draw.text((z_x, z_y), "Z", fill=(80, 90, 120, 180))

    if spark:
        cx = x + 48 * (-1 if flip else 1)
        cy = baseline - 132 + math.sin(phase * math.tau) * 5
        draw.line((cx - 6, cy, cx + 6, cy), fill=(90, 160, 240, 170), width=2)
        draw.line((cx, cy - 6, cx, cy + 6), fill=(90, 160, 240, 170), width=2)

    return canvas


def row_frames(source: Image.Image, row: int) -> list[Image.Image]:
    frames: list[Image.Image] = []
    for col in range(COLS):
        phase = col / COLS
        wave = math.sin(phase * math.tau)
        if row == 0:  # idle breathing
            frame = make_frame(source, phase=phase, scale=1.0, sx=1.0 + wave * 0.012, sy=1.0 - wave * 0.012)
        elif row == 1:  # running right
            frame = make_frame(
                source,
                phase=phase,
                x=88 + col * 3,
                scale=0.98,
                sx=1.05,
                sy=0.95,
                angle=wave * 5,
                ghost=(16, "right"),
            )
        elif row == 2:  # running left
            frame = make_frame(
                source,
                phase=phase,
                x=104 - col * 3,
                scale=0.98,
                sx=1.05,
                sy=0.95,
                angle=-wave * 5,
                flip=True,
                ghost=(16, "left"),
            )
        elif row == 3:  # waving
            frame = make_frame(source, phase=phase, scale=1.0, angle=wave * 2, paw=True)
        elif row == 4:  # jumping
            jump = abs(math.sin(phase * math.tau))
            frame = make_frame(
                source,
                phase=phase,
                baseline=184 - jump * 36,
                scale=1.0,
                sx=1.0 - jump * 0.05,
                sy=1.0 + jump * 0.06,
                angle=wave * 5,
            )
        elif row == 5:  # failed
            frame = make_frame(
                source,
                phase=phase,
                baseline=188 + abs(wave) * 5,
                scale=1.0,
                sx=1.08,
                sy=0.9,
                angle=wave * 8,
                shade=0.88,
            )
        elif row == 6:  # waiting
            frame = make_frame(source, phase=phase, scale=1.0, baseline=184 + abs(wave) * 3, sleep=True)
        elif row == 7:  # running / active
            frame = make_frame(
                source,
                phase=phase,
                x=96 + wave * 8,
                scale=0.98,
                sx=1.04,
                sy=0.96,
                angle=wave * 6,
                ghost=(10, "right" if col % 2 == 0 else "left"),
            )
        else:  # review
            frame = make_frame(source, phase=phase, scale=1.0, angle=wave * 3, spark=True)
        frames.append(frame)
    return frames


def generate(source_path: Path, out_path: Path) -> None:
    source = crop_subject(Image.open(source_path).convert("RGBA"))
    sheet = Image.new("RGBA", SHEET_SIZE, (0, 0, 0, 0))
    for row in range(ROWS):
        for col, frame in enumerate(row_frames(source, row)):
            sheet.alpha_composite(frame, (col * FRAME_W, row * FRAME_H))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def main() -> int:
    generate(Path("assets/ragdoll-preview.png"), Path("pet/ragdoll-cat/spritesheet.png"))
    generate(Path("assets/ragdoll-preview.png"), Path("output/animated-ragdoll-spritesheet.png"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
