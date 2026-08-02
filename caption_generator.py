"""
caption_generator.py

Builds the Instagram caption + hashtags for a post. Works with zero API
keys out of the box (template-based). If ANTHROPIC_API_KEY is set, it
asks Claude to write a punchier, more varied caption instead.
"""

import os
import random

BASE_HASHTAGS = [
    "#manifestation", "#affirmations", "#motivation", "#goodvibes",
    "#mindset", "#selfgrowth", "#positivity", "#dailyquotes",
    "#lawofattraction", "#healing",
]

TEMPLATE_OPENERS = [
    "Claim this energy. ✨",
    "Read this like it's meant for you. 🤍",
    "Save this for the days you forget. 📌",
    "Send this to someone who needs it today.",
]

CTA_LINES = [
    "Tag someone who needs to see this.",
    "Save this for later — you'll want it again.",
    "Which line hit you the most? Tell me below.",
    "Follow for a new one every day.",
]


def _template_caption(quote):
    opener = random.choice(TEMPLATE_OPENERS)
    cta = random.choice(CTA_LINES)
    body = " ".join(quote["body_paragraphs"]) if quote["body_paragraphs"] else ""
    attribution = f"\n\n{quote['attribution']}" if quote.get("attribution") else ""

    caption = f"{opener}\n\n{quote.get('highlight') or body}"
    if body and quote.get("highlight"):
        caption += f"\n{body}"
    caption += attribution
    caption += f"\n\n{cta}"

    hashtags = random.sample(BASE_HASHTAGS, k=6)
    caption += "\n\n" + " ".join(hashtags)
    return caption


def _ai_caption(quote):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _template_caption(quote)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        quote_text = (quote.get("highlight") or "") + " " + " ".join(quote["body_paragraphs"])
        attribution_note = f" (originally by {quote['attribution']}, credit them)" if quote.get("attribution") else ""

        prompt = (
            f"Write an Instagram caption for a manifestation/motivational quote "
            f"post. The quote shown in the image is: \"{quote_text.strip()}\"{attribution_note}. "
            "Style: warm, short, 2-4 lines, then a call-to-action (save/tag/follow), "
            "then 6-8 relevant hashtags on the last line. No emojis in every line — "
            "use them sparingly. Respond with ONLY the caption text, nothing else."
        )
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in msg.content if hasattr(b, "text")).strip()
        return text or _template_caption(quote)
    except Exception:
        return _template_caption(quote)


def build_caption(quote):
    return _ai_caption(quote)


if __name__ == "__main__":
    sample = {
        "highlight": "This is your sign.",
        "body_paragraphs": ["The thing you've been quietly working toward", "is closer than it looks."],
        "attribution": None,
    }
    print(build_caption(sample))
