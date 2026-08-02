# Travel Social Agent

Turn hundreds of travel photos and a few scattered memories into a social media post worth sharing.

Even after an amazing trip, I often find myself putting off posting anything. Sharing a travel story means sorting through hundreds of photos, remembering what happened at each moment, choosing the images that best capture the experience, and writing a caption that matches the place, culture, and mood. By the time I think about doing all of that, the trip is over, everyday life has resumed, and the post never gets made.

I do not want to overshare every detail of a vacation. But I still value sharing a few meaningful moments. A thoughtful travel post can help me connect with people who have similar interests, preserve memories that would otherwise fade, and give me something personal to revisit years later.

That is why I created Travel Social Agent.

You describe what happened and point the app to a folder of photos. The agent reads your story, reviews the images, selects the ones that best match the experience, drafts a platform-appropriate caption, and shows you a preview. You stay in control throughout the process, and nothing is published until you explicitly approve it.

The current version publishes to a Facebook Page, but the same workflow could later be extended to platforms such as Instagram or RedNote, with captions and formatting adapted to each platform.

Built as a learning project for agentic AI, the app explores tool calling, multimodal reasoning, workflow orchestration, and human-in-the-loop approval.

Have fun, keep traveling, and make the memories easier to share.

This is how the agent works: you write what happened. The agent reads your story, looks at each photo, picks the handful that actually match, drafts a caption, and shows you a preview. Nothing is published until you click the button.

Built as a learning project for agentic AI: tool calling, multimodal reasoning, workflow orchestration, and human-in-the-loop approval.

---

## What it does

1. **Story** — you write about the trip in your own words.
2. **Photos** — you point at a local folder. It can contain photos from other trips.
3. **Recommendations** — every photo is scored against your story. You get a cover photo, an ordered set of supporting photos, a plain-language reason for each, alternatives you can swap in, and the ones that clearly do not fit set aside.
4. **Caption** — an editable draft next to a live Facebook preview, with one-click revisions (*Make shorter*, *More personal*, *Focus on the people*, *Try another opening*).
5. **Publish** — the connected Page is named explicitly, you see exactly what will go out, and one button sends it.

The interface is styled as a travel journal: a paper page on a desk, photos taped in as prints. The Facebook preview deliberately stays plain, because it has to look like the real post rather than like stationery.

---

## Safety

This tool posts to a real social media account, so the defaults are cautious:

- **Nothing is ever auto-posted.** Publishing only happens on an explicit click in the final step.
- **`DRY_RUN=true` is the default.** In this mode the app runs the entire flow and logs what *would* be sent, without calling Facebook at all.
- **Your keys stay local.** Everything is read from `.env`, which is git-ignored. No credentials are hardcoded anywhere.
- **Your photos stay local.** `data/photos/` is git-ignored except for a placeholder. Photos are sent to the OpenAI API for scoring, and only the ones you approve go to Facebook.

---

## Requirements

- Python 3.9 or newer
- An OpenAI API key (uses `gpt-4o` for text and vision)
- A Facebook Page you administer — only needed for the publish step

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/YOUR_USERNAME/travel-social-agent.git
cd travel-social-agent
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create your `.env`

```bash
cp .env.example .env
```

Open `.env` and add your OpenAI key:

```
OPENAI_API_KEY=sk-proj-...
```

That is enough to run everything except publishing.

### 4. Add some photos

Drop `.jpg`, `.jpeg`, `.png`, `.webp`, or `.heic` files into `data/photos/`, or point the app at any folder on your machine.

Deliberately include a few photos that have nothing to do with your story — that is the part worth watching.

### 5. Run it

```bash
streamlit run app.py
```

Then open http://localhost:8501.

---

## Connecting a Facebook Page

Skip this if you only want to try the photo selection and caption writing. The app runs fine in dry-run mode without it.

Facebook's permission model is the fiddliest part of this project. The key thing to know up front: **Graph API Explorer gives you a *User* token, but posting to a Page needs that Page's own token.** These are different strings, and using the wrong one produces a confusing "does not exist, or missing permissions" error.

### 1. Create a Meta app

Go to [developers.facebook.com](https://developers.facebook.com) → **My Apps** → **Create App**. Any type is fine.

### 2. Enable the Page permissions

In your app, open **Use cases** and customise **Manage everything on your Page**. Make sure both of these are added:

- `pages_manage_posts`
- `pages_read_engagement`

Both are required. With only one, Graph API Explorer refuses to generate a Page token at all.

### 3. Generate a User token

Open the [Graph API Explorer](https://developers.facebook.com/tools/explorer/), select your app, add those two permissions, and click **Generate Access Token**. Approve the dialog.

Copy the token into your `.env` as `FACEBOOK_PAGE_ACCESS_TOKEN` for now — the next step swaps it for the right one.

### 4. Exchange it for the Page token

```bash
python scripts/check_facebook_credentials.py --write-env
```

This lists the Pages your token can manage and writes the correct Page ID and Page token into `.env` for you. Tokens are printed redacted, so it is safe to share the output when asking for help.

### 5. Test it

```bash
python scripts/try_facebook_post.py              # dry run, publishes nothing
python scripts/try_facebook_post.py --live       # real text-only post
```

Once that works, set `DRY_RUN=false` in `.env` when you are ready to publish from the app.

> **Page tokens expire.** A token from Graph API Explorer typically lasts about an hour, or roughly 60 days if you exchange it for a long-lived one. When publishing suddenly fails with an OAuth error, re-run step 4.

---

## Helper scripts

| Command | What it does |
|---|---|
| `python scripts/check_facebook_credentials.py` | Shows which Pages your token can post to. Add `--write-env` to save the right one. |
| `python scripts/try_photo_scoring.py` | Runs story analysis and photo scoring in the terminal so you can see raw scores and reasons. Use `--folder` for a different directory. |
| `python scripts/try_facebook_post.py` | Tests posting. Dry run by default; `--live` publishes, `--photos` attaches images. |

Run the tests with:

```bash
pytest
```

These are offline — they do not need any API keys.

---

## Development preview

To work on the UI without spending API calls, append a query parameter:

- `http://localhost:8501/?preview=1` — jumps to the Recommendations step with seeded data
- `http://localhost:8501/?preview=caption` — jumps to the Caption step

Both use whatever photos are in `data/photos/` with fabricated scores. Without the parameter the flag is inert.

---

## How it works

```
        your story                     your photo folder
             │                                │
             ▼                                ▼
      analyze_story()                 scan_local_images()
   location · main event                 paths + sizes
   tone · things to look for                  │
             └──────────────┬─────────────────┘
                            ▼
                  score_image_relevance()      ← one vision call per photo
                     score 1–10 + reason
                            ▼
                   select_best_images()
                 threshold + rank + limit
                            ▼
              generate_facebook_caption()
                            ▼
                    ┌───────────────┐
                    │  YOU APPROVE  │           ← nothing proceeds without this
                    └───────────────┘
                            ▼
                  post_to_facebook_page()
```

### Layout

```
travel_social_agent/
├── app.py                     Streamlit UI — the five steps
├── src/
│   ├── config.py              Reads .env
│   ├── state.py               Shared state passed between agent nodes
│   ├── graph.py               The same tools wired as a LangGraph workflow
│   ├── agents/                Nodes that reason (each wraps an LLM call)
│   │   ├── story_analyzer.py
│   │   ├── photo_ranker.py
│   │   └── caption_writer.py
│   ├── tools/                 Functions with real-world effects
│   │   ├── image_tools.py     Scan folders, convert HEIC, select photos
│   │   ├── facebook_tool.py   Meta Graph API
│   │   └── database_tool.py   SQLite drafts
│   ├── prompts/               One markdown file per LLM role
│   ├── services/              API clients
│   └── ui/                    theme.py (design tokens + CSS), components.py
├── scripts/                   Terminal helpers, not part of the app
└── tests/                     Offline tests
```

### Notes for anyone reading the code

- **`src/graph.py` is not what the app runs.** The Streamlit UI calls the agent nodes directly so it can show real per-photo progress and pause for approval. `graph.py` wires the identical tools into a LangGraph `StateGraph`, kept as a readable reference for how the same pipeline looks as a graph.
- **Relevance scores never reach the screen.** The model returns 1–10; the UI translates that into "Strong match" / "Good match" / "Possible". A decimal is not something a person can act on, and the selection controls ask about intent ("Only the best" / "Balanced" / "Include more") rather than a number.
- **HEIC is converted in memory.** OpenAI's API does not accept HEIC, so iPhone photos are decoded to JPEG before upload. Your files are never modified.

---

## Cost

Roughly, per post, using `gpt-4o`:

- 1 text call for the story
- **1 vision call per photo in the folder**
- 1 text call per caption, plus 1 for each revision

The photo scoring dominates. A folder of 50 photos means 50 vision calls every time you run it. Start small.

---

## Troubleshooting

**"does not exist, cannot be loaded due to missing permissions"**
You are using a User token where a Page token is needed, or the Page ID is wrong. Run `python scripts/check_facebook_credentials.py`.

**"Session has expired"**
Page tokens are short-lived. Regenerate in Graph API Explorer and re-run the credentials script.

**`pages_manage_posts` is missing from the permissions dropdown**
Your app has not enabled the Page use case yet. App dashboard → **Use cases** → customise **Manage everything on your Page**.

**Graph API Explorer keeps switching back to "User Token"**
It does that after the approval dialog. Ignore it — generate the User token, then let `check_facebook_credentials.py` do the exchange.

**HEIC photos are not showing up**
Install the decoder: `pip install pillow-heif`.

**"Port 8501 is already in use"**
An earlier Streamlit is still running. `pkill -f "streamlit run app.py"`, or use `streamlit run app.py --server.port 8502`.

**No photos pass the threshold**
Open **Adjust** on the Recommendations step and choose *Include more*, or pull a photo out of the *Set aside* section with **Add anyway**.

---

## Limitations

- Photos come from a local folder only. No iCloud, Google Photos, or upload widget.
- One Facebook Page at a time. No Instagram, Threads, or scheduling.
- Every run re-scores every photo; results are not cached between runs.
- The page-turn animation between steps is one-sided. Streamlit rebuilds the DOM on each rerun, so the outgoing page cannot be shown rotating away.
- Photos are sent to OpenAI for scoring. Do not point it at anything you would not want processed by a third-party API.

---

## License

MIT — see [LICENSE](LICENSE). Use it, fork it, break it.
