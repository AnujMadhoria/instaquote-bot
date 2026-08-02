"""
image_generator.py

Renders a quote / poem excerpt onto a procedurally generated textured
paper background, styled to look like it was actually typed/printed on
physical paper and highlighted with a real marker — not flat vector text
on a solid color. No external image assets needed.

Output: a 1080x1350 JPG (Instagram 4:5 portrait) ready to post.
"""

import os
import math
import random
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_REGULAR = os.path.join(BASE_DIR, "assets/fonts/EBGaramond.ttf")
FONT_ITALIC = os.path.join(BASE_DIR, "assets/fonts/EBGaramond-Italic.ttf")

CANVAS_SIZE = (1080, 1350)

# darker, more muted paper tones (was too bright/washed out before)
PAPER_BASE_COLORS = [
    (205, 196, 174),
    (200, 190, 167),
    (209, 200, 179),
]
INK_COLOR = (35, 29, 22)          # warm near-black, like typewriter ribbon
HIGHLIGHT_COLOR = (241, 214, 48)  # marker yellow


def _load_font(path, size, weight=None):
    font = ImageFont.truetype(path, size)
    if weight is not None:
        try:
            font.set_variation_by_axes([weight])
        except Exception:
            pass
    return font


def make_paper_texture(width, height, seed=None):
    """Procedurally generate a darker, more textured paper/canvas background."""
    rng = np.random.default_rng(seed)
    base = random.choice(PAPER_BASE_COLORS)

    noise = rng.integers(-14, 14, (height, width), dtype=np.int16)
    r = np.clip(base[0] + noise, 0, 255).astype(np.uint8)
    g = np.clip(base[1] + noise, 0, 255).astype(np.uint8)
    b = np.clip(base[2] + noise, 0, 255).astype(np.uint8)
    arr = np.dstack([r, g, b])
    img = Image.fromarray(arr, "RGB")
    img = img.filter(ImageFilter.GaussianBlur(0.5))

    # coarser mottled patches (like uneven canvas/paper dye)
    patch_noise = rng.integers(-10, 10, (height // 8, width // 8), dtype=np.int16)
    patch_img = Image.fromarray(
        np.clip(128 + patch_noise, 0, 255).astype(np.uint8), "L"
    ).resize((width, height), Image.BICUBIC)
    patch_rgb = Image.merge("RGB", [patch_img, patch_img, patch_img])
    img = Image.blend(img, patch_rgb, alpha=0.10)

    # fine grain speckle
    grain = rng.integers(0, 255, (height, width), dtype=np.uint8)
    grain_img = Image.fromarray(grain, "L").convert("RGB")
    img = Image.blend(img, grain_img, alpha=0.035)

    # stronger vignette than before — darker edges
    vignette_mask = Image.new("L", (width, height), 0)
    vd = ImageDraw.Draw(vignette_mask)
    vd.ellipse([-width * 0.25, -height * 0.25, width * 1.25, height * 1.25], fill=255)
    vignette_mask = vignette_mask.filter(ImageFilter.GaussianBlur(200))
    dark_layer = Image.new("RGB", (width, height), tuple(max(c - 70, 0) for c in base))
    img = Image.composite(img, dark_layer, vignette_mask)

    # overall slight darkening pass
    arr2 = np.asarray(img).astype(np.int16) - 8
    img = Image.fromarray(np.clip(arr2, 0, 255).astype(np.uint8), "RGB")

    return img


def _wrap_by_pixel(draw, text, font, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_ink_line(canvas_rgba, x, y, text, font, fill, rng):
    """Draw one line of text character-by-character. Solid, fully opaque
    ink (no fading) — only a hairline position jitter is kept so it
    doesn't look robotically perfect."""
    draw = ImageDraw.Draw(canvas_rgba)
    cx = x
    for ch in text:
        dy = rng.uniform(-0.5, 0.5)
        draw.text((cx, y + dy), ch, font=font, fill=fill + (255,))
        cx += font.getlength(ch)
    return cx


def _draw_marker_highlight(base_img, x0, y0, x1, y1, seed=None):
    """Paints a clean, solid highlighter block — essentially a rectangle
    with only a couple of pixels of corner jitter, matching a real
    highlighter-pen swipe rather than an exaggerated wavy blob."""
    rng = random.Random(seed)
    pad = 6
    w, h = int(x1 - x0), int(y1 - y0)
    layer_w, layer_h = w + pad * 2, h + pad * 2
    layer = Image.new("RGBA", (layer_w, layer_h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)

    jitter = 3  # tiny corner irregularity only — stays essentially rectangular
    tl = (pad + rng.uniform(-jitter, jitter), pad + rng.uniform(-jitter, jitter))
    tr = (pad + w + rng.uniform(-jitter, jitter), pad + rng.uniform(-jitter, jitter))
    br = (pad + w + rng.uniform(-jitter, jitter), pad + h + rng.uniform(-jitter, jitter))
    bl = (pad + rng.uniform(-jitter, jitter), pad + h + rng.uniform(-jitter, jitter))
    ld.polygon([tl, tr, br, bl], fill=HIGHLIGHT_COLOR + (255,))
    layer = layer.filter(ImageFilter.GaussianBlur(0.5))

    px, py = int(x0 - pad), int(y0 - pad)
    base_img.paste(layer, (px, py), layer)


def create_quote_image(
    highlight_text,
    body_paragraphs,
    attribution=None,
    footer_text="YOUR.HANDLE",
    output_path="output.jpg",
    seed=None,
):
    width, height = CANVAS_SIZE
    seed = seed if seed is not None else random.randint(0, 999999)
    rng = random.Random(seed)

    img = make_paper_texture(width, height, seed=seed)
    measure_draw = ImageDraw.Draw(img)

    margin_x = 140
    max_text_width = width - margin_x * 2

    # smaller sizes + a touch more weight than the first draft
    highlight_font = _load_font(FONT_REGULAR, 50, weight=640)
    body_font = _load_font(FONT_REGULAR, 44, weight=480)
    italic_font = _load_font(FONT_ITALIC, 36)
    footer_font = _load_font(FONT_REGULAR, 24, weight=520)

    line_gap = 16
    para_gap = 38

    blocks = []
    if highlight_text:
        blocks.append((_wrap_by_pixel(measure_draw, highlight_text, highlight_font, max_text_width), highlight_font, True))
    for para in body_paragraphs:
        blocks.append((_wrap_by_pixel(measure_draw, para, body_font, max_text_width), body_font, False))
    if attribution:
        blocks.append(([attribution], italic_font, False))

    def block_height(lines, font):
        ascent, descent = font.getmetrics()
        return len(lines) * (ascent + descent + line_gap)

    total_height = sum(block_height(b[0], b[1]) for b in blocks) + para_gap * (len(blocks) - 1)
    y = (height - total_height) / 2 - 40

    ink_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    for lines, font, is_highlight in blocks:
        ascent, descent = font.getmetrics()
        line_height = ascent + descent + line_gap

        if is_highlight:
            block_w = max(measure_draw.textlength(l, font=font) for l in lines)
            block_h = line_height * len(lines) - line_gap
            pad_x, pad_y = 10, 5
            _draw_marker_highlight(
                img,
                margin_x - pad_x, y - pad_y,
                margin_x + block_w + pad_x, y + block_h + pad_y,
                seed=seed + 1,
            )

        for line in lines:
            _draw_ink_line(ink_layer, margin_x, y, line, font, INK_COLOR, rng)
            y += line_height

        y += para_gap

    # soften the vector edges of the text so it reads as printed/typed
    # ink absorbed into paper fibers, not crisp screen text
    ink_layer = ink_layer.filter(ImageFilter.GaussianBlur(0.35))

    img = Image.alpha_composite(img.convert("RGBA"), ink_layer)

    # footer watermark
    draw = ImageDraw.Draw(img)
    tracked = " ".join(list(footer_text.upper()))
    fw = draw.textlength(tracked, font=footer_font)
    draw.text(((width - fw) / 2, height - 108), tracked, font=footer_font, fill=(96, 88, 72))

    img = img.convert("RGB")
    img.save(output_path, "JPEG", quality=93)
    return output_path


if __name__ == "__main__":
    create_quote_image(
        highlight_text="Congratulations!",
        body_paragraphs=[
            "A permanent position with a higher salary will be coming in August.",
            "Send this to yourself immediately.",
        ],
        footer_text="yourhandle",
        output_path=os.path.join(BASE_DIR, "sample_output.jpg"),
        seed=42,
    )
    print("Saved sample_output.jpg")
