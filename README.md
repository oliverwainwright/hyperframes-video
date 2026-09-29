# hyperframes-video

A single-video [HyperFrames](https://hyperframes.heygen.com) project: a 30-second vertical (1080×1920) short, authored as plain HTML + GSAP, rendered to MP4 by the HyperFrames CLI, and pushed to YouTube, Instagram and X through the Blotato API.

The video in this repo, **"October 15 Isn't Just Medicare Day"**, is a promo for *The UnRetired Earner* brand. It rides the Medicare Open Enrollment news cycle to pitch a "review your income plan too" message, with a DM-keyword CTA (`AUDIT`).

---

## What it is used for

| Purpose | How |
|---|---|
| **Author a video as code** | The whole video is one `index.html`: DOM elements are the visuals, a GSAP timeline is the animation. |
| **Render deterministically** | HyperFrames seeks the timeline frame by frame and encodes MP4 (H.264 video, AAC audio, 30 fps). No screen recording involved. |
| **Work with AI coding agents** | `AGENTS.md` / `CLAUDE.md` tell an agent which HyperFrames skills to load and which rules keep compositions render-safe. |
| **Distribute** | Two standalone Python scripts upload the finished MP4 to Blotato and publish it to YouTube, Instagram Reels and X. |

---

## Repository layout

```
hyperframes-video-main/
├── index.html                      # The composition: styles, 5 scenes, GSAP timeline
├── package.json                    # npm scripts: dev / check / render / publish (CLI pinned to 0.8.81)
├── hyperframes.json                # HyperFrames project config (registry URL, paths, media proxy)
├── meta.json                       # Project id, name, creation timestamp
├── AGENTS.md  /  CLAUDE.md         # Identical agent instructions (skills, commands, rules)
│
├── bgm.mp3                         # Background music (~192 s, trimmed to 30 s by the composition)
├── ow-headshot-bw.png              # 1024×1024 B&W headshot used in the CTA scene
├── frame_2/8/15/22/27.png          # 1080×1920 still frames sampled from the render (QA snapshots)
├── unretired-medicare-income.mp4   # Rendered output: 30 s, 1080×1920, 30 fps
│
├── publish_yt.py                   # Blotato → YouTube publisher
└── publish_ig_x.py                 # Blotato → Instagram Reel + X publisher
```

---

## Architecture

The project has three layers: **composition**, **render toolchain**, and **distribution**.

```
┌──────────────────────────┐    ┌───────────────────────────┐    ┌──────────────────────────┐
│  1. COMPOSITION          │    │  2. RENDER TOOLCHAIN      │    │  3. DISTRIBUTION         │
│                          │    │                           │    │                          │
│  index.html              │    │  npx hyperframes@0.8.81   │    │  publish_yt.py           │
│   ├─ CSS (scene styles)  │───▶│   ├─ preview  (Studio)    │───▶│  publish_ig_x.py         │
│   ├─ DOM (5 scenes)      │    │   ├─ check    (lint etc.) │    │     │                    │
│   ├─ <audio> (bgm.mp3)   │    │   └─ render   (MP4)       │    │     ▼                    │
│   └─ GSAP master timeline│    │                           │    │  Blotato REST API v2     │
│      window.__timelines  │    │  output: *.mp4            │    │  → YouTube / IG / X      │
└──────────────────────────┘    └───────────────────────────┘    └──────────────────────────┘
```

### 1. Composition (`index.html`)

**Stage.** A single `#stage` div carries the HyperFrames data attributes that define the video:

```html
<div id="stage"
     data-composition-id="root"
     data-start="0" data-duration="30"
     data-width="1080" data-height="1920">
```

**Scenes.** Five absolutely-positioned, full-frame `.scene` divs, all hidden (`opacity: 0; visibility: hidden`) until the timeline reveals them:

| Scene | Window | Role | Key visuals |
|---|---|---|---|
| `#s1` | 0–5 s | Hook | Headline about Medicare review, calendar card ("15 October") |
| `#s2` | 5–11 s | Turn | "Spend 30 minutes on your INCOME plan too", struck-through *Medicare* tag vs. highlighted *Income* tag |
| `#s3` | 11–19 s | Reframe | Two cards: 🛡️ Coverage (protects health) vs 💰 Income (protects freedom, glowing) |
| `#s4` | 19–25 s | The move | Three-item checklist: pick a skill, name a price, tell 5 people |
| `#s5` | 25–30 s | CTA | Headshot, "DM me AUDIT", wordmark *The UnRetired Earner* |

**Design system.** Dark background (`#0a0a0a`), indigo accent (`#6366f1` / `#8b8ef7`), Inter typeface, and a soft radial "glow" element per scene (radial gradients only, as the comments note, rather than full-screen linear gradients).

**Timeline.** One paused GSAP timeline, registered under the composition id:

```js
window.__timelines = window.__timelines || {};
const tl = gsap.timeline({ paused: true });
// ...
window.__timelines["root"] = tl;
```

- Scene start times are constants: `S1=0, S2=5, S3=11, S4=19, S5=25`.
- Scenes hand off with a **0.6 s crossfade** (`XF`): the next scene is set visible at `S_next - XF` while the outgoing one fades via `autoAlpha`.
- Each scene staggers its own elements with `from()` tweens (fade + translate/scale, `power3.out` / `back.out` easing).
- Emphasis loops (`yoyo` + `repeat: 3`) are **finite**, never infinite, so the timeline has a defined end and can be seeked.
- The last scene fades out at 29.5 s.

**Audio.** A single `<audio>` element (`bgm.mp3`, volume 0.55, `data-duration="30"`) sits on track 9. The source file is ~192 s long, so the framework trims it to the 30 s composition window.

**External dependency.** GSAP 3.14.2 is loaded from jsDelivr (`cdn.jsdelivr.net`). Rendering therefore needs network access unless the script is vendored locally.

### 2. Render toolchain (`package.json`, `hyperframes.json`)

There is no build step and no installed dependencies. Every script calls the CLI through `npx --yes hyperframes@0.8.81`, pinned so re-renders stay reproducible.

| Command | What it does |
|---|---|
| `npm run dev` | Foreground Studio preview for a human (blocks until stopped) |
| `npx hyperframes preview --background` | Agent-safe persistent preview (`--status` / `--stop` to manage) |
| `npm run check` | Lint + runtime + layout + motion + contrast checks in one pass |
| `npm run render` | Render the composition to MP4 |
| `npm run publish` | HyperFrames' own publish flow (shareable link) |
| `npx hyperframes docs <topic>` | Offline reference (`data-attributes`, `gsap`, `compositions`, `rendering`, `examples`, `troubleshooting`) |

`hyperframes.json` points at the HyperFrames block registry on GitHub, maps `blocks → compositions`, `components → compositions/components`, `assets → assets`, and enables `media.autoProxy`. Those directories don't exist in this repo yet because the video is a single-file composition with no sub-compositions.

**To upgrade the pinned CLI:**

```bash
npx hyperframes@latest upgrade --project . --check   # preview the delta
npx hyperframes@latest upgrade --project .           # rewrite the pins
```

### 3. Agent layer (`AGENTS.md` / `CLAUDE.md`)

The two files are byte-identical, so Codex-style agents and Claude Code read the same instructions. They:

- Direct the agent to invoke the `/hyperframes` router skill **before** touching a composition. It dispatches to workflows such as `/faceless-explainer`, `/motion-graphics`, `/product-launch-video`, `/slideshow`, `/music-to-video`, `/general-video` and others.
- Require `npm run check` after every edit, with errors fixed before handing work back.
- Encode the framework rules below.

**Key composition rules**

1. Every timed element needs `data-start` and a duration.
2. Timed visuals get `class="clip"`.
3. Register exactly one paused root timeline per composition on `window.__timelines`; child scene timelines must **not** be paused.
4. Videos are `muted`, with a separate `<audio>` element for sound.
5. Sub-compositions are referenced with `data-composition-src`.
6. Logic must be deterministic: no `Date.now()`, no `Math.random()`, no network fetches.

### 4. Distribution scripts

Both scripts are dependency-free Python 3 (stdlib `urllib` only) and share the same flow against **Blotato API v2** (`https://backend.blotato.com/v2`):

```
POST /media/uploads          → returns presignedUrl + publicUrl
PUT  <presignedUrl>          → upload the MP4
GET  <publicUrl>             → confirm the file is reachable
POST /posts                  → create post(s) referencing publicUrl
GET  /posts/{submissionId}   → poll (every 6 s) until published / failed
```

| Script | Targets | Notable settings |
|---|---|---|
| `publish_yt.py` | YouTube | Public, notifies subscribers, `isMadeForKids: false`, `containsSyntheticMedia: true` (AI-content disclosure), custom title + description |
| `publish_ig_x.py` | Instagram Reel (also shared to feed) and X | One upload reused for both posts; shared caption; polls both submissions and prints a final summary |

Shared helper `req()` adds the `blotato-api-key` header, JSON-encodes bodies, and retries transient network failures up to 3 times.

---

## Getting started

**Prerequisites:** Node.js (for `npx`), a network connection (CLI download + GSAP CDN), and Python 3 for publishing.

```bash
# Preview in the HyperFrames Studio
npm run dev

# Validate before rendering
npm run check

# Render to MP4
npm run render
```

**Publishing to social platforms:**

```bash
export BLOTATO_API_KEY="your-key"
python3 publish_yt.py        # YouTube
python3 publish_ig_x.py      # Instagram Reel + X
```

---

## Adapting this project for a new video

1. Edit the copy in the five `.scene` blocks of `index.html`, or add or remove scenes.
2. Update the scene-start constants (`S1…S5`) and `data-duration` on `#stage` and `<audio>` so they agree.
3. Swap `bgm.mp3` and `ow-headshot-bw.png` as needed.
4. Run `npm run check`, then `npm run render`.
5. Update `VIDEO`, `TITLE`, `DESC` / `CAPTION` in the publish scripts.

---

## Things to know

- **Hard-coded paths and IDs.** Both publish scripts use an absolute `VIDEO` path (`/home/ow/projects/hyperframes-video/...`) and fixed Blotato account IDs. Change these on any other machine or account.
- **Secrets.** The API key is read from the `BLOTATO_API_KEY` environment variable and is not stored in the repo. Keep it that way.
- **Publishing is immediate and public.** `publish_yt.py` posts straight to public with subscriber notification; there is no dry-run flag.
- **Time-sensitive content.** The copy references Open Enrollment dates (Oct 15 – Dec 7). Revise it before reusing the video in a different year.
- **Large binaries in the repo.** `bgm.mp3` (~7.7 MB), the rendered MP4 (~4.4 MB) and the headshot (~1.8 MB) account for nearly all of the repo's size. Consider Git LFS or gitignoring rendered output.
- **No `.gitignore`, `README` or `transcript.json`.** This README fills the second gap; `transcript.json` is only generated if captions or narration are added.

