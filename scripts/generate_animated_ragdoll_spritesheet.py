#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps


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


def paint_soft(
    subject: Image.Image,
    color: tuple[int, int, int],
    opacity: int,
    painter,
    *,
    blur: float = 1.0,
) -> None:
    mask = Image.new("L", subject.size, 0)
    painter(ImageDraw.Draw(mask))
    if blur:
        mask = mask.filter(ImageFilter.GaussianBlur(blur))
    alpha = ImageChops.multiply(mask, subject.getchannel("A"))
    alpha = alpha.point(lambda value: min(255, round(value * opacity / 255)))
    layer = Image.new("RGBA", subject.size, (*color, 0))
    layer.putalpha(alpha)
    subject.alpha_composite(layer)


def apply_reference_markings(source: Image.Image) -> Image.Image:
    """Paint the user's reference-cat face onto the source sprite."""
    cat = source.copy()

    cream = (250, 245, 226)
    warm_white = (255, 251, 236)
    warm_gray = (144, 125, 101)
    dark_gray = (65, 55, 47)

    # First cover the old symmetric mask; the reference cat has a bright, wide
    # white muzzle and a white blaze rising between uneven gray patches.
    paint_soft(
        cat,
        cream,
        238,
        lambda draw: (
            draw.ellipse((17, 26, 123, 112), fill=255),
            draw.ellipse((30, 64, 119, 124), fill=255),
            draw.polygon([(45, 18), (94, 15), (126, 55), (113, 112), (39, 112), (14, 63)], fill=255),
        ),
        blur=1.7,
    )

    # Left side in the photo: dark ear and an irregular gray cap, but the cheek
    # and eye area stay mostly white.
    paint_soft(
        cat,
        dark_gray,
        215,
        lambda draw: (
            draw.polygon([(16, 22), (34, 2), (52, 35), (39, 51), (21, 42)], fill=255),
            draw.polygon([(110, 13), (132, 4), (145, 34), (132, 57), (111, 42)], fill=255),
        ),
        blur=0.8,
    )
    paint_soft(
        cat,
        warm_gray,
        205,
        lambda draw: draw.polygon(
            [(18, 24), (48, 9), (75, 11), (88, 25), (78, 42), (57, 38), (39, 48), (19, 39)],
            fill=255,
        ),
        blur=1.1,
    )

    # Right side in the photo: a large warm gray mask wraps the higher right eye
    # and runs down the cheek, with a soft white muzzle cutting through it.
    paint_soft(
        cat,
        warm_gray,
        238,
        lambda draw: (
            draw.polygon(
                [(88, 15), (122, 9), (149, 36), (149, 76), (132, 116), (105, 106), (90, 75), (82, 42)],
                fill=255,
            ),
            draw.ellipse((90, 27, 150, 111), fill=255),
        ),
        blur=1.35,
    )
    paint_soft(
        cat,
        dark_gray,
        76,
        lambda draw: draw.ellipse((88, 46, 121, 76), fill=255),
        blur=1.4,
    )

    # Carve the photo's bright white blaze and muzzle back through the gray.
    paint_soft(
        cat,
        warm_white,
        245,
        lambda draw: draw.polygon([(55, 8), (80, 13), (93, 43), (91, 70), (79, 88), (60, 71), (49, 35)], fill=255),
        blur=1.2,
    )
    paint_soft(
        cat,
        warm_white,
        252,
        lambda draw: (
            draw.ellipse((20, 49, 80, 106), fill=255),
            draw.ellipse((53, 64, 119, 121), fill=255),
            draw.ellipse((35, 80, 115, 130), fill=255),
            draw.polygon([(66, 58), (94, 59), (104, 105), (84, 127), (60, 109)], fill=255),
        ),
        blur=1.2,
    )
    paint_soft(
        cat,
        warm_gray,
        150,
        lambda draw: draw.polygon([(107, 64), (128, 59), (126, 101), (116, 112), (106, 99)], fill=255),
        blur=1.4,
    )
    paint_soft(
        cat,
        warm_white,
        145,
        lambda draw: draw.polygon([(118, 91), (137, 92), (131, 124), (111, 124), (105, 109)], fill=255),
        blur=1.2,
    )
    paint_soft(
        cat,
        warm_white,
        235,
        lambda draw: (
            draw.ellipse((58, 80, 112, 126), fill=255),
            draw.ellipse((70, 88, 124, 121), fill=255),
        ),
        blur=0.9,
    )
    paint_soft(
        cat,
        (222, 215, 197),
        52,
        lambda draw: draw.ellipse((98, 82, 138, 114), fill=255),
        blur=2.0,
    )
    paint_soft(
        cat,
        warm_gray,
        210,
        lambda draw: draw.polygon([(122, 47), (153, 53), (152, 112), (132, 125), (117, 100)], fill=255),
        blur=1.2,
    )

    draw = ImageDraw.Draw(cat, "RGBA")
    fur_strokes = [
        (48, 18, 50, 42),
        (56, 15, 57, 38),
        (63, 13, 63, 34),
        (74, 15, 72, 39),
        (88, 23, 87, 50),
        (101, 21, 104, 52),
        (118, 26, 115, 61),
        (132, 38, 122, 73),
    ]
    for x0, y0, x1, y1 in fur_strokes:
        color = (81, 71, 59, 64) if x0 > 82 else (126, 114, 95, 72)
        draw.line((x0, y0, x1, y1), fill=color, width=1)

    # Uneven eyes from the photo: the viewer-left eye sits lower/smaller, while
    # the viewer-right eye is larger inside the gray mask.
    draw.ellipse((47, 61, 68, 77), fill=(27, 25, 24, 238))
    draw.ellipse((50, 63, 66, 76), fill=(78, 107, 124, 240))
    draw.ellipse((55, 64, 66, 75), fill=(24, 29, 33, 235))
    draw.ellipse((51, 62, 56, 66), fill=(235, 245, 252, 228))
    draw.ellipse((90, 49, 114, 73), fill=(23, 23, 22, 246))
    draw.ellipse((93, 51, 111, 71), fill=(56, 94, 120, 246))
    draw.ellipse((99, 54, 111, 69), fill=(20, 26, 32, 242))
    draw.ellipse((94, 51, 100, 57), fill=(225, 239, 250, 228))

    draw.polygon([(77, 79), (86, 78), (89, 82), (84, 88), (77, 87), (74, 83)], fill=(226, 157, 155, 226))
    draw.ellipse((78, 81, 80, 83), fill=(123, 72, 78, 96))
    draw.ellipse((86, 80, 88, 82), fill=(123, 72, 78, 96))
    draw.line((83, 88, 83, 96), fill=(105, 68, 70, 96), width=1)
    draw.arc((73, 92, 84, 101), 30, 95, fill=(105, 68, 70, 68), width=1)
    draw.arc((82, 92, 98, 101), 85, 155, fill=(105, 68, 70, 68), width=1)

    for side, x0, y0, length in (("left", 60, 91, 48), ("right", 94, 88, 61)):
        sign = -1 if side == "left" else 1
        for idx, dy in enumerate((-12, -4, 5, 14, 22)):
            draw.line(
                (x0, y0 + dy, x0 + sign * (length + idx * 5), y0 + dy * 0.50 - 8),
                fill=(255, 253, 241, 138),
                width=1,
            )
    return cat


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
    blink: bool = False,
    wink: bool = False,
    tail: bool = False,
    dust: bool = False,
    dizzy: bool = False,
    shadow: bool = False,
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

    draw = ImageDraw.Draw(canvas, "RGBA")
    if shadow:
        shadow_width = 64 + abs(math.sin(phase * math.tau)) * 18
        draw.ellipse(
            (x - shadow_width / 2, baseline - 7, x + shadow_width / 2, baseline + 3),
            fill=(71, 59, 49, 45),
        )

    paste_centered(canvas, subject, x + sway, baseline + bob)

    if paw:
        paw_x = x + 34 * (-1 if flip else 1) + math.sin(phase * math.tau) * 4
        paw_y = baseline - 72 + math.cos(phase * math.tau) * 10
        draw.ellipse((paw_x - 8, paw_y - 8, paw_x + 10, paw_y + 10), fill=(73, 48, 40, 225))
        draw.ellipse((paw_x - 3, paw_y - 4, paw_x + 5, paw_y + 4), fill=(236, 184, 188, 190))
        draw.arc((paw_x + 8, paw_y - 20, paw_x + 34, paw_y + 12), 190, 300, fill=(111, 75, 54, 165), width=3)

    if sleep:
        z_x = x + 48
        z_y = baseline - 134 - 8 * math.sin(phase * math.tau)
        draw.text((z_x, z_y), "Z", fill=(80, 90, 120, 190))

    if spark:
        cx = x + 48 * (-1 if flip else 1)
        cy = baseline - 132 + math.sin(phase * math.tau) * 5
        draw.line((cx - 6, cy, cx + 6, cy), fill=(90, 160, 240, 170), width=2)
        draw.line((cx, cy - 6, cx, cy + 6), fill=(90, 160, 240, 170), width=2)

    if tail:
        side = -1 if flip else 1
        tx = x + side * (55 + math.sin(phase * math.tau) * 5)
        ty = baseline - 78 + math.cos(phase * math.tau) * 4
        box = (tx - 23, ty - 30, tx + 35, ty + 34) if side > 0 else (tx - 35, ty - 30, tx + 23, ty + 34)
        start, end = (210, 330) if side > 0 else (210, 330)
        draw.arc(box, start, end, fill=(86, 72, 61, 38), width=2)

    if dust:
        drift = math.sin(phase * math.tau) * 8
        for idx in range(3):
            px = x - 38 + idx * 22 - drift
            py = baseline - 8 + (idx % 2) * 4
            draw.ellipse((px - 7, py - 3, px + 8, py + 4), fill=(154, 126, 97, 70))

    if blink or wink:
        eye_y = baseline - 101 + math.sin(phase * math.tau) * 2
        left_eye = x - 20
        right_eye = x + 19
        closed = (left_eye, right_eye) if blink else ((right_eye,) if not flip else (left_eye,))
        for ex in closed:
            draw.line((ex - 8, eye_y, ex + 8, eye_y + 1), fill=(45, 36, 32, 230), width=3)
            draw.arc((ex - 8, eye_y - 6, ex + 8, eye_y + 5), 20, 160, fill=(250, 242, 224, 210), width=2)

    if dizzy:
        cx = x + 36
        cy = baseline - 128 + math.sin(phase * math.tau) * 4
        for idx, offset in enumerate((0, 18, 36)):
            sx0 = cx - 16 + offset * 0.55
            sy0 = cy + math.sin(phase * math.tau + idx) * 8
            draw.line((sx0 - 5, sy0, sx0 + 5, sy0), fill=(98, 145, 210, 175), width=2)
            draw.line((sx0, sy0 - 5, sx0, sy0 + 5), fill=(98, 145, 210, 175), width=2)

    return canvas


def row_frames(source: Image.Image, row: int) -> list[Image.Image]:
    frames: list[Image.Image] = []
    for col in range(COLS):
        phase = col / COLS
        wave = math.sin(phase * math.tau)
        if row == 0:  # idle breathing
            frame = make_frame(
                source,
                phase=phase,
                scale=1.0,
                sx=1.0 + wave * 0.018,
                sy=1.0 - wave * 0.018,
                blink=col in (3, 4),
                tail=True,
                shadow=True,
            )
        elif row == 1:  # running right
            frame = make_frame(
                source,
                phase=phase,
                x=76 + col * 5,
                baseline=182 + abs(wave) * 5,
                scale=0.95,
                sx=1.12,
                sy=0.88,
                angle=wave * 8,
                ghost=(24, "right"),
                dust=True,
                shadow=True,
            )
        elif row == 2:  # running left
            frame = make_frame(
                source,
                phase=phase,
                x=116 - col * 5,
                baseline=182 + abs(wave) * 5,
                scale=0.95,
                sx=1.12,
                sy=0.88,
                angle=-wave * 8,
                flip=True,
                ghost=(24, "left"),
                dust=True,
                shadow=True,
            )
        elif row == 3:  # waving
            frame = make_frame(source, phase=phase, scale=1.0, angle=wave * 4, paw=True, tail=True, wink=col in (2, 3))
        elif row == 4:  # jumping
            jump = abs(math.sin(phase * math.tau))
            frame = make_frame(
                source,
                phase=phase,
                baseline=184 - jump * 40,
                scale=0.95 + jump * 0.02,
                sx=1.0 - jump * 0.08,
                sy=1.0 + jump * 0.12,
                angle=wave * 8,
                shadow=True,
                spark=col in (2, 6),
            )
        elif row == 5:  # failed
            frame = make_frame(
                source,
                phase=phase,
                baseline=190 + abs(wave) * 4,
                scale=0.98,
                sx=1.18,
                sy=0.82,
                angle=-10 + wave * 7,
                shade=0.88,
                dizzy=True,
                shadow=True,
            )
        elif row == 6:  # waiting
            frame = make_frame(
                source,
                phase=phase,
                scale=1.0,
                baseline=184 + abs(wave) * 4,
                sleep=True,
                blink=col in (1, 2, 5),
                tail=True,
                shadow=True,
            )
        elif row == 7:  # running / active
            frame = make_frame(
                source,
                phase=phase,
                x=96 + wave * 14,
                baseline=183 - abs(wave) * 10,
                scale=0.96,
                sx=1.08,
                sy=0.92,
                angle=wave * 10,
                ghost=(16, "right" if col % 2 == 0 else "left"),
                dust=col % 2 == 0,
                tail=True,
                shadow=True,
            )
        else:  # review
            frame = make_frame(
                source,
                phase=phase,
                scale=1.0,
                angle=wave * 5,
                spark=True,
                paw=col in (1, 2, 5, 6),
                blink=col == 4,
                tail=True,
            )
        frames.append(frame)
    return frames


def build_frames(source_path: Path) -> list[list[Image.Image]]:
    source = apply_reference_markings(crop_subject(Image.open(source_path).convert("RGBA")))
    return [row_frames(source, row) for row in range(ROWS)]


def make_spritesheet(frames_by_row: list[list[Image.Image]]) -> Image.Image:
    sheet = Image.new("RGBA", SHEET_SIZE, (0, 0, 0, 0))
    for row, frames in enumerate(frames_by_row):
        for col, frame in enumerate(frames):
            sheet.alpha_composite(frame, (col * FRAME_W, row * FRAME_H))
    return sheet


def generate(source_path: Path, out_path: Path) -> Image.Image:
    sheet = make_spritesheet(build_frames(source_path))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    return sheet


def save_contact_sheet(sheet: Image.Image, out_path: Path) -> None:
    scale = 0.5
    frame_w = round(FRAME_W * scale)
    frame_h = round(FRAME_H * scale)
    label_h = 10
    preview = Image.new("RGBA", (frame_w * COLS, (frame_h + label_h) * ROWS), (255, 255, 255, 255))
    draw = ImageDraw.Draw(preview)
    labels = ["idle", "run right", "run left", "wave", "jump", "oops", "nap", "dash", "spark"]
    for row in range(ROWS):
        draw.text((2, row * (frame_h + label_h)), labels[row], fill=(48, 42, 36, 255))
        for col in range(COLS):
            frame = sheet.crop((col * FRAME_W, row * FRAME_H, (col + 1) * FRAME_W, (row + 1) * FRAME_H))
            small = frame.resize((frame_w, frame_h), Image.Resampling.LANCZOS)
            preview.alpha_composite(small, (col * frame_w, row * (frame_h + label_h) + label_h))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    preview.save(out_path)


def save_motion_gif(sheet: Image.Image, out_path: Path) -> None:
    gif_frames: list[Image.Image] = []
    rows = [0, 3, 4, 7]
    for col in range(COLS):
        canvas = Image.new("RGBA", (FRAME_W * len(rows), FRAME_H), (255, 255, 255, 255))
        for idx, row in enumerate(rows):
            frame = sheet.crop((col * FRAME_W, row * FRAME_H, (col + 1) * FRAME_W, (row + 1) * FRAME_H))
            canvas.alpha_composite(frame, (idx * FRAME_W, 0))
        gif_frames.append(canvas.convert("P", palette=Image.Palette.ADAPTIVE))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    gif_frames[0].save(out_path, save_all=True, append_images=gif_frames[1:], duration=110, loop=0, disposal=2)


def main() -> int:
    sheet = generate(Path("assets/ragdoll-preview.png"), Path("pet/ragdoll-cat/spritesheet.png"))
    Path("output").mkdir(exist_ok=True)
    sheet.save(Path("output/animated-ragdoll-spritesheet.png"))
    save_contact_sheet(sheet, Path("assets/previews/animation-contact-sheet.png"))
    save_motion_gif(sheet, Path("assets/previews/ragdoll-motion-preview.gif"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
