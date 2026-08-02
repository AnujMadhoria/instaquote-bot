"""
publish.py — Phase 2 (runs after generate.py's output has been git-pushed)

Reads output/manifest.json, builds the public raw.githubusercontent.com
URL for the image that was just committed, and publishes it to Instagram
via the Graph API.

Required env vars:
  GH_REPO         e.g. "yourname/instaquote-bot"
  GH_BRANCH       defaults to "main"
  IG_USER_ID      Instagram Business Account ID
  IG_ACCESS_TOKEN Long-lived Instagram Graph API access token
"""

import os
import json
import time

from instagram_poster import post_image, InstagramPostError

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def main():
    with open(os.path.join(OUTPUT_DIR, "manifest.json")) as f:
        manifest = json.load(f)

    gh_repo = os.environ["GH_REPO"]
    gh_branch = os.environ.get("GH_BRANCH", "main")
    ig_user_id = os.environ["IG_USER_ID"]
    access_token = os.environ["IG_ACCESS_TOKEN"]

    image_url = (
        f"https://raw.githubusercontent.com/{gh_repo}/{gh_branch}"
        f"/output/images/{manifest['filename']}"
    )
    print(f"Publishing {image_url}")

    # Give the CDN a moment to catch up with the push
    time.sleep(10)

    try:
        media_id = post_image(ig_user_id, image_url, manifest["caption"], access_token)
        print(f"Published to Instagram. media_id={media_id}")
    except InstagramPostError as e:
        print(f"Instagram publish failed: {e}")
        raise


if __name__ == "__main__":
    main()
