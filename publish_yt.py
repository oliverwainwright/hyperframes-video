#!/usr/bin/env python3
import os, json, time, urllib.request, urllib.error

API = "https://backend.blotato.com/v2"
KEY = os.environ["BLOTATO_API_KEY"]
VIDEO = "/home/ow/projects/hyperframes-video/unretired-medicare-income.mp4"
ACCOUNT = "28636"  # TheUnRetiredpreneur

TITLE = "October 15 Isn't Just Medicare Day"
DESC = (
    "Everyone 55+ is about to review their Medicare plan during Open Enrollment "
    "(Oct 15–Dec 7). Spend 30 minutes reviewing your INCOME plan too.\n\n"
    "Enrollment protects your future — so does one paid skill. This season, enroll "
    "yourself in ONE income idea: pick a skill you already have, name a price, tell 5 people.\n\n"
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

# 1. request upload slot
st, up = req("POST", f"{API}/media/uploads", {"filename": "unretired-medicare-income.mp4"})
print("upload slot:", st)
pre, pub = up["presignedUrl"], up["publicUrl"]

# 2. PUT file to presigned url
with open(VIDEO, "rb") as f:
    body = f.read()
put = urllib.request.Request(pre, data=body, method="PUT")
put.add_header("Content-Type", "video/mp4")
for attempt in range(3):
    try:
        with urllib.request.urlopen(put, timeout=300) as resp:
            print("PUT:", resp.status); break
    except Exception as e:
        print("PUT retry", attempt, e); time.sleep(3)

# confirm reachable
st, _ = req("GET", pub) if False else (None, None)
chk = urllib.request.Request(pub, method="GET")
try:
    with urllib.request.urlopen(chk, timeout=60) as resp:
        print("public reachable:", resp.status)
except urllib.error.HTTPError as e:
    print("public reachable:", e.code)

# 3. publish immediately (public, AI media flagged)
payload = {"post": {
    "accountId": ACCOUNT,
    "content": {"text": DESC, "mediaUrls": [pub], "platform": "youtube"},
    "target": {
        "targetType": "youtube",
        "title": TITLE,
        "privacyStatus": "public",
        "shouldNotifySubscribers": True,
        "isMadeForKids": False,
        "containsSyntheticMedia": True,
    },
}}
st, res = req("POST", f"{API}/posts", payload)
print("publish:", st, res)
sid = res.get("postSubmissionId")
if not sid:
    print("NO SUBMISSION ID — aborting"); raise SystemExit(1)

# 4. poll
for i in range(40):
    time.sleep(6)
    st, s = req("GET", f"{API}/posts/{sid}")
    status = s.get("status") or s.get("state")
    print(f"poll {i}: {status}")
    if status in ("published", "completed", "success"):
        print("PUBLISHED:", json.dumps(s)); break
    if status in ("failed", "error"):
        print("FAILED:", json.dumps(s)); break
else:
    print("still pending, submissionId:", sid)
