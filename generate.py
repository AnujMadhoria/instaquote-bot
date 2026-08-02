"""
generate.py — Phase 1 (runs first, before anything is public)

1. Picks a quote (AI-generated or public-domain, mixed).
2. Renders it onto the styled image.
3. Writes a caption.
4. Saves image + a manifest.json that publish.py reads later.

This script does NOT talk to Instagram — it just prepares content. The
GitHub Actions workflow commits the output/ folder (making the image
publicly reachable via raw.githubusercontent.com) before publish.py runs.
"""

import os
import json
from datetime import datetime, timezone

from content_source import pick_quote
from caption_generator import build_caption
from image_generator import create_quote_image

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")

IG_HANDLE = os.environ.get("IG_HANDLE", "your.handle")


def main():
    os.makedirs(IMAGES_DIR, exist_ok=True)

    quote = pick_quote(mode="mix")
    caption = build_caption(quote)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    filename = f"post-{stamp}.jpg"
    image_path = os.path.join(IMAGES_DIR, filename)

    create_quote_image(
        highlight_text=quote.get("highlight"),
        body_paragraphs=quote.get("body_paragraphs", []),
        attribution=quote.get("attribution"),
        footer_text=IG_HANDLE,
        output_path=image_path,
    )

    manifest = {
        "filename": filename,
        "caption": caption,
        "source": quote.get("source"),
        "generated_at": stamp,
    }
    with open(os.path.join(OUTPUT_DIR, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated {filename} (source: {quote.get('source')})")
    print("---- caption ----")
    print(caption)


if __name__ == "__main__":
    main()
