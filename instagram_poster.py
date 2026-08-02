"""
instagram_poster.py

Thin wrapper around Meta's official Instagram Graph API for publishing a
single image post. This is the same API Buffer/Later/Hootsuite use under
the hood — it requires an Instagram *Business or Creator* account linked
to a Facebook Page, a Meta app, and a long-lived access token.

Two-step publish flow:
  1. Create a media container from a PUBLIC image URL.
  2. Publish that container.

See README.md for how to get IG_USER_ID and IG_ACCESS_TOKEN.
"""

import os
import time
import requests

GRAPH_API_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class InstagramPostError(Exception):
    pass


def create_media_container(ig_user_id, image_url, caption, access_token):
    resp = requests.post(
        f"{GRAPH_BASE}/{ig_user_id}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token,
        },
        timeout=30,
    )
    data = resp.json()
    if "id" not in data:
        raise InstagramPostError(f"Failed to create media container: {data}")
    return data["id"]


def publish_media(ig_user_id, creation_id, access_token, max_retries=5):
    """Instagram sometimes needs a few seconds to finish processing the
    container before it can be published — retry with backoff."""
    for attempt in range(max_retries):
        resp = requests.post(
            f"{GRAPH_BASE}/{ig_user_id}/media_publish",
            data={"creation_id": creation_id, "access_token": access_token},
            timeout=30,
        )
        data = resp.json()
        if "id" in data:
            return data["id"]

        error = data.get("error", {})
        if error.get("error_subcode") == 2207027:  # media still processing
            time.sleep(5 * (attempt + 1))
            continue
        raise InstagramPostError(f"Failed to publish media: {data}")

    raise InstagramPostError("Media never finished processing after retries")


def post_image(ig_user_id, image_url, caption, access_token):
    """Full publish flow. Returns the published media ID."""
    creation_id = create_media_container(ig_user_id, image_url, caption, access_token)
    time.sleep(3)  # brief pause before checking/publishing
    media_id = publish_media(ig_user_id, creation_id, access_token)
    return media_id


if __name__ == "__main__":
    ig_user_id = os.environ["IG_USER_ID"]
    access_token = os.environ["IG_ACCESS_TOKEN"]
    image_url = os.environ["POST_IMAGE_URL"]
    caption = os.environ.get("POST_CAPTION", "")

    media_id = post_image(ig_user_id, image_url, caption, access_token)
    print(f"Published! media_id={media_id}")
