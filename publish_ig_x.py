#!/usr/bin/env python3
import os, json, time, urllib.request, urllib.error

API = "https://backend.blotato.com/v2"
KEY = os.environ["BLOTATO_API_KEY"]
VIDEO = "/home/ow/projects/hyperframes-video/unretired-medicare-income.mp4"

# X caption (more hashtags OK); IG caption capped at 5 hashtags
CAPTION = (
    "Everyone 55+ is about to review their Medicare plan (Open Enrollment Oct 15\u2013Dec 7). "
    "Spend 30 minutes on your INCOME plan too.\n\n"
    "Enrollment protects your future \u2014 so does one paid skill. This season, enroll yourself "
    "in ONE income idea: pick a skill you already have, name a price, tell 5 people.\n\n"
    "DM \"AUDIT\" for the 1-page skills-to-income checklist.\n\n"
    "#UnRetired #SecondAct #RetirementIncome #Seniors #SideIncome"
)

def req(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("blotato-api-key", KEY)
    if data: r.add_header("Content-Type", "application/json")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(r, timeout=120) as resp:
                return resp.status, json.loads(resp.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception as e:
            if attempt == 2: raise
            time.sleep(3)

# 1. upload once
st, up = req("POST", f"{API}/media/uploads", {"filename": "unretired-medicare-income.mp4"})
print("upload slot:", st)
pre, pub = up["presignedUrl"], up["publicUrl"]
with open(VIDEO, "rb") as f: body = f.read()
put = urllib.request.Request(pre, data=body, method="PUT")
put.add_header("Content-Type", "video/mp4")
for attempt in range(3):
    try:
        with urllib.request.urlopen(put, timeout=300) as resp:
            print("PUT:", resp.status); break
    except Exception as e:
        print("PUT retry", attempt, e); time.sleep(3)
chk = urllib.request.Request(pub, method="GET")
try:
    with urllib.request.urlopen(chk, timeout=60) as resp:
        print("public reachable:", resp.status)
except urllib.error.HTTPError as e:
    print("public reachable:", e.code)

# 2. targets
posts = [
    {"name": "instagram", "payload": {"post": {
        "accountId": "24448",
        "content": {"text": CAPTION, "mediaUrls": [pub], "platform": "instagram"},
        "target": {"targetType": "instagram", "mediaType": "reel", "shareToFeed": True},
    }}},
    {"name": "twitter", "payload": {"post": {
        "accountId": "13231",
        "content": {"text": CAPTION, "mediaUrls": [pub], "platform": "twitter"},
        "target": {"targetType": "twitter"},
    }}},
]

subs = {}
for p in posts:
    st, res = req("POST", f"{API}/posts", p["payload"])
    print(f"publish {p['name']}: {st} {res}")
    sid = res.get("postSubmissionId")
    if sid: subs[p["name"]] = sid

# 3. poll all
results = {}
for i in range(45):
    time.sleep(6)
    done = True
    for name, sid in subs.items():
        if name in results: continue
        st, s = req("GET", f"{API}/posts/{sid}")
        status = s.get("status") or s.get("state")
        print(f"poll {i} {name}: {status}")
        if status in ("published", "completed", "success"):
            results[name] = s.get("publicUrl", "published")
        elif status in ("failed", "error"):
            results[name] = "FAILED: " + json.dumps(s)
        else:
            done = False
    if len(results) == len(subs): break

print("\n=== FINAL ===")
for name, sid in subs.items():
    print(name, "->", results.get(name, "still pending, sid=" + sid))
