# InstaQuote Bot

Generates a manifestation/quote-style image daily (textured paper background,
serif type, yellow-highlighter hook line) and posts it to Instagram
automatically via Meta's official Graph API — the same API Buffer/Later
use, so it's compliant with Instagram's automation rules (no bots/Selenium
that could get your account flagged).

**Content mix:** ~50% freshly AI-generated original affirmations, ~50%
short excerpts from poets who are safely public domain (Dickinson, Whitman,
Wordsworth, Blake, Keats, etc. — all published pre-1929 / authors dead 70+
years). Public-domain excerpts are auto-credited in the caption.

Posts are static images, not reels — this sidesteps the copyrighted-music
licensing issue entirely and is far simpler to automate reliably.

---

## 1. Set up your Instagram account (one-time)

1. **Switch to a Professional account.** In the Instagram app: Settings →
   Account type and tools → Switch to Professional Account → choose
   *Creator* or *Business*.
2. **Link a Facebook Page.** During that same flow (or later under
   Settings → Linked accounts), connect the IG account to a Facebook Page.
   If you don't have one, create a new Page — it can be minimal, it just
   needs to exist as the connector between IG and the Graph API.

## 2. Create a Meta App (one-time)

1. Go to [developers.facebook.com/apps](https://developers.facebook.com/apps)
   → **Create App** → type: *Other* → *Business*.
2. In the app dashboard, **Add Product** → find **Instagram** → set up the
   **Instagram API** (formerly "Instagram Graph API") product.
3. Under App Roles, add yourself as an **Admin/Tester** so you can generate
   tokens for your own account without needing Meta's public app review.

## 3. Get your access token and IG user ID

1. Go to **Graph API Explorer**
   ([developers.facebook.com/tools/explorer](https://developers.facebook.com/tools/explorer)).
2. Select your app, click **Get Token → Get User Access Token**, and check
   these permissions: `instagram_basic`, `instagram_content_publish`,
   `pages_show_list`, `pages_read_engagement`.
3. Generate the token, then **exchange it for a long-lived token** (lasts
   ~60 days instead of ~1 hour):
   ```
   GET https://graph.facebook.com/v21.0/oauth/access_token
       ?grant_type=fb_exchange_token
       &client_id={app-id}
       &client_secret={app-secret}
       &fb_exchange_token={short-lived-token}
   ```
   Save the returned token — this is your `IG_ACCESS_TOKEN`.
4. Find your **IG_USER_ID**:
   ```
   GET https://graph.facebook.com/v21.0/me/accounts?access_token={token}
   ```
   Copy the Page ID from the result, then:
   ```
   GET https://graph.facebook.com/v21.0/{page-id}?fields=instagram_business_account&access_token={token}
   ```
   The `id` in the response is your `IG_USER_ID`.

> **Token expiry:** long-lived tokens last ~60 days. Repeat step 3's
> exchange call before it expires (you can do this anytime while the
> current token is still valid — it resets the 60-day clock) and update
> the `IG_ACCESS_TOKEN` secret. Put a recurring reminder on your calendar
> every ~50 days.

## 4. Push this project to GitHub and add secrets

1. Create a new GitHub repo and push this folder to it.
2. Go to **Settings → Secrets and variables → Actions** and add:
   - `IG_ACCESS_TOKEN` — from step 3
   - `IG_USER_ID` — from step 3
   - `ANTHROPIC_API_KEY` — *(optional)* from
     [console.anthropic.com](https://console.anthropic.com) — enables
     AI-generated quotes/captions instead of the template fallback
3. Under **Settings → Secrets and variables → Actions → Variables**, add:
   - `IG_HANDLE` — your Instagram @handle, shown as the watermark
4. Go to the **Actions** tab and enable workflows if prompted. The
   `daily-post.yml` workflow will now run automatically at the scheduled
   time (edit the cron line to change it — it's in UTC).

## 5. Test it manually first

Before trusting the daily schedule, trigger it once by hand:
**Actions tab → Daily Instagram Post → Run workflow.** Check the run logs
and your Instagram feed.

---

## Running locally (optional, for tweaking the design)

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in values you want to test with
python generate.py     # renders output/images/*.jpg + writes manifest.json
```

Open the generated image in `output/images/` to preview the design before
it ever touches the internet. `publish.py` requires the image to already
be publicly reachable (i.e. pushed to GitHub), so it's meant to run inside
the GitHub Actions workflow, not standalone locally — unless you host the
image somewhere public yourself and hardcode the URL.

## Customizing the look

All the visual design lives in `image_generator.py`:
- `PAPER_BASE_COLORS` — background tones
- `HIGHLIGHT_COLOR` — the marker-yellow color
- `CANVAS_SIZE` — currently 1080×1350 (4:5, Instagram's recommended
  portrait ratio)
- Fonts are in `assets/fonts/` (EB Garamond, SIL Open Font License —
  free to use/modify). Swap in any other `.ttf` you like.

## Costs

- GitHub Actions: free for public repos (2,000 min/month free even for
  private repos, and this job takes under a minute).
- Graph API posting: free.
- Image hosting: free — reuses the GitHub raw URL of the committed image,
  no third-party host needed.
- Anthropic API (optional): a few cents per month at 1 post/day.

## A note on scale

Instagram's Graph API allows up to 25 posts per rolling 24 hours per
account, so daily posting has huge headroom if you later want to post
more often or run multiple themed accounts.
