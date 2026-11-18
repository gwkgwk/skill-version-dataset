"""Recover genuine first-parent Skill updates seeded exclusively by GitSkills.

All downloaded artifacts are inert data. No Skill or repository code is run.
"""
import argparse
import base64
import collections
import concurrent.futures
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath

import requests

ROOT = Path(__file__).resolve().parent
REVISION = "fff3df93beeee51a5444450891751f143e38da3e"
SEED = "gitskills-real-updates-2026-11-18"
LOCAL = threading.local()
LOCK = threading.Lock()
TOKEN = None
CALLS = 0
REMAINING = None
LAST_REQUEST = 0.0


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def git_sha(data, kind="blob"):
    return hashlib.sha1(f"{kind} {len(data)}\0".encode() + data).hexdigest()


def session():
    if not hasattr(LOCAL, "session"):
        s = requests.Session()
        s.proxies.update(urllib.request.getproxies())
        s.headers.update({"User-Agent": "GitSkills-real-update-research", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "Authorization": "Bearer " + TOKEN})
        LOCAL.session = s
    return LOCAL.session


class Unavailable(Exception):
    pass


def api(endpoint, *, cache=True):
    global CALLS, REMAINING, LAST_REQUEST
    assert endpoint.startswith("/") and not endpoint.startswith("//")
    url = "https://api.github.com" + endpoint
    cached = ROOT / "work/http" / (hashlib.sha256(url.encode()).hexdigest() + ".json")
    if cache and cached.exists():
        return json.loads(cached.read_text(encoding="utf-8"))
    for attempt in range(4):
        with LOCK:
            delay = max(0, 0.10 - (time.monotonic() - LAST_REQUEST))
            if delay:
                time.sleep(delay)
            LAST_REQUEST = time.monotonic()
            CALLS += 1
        try:
            response = session().get(url, timeout=(15, 35))
        except requests.RequestException as error:
            if attempt == 3:
                raise Unavailable("network_" + type(error).__name__) from None
            time.sleep(2 ** attempt)
            continue
        if "X-RateLimit-Remaining" in response.headers:
            with LOCK:
                REMAINING = int(response.headers["X-RateLimit-Remaining"])
        if response.status_code in (403, 429) and (response.headers.get("Retry-After") or REMAINING == 0):
            retry = int(response.headers.get("Retry-After", "60"))
            if REMAINING == 0:
                raise Unavailable("github_hourly_rate_limit")
            time.sleep(min(retry, 60))
            continue
        if response.status_code in (500, 502, 503, 504) and attempt < 3:
            time.sleep(2 ** attempt)
            continue
        if response.status_code != 200:
            raise Unavailable("http_" + str(response.status_code))
        result = response.json()
        if cache:
            # Separate threads may share a URL: distinct temporary names avoid clashes.
            cached.parent.mkdir(parents=True, exist_ok=True)
            temporary = cached.with_suffix(f".{threading.get_ident()}.tmp")
            temporary.write_text(json.dumps(result, ensure_ascii=True), encoding="ascii")
            os.replace(temporary, cached)
        return result
    raise Unavailable("retry_exhausted")



def authenticate():
    global TOKEN
    environment = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="Never")
    result = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\nusername=gwkgwk\n\n", capture_output=True, text=True, env=environment, timeout=20)
    fields = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    TOKEN = fields.get("password")
    if not TOKEN:
        raise SystemExit("Existing GitHub login is required; no credential was printed or saved.")
    if api("/user", cache=False)["login"] != "gwkgwk":
        raise SystemExit("Authenticated account mismatch.")

