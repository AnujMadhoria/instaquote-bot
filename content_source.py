"""
content_source.py

Produces the text content for a post. Mixes two sources, chosen at random
each run:

  1. "ai"        — an original short affirmation/quote generated fresh by
                    an LLM (Anthropic API). No copyright risk since it's
                    newly generated text.

  2. "public_domain" — a short excerpt (2-4 lines) pulled from PoetryDB
                    (https://poetrydb.org), restricted to a curated list
                    of poets who died 70+ years ago AND whose relevant
                    works were published pre-1929, so they are safely in
                    the public domain in the US. We deliberately do NOT
                    use translated works (e.g. Rumi translations), since
                    translations carry their own separate copyright.

Both paths fall back to a small local list if the network/API call fails,
so the pipeline never breaks a scheduled run.
"""

import os
import random
import json
import requests

# Poets confirmed public domain (death 70+ years ago, works pre-1929 US publication)
CURATED_PD_POETS = [
    "Emily Dickinson",
    "Walt Whitman",
    "William Wordsworth",
    "William Blake",
    "John Keats",
    "Christina Rossetti",
    "Ralph Waldo Emerson",
    "Henry Wadsworth Longfellow",
    "Elizabeth Barrett Browning",
]

# Small offline fallback so the script never fails a scheduled run
LOCAL_PD_FALLBACK = [
    {
        "lines": ["Not knowing when the dawn will come,", "I open every door."],
        "author": "Emily Dickinson",
    },
    {
        "lines": ["I celebrate myself, and sing myself,", "and what I assume you shall assume."],
        "author": "Walt Whitman",
    },
]

LOCAL_AI_FALLBACK = [
    {
        "highlight": "This is your sign.",
        "body": ["The thing you've been quietly working toward", "is closer than it looks."],
    },
    {
        "highlight": "Good news is coming.",
        "body": ["Stay ready.", "Stay open.", "It's already on its way to you."],
    },
]


def fetch_public_domain_snippet():
    """Pull a random 2-4 line excerpt from a curated, safely-PD poet."""
    poet = random.choice(CURATED_PD_POETS)
    try:
        resp = requests.get(
            f"https://poetrydb.org/author/{requests.utils.quote(poet)}",
            timeout=8,
        )
        resp.raise_for_status()
        poems = resp.json()
        if not isinstance(poems, list) or not poems:
            raise ValueError("no poems returned")

        poem = random.choice(poems)
        lines = [l for l in poem.get("lines", []) if l.strip()]
        if len(lines) < 2:
            raise ValueError("poem too short")

        start = random.randint(0, max(0, len(lines) - 4))
        excerpt = lines[start:start + random.choice([2, 3])]
        return {"lines": excerpt, "author": poet}
    except Exception:
        return random.choice(LOCAL_PD_FALLBACK)


def generate_ai_quote():
    """Generate an original short affirmation/quote via the Gemini API.
    Requires GEMINI_API_KEY. Falls back to a local list if unset/unavailable.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return random.choice(LOCAL_AI_FALLBACK)

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        prompt = (
            "Write one short, original manifestation/affirmation-style quote "
            "in the tone of a viral Instagram 'good news is coming' post. "
            "Respond ONLY with JSON, no markdown fences, in this exact shape: "
            '{"highlight": "3-6 word punchy hook line", '
            '"body": ["line 1", "line 2", "optional line 3"]}. '
            "Keep it warm, hopeful, and universal — no specific names, no "
            "religious claims, no financial/medical promises."
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        text = (response.text or "").strip()
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        if "highlight" in data and "body" in data:
            return data
        raise ValueError("unexpected shape")
    except Exception:
        return random.choice(LOCAL_AI_FALLBACK)


def pick_quote(mode="mix"):
    """
    Returns a normalized dict:
      {
        "highlight": str or None,
        "body_paragraphs": [str, ...],
        "attribution": str or None,
        "source": "ai" | "public_domain",
      }
    """
    source = random.choice(["ai", "public_domain"]) if mode == "mix" else mode

    if source == "ai":
        data = generate_ai_quote()
        return {
            "highlight": data.get("highlight"),
            "body_paragraphs": data.get("body", []),
            "attribution": None,
            "source": "ai",
        }
    else:
        data = fetch_public_domain_snippet()
        lines = data["lines"]
        return {
            "highlight": lines[0],
            "body_paragraphs": lines[1:] if len(lines) > 1 else [],
            "attribution": f"— {data['author']}",
            "source": "public_domain",
        }


if __name__ == "__main__":
    print(json.dumps(pick_quote(), indent=2))
