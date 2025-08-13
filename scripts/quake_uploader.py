#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simulate-Quake Uploader (LEGACY ARRAY FORMAT)
- เขียน dist/quake.json เป็น "ลิสต์" ของเหตุการณ์ [ {...}, {...}, ... ]
- เติมเหตุการณ์ใหม่ไว้ "บนสุด" และเก็บแค่จำนวนล่าสุดตาม --keep (ดีฟอลต์ 120)
- commit + push ไปยัง branch ที่กำหนด (ดีฟอลต์ main)
- GitHub Actions จะ deploy dist/ ไป Pages อัตโนมัติ
"""

import argparse
import json
import os
import random
import string
import subprocess
import sys
import time
from datetime import datetime, timezone
from math import cos, radians

DEFAULT_BRANCH = "main"
DEFAULT_INTERVAL_SEC = 60
DEFAULT_KEEP = 120   # เก็บเหตุการณ์ล่าสุดกี่รายการ

def iso_now_utc():
    return datetime.now(timezone.utc).isoformat()

def rand_id(prefix="sim"):
    salt = "".join(random.choices(string.digits, k=6))
    return f"{prefix}-{salt}"

def jitter_deg(lat, km_lat=10.0, km_lon=10.0):
    dlat = (km_lat / 111.0) * (random.random() - 0.5) * 2
    denom = 111.0 * max(0.1, cos(radians(lat)))
    dlon = (km_lon / denom) * (random.random() - 0.5) * 2
    return dlat, dlon

def load_legacy_array(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []

def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def run(cmd, cwd=None, check=True):
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return result

def git_commit_and_push(repo_dir, branch, token_push=False):
    run(["git", "add", "dist/quake.json"], cwd=repo_dir)
    msg = f"simulate: update quake.json at {iso_now_utc()}"
    run(["git", "commit", "-m", msg], cwd=repo_dir)
    if token_push:
        repo = os.environ.get("GITHUB_REPO", "")
        token = os.environ.get("GITHUB_TOKEN", "")
        if not repo or not token:
            raise RuntimeError("GITHUB_REPO/GITHUB_TOKEN not set for token push")
        push_url = f"https://{token}@github.com/{repo}.git"
        run(["git", "push", push_url, f"HEAD:{branch}"], cwd=repo_dir)
    else:
        run(["git", "push", "origin", branch], cwd=repo_dir)

# ---------- SCENARIOS ----------
def inland_thailand_strong():
    base_lat, base_lon = 15.5, 101.8
    dlat, dlon = jitter_deg(base_lat, km_lat=150, km_lon=150)
    lat = round(base_lat + dlat, 4)
    lon = round(base_lon + dlon, 4)
    mag = round(random.uniform(7.3, 8.2), 1)
    depth = round(random.uniform(8.0, 28.0), 1)
    return {"place": "Simulated (Inland Thailand)", "lat": lat, "lon": lon,
            "magnitude": mag, "depth": depth, "tsunami": False}

def andaman_tsunami():
    base_lat, base_lon = 8.2, 97.2
    dlat, dlon = jitter_deg(base_lat, km_lat=160, km_lon=160)
    lat = round(base_lat + dlat, 4)
    lon = round(base_lon + dlon, 4)
    mag = round(random.uniform(7.4, 8.6), 1)
    depth = round(random.uniform(8.0, 30.0), 1)
    return {"place": "Simulated (Andaman Sea)", "lat": lat, "lon": lon,
            "magnitude": mag, "depth": depth, "tsunami": True}

def far_big_event():
    base_lat, base_lon = 38.3, 142.4
    dlat, dlon = jitter_deg(base_lat, km_lat=200, km_lon=200)
    lat = round(base_lat + dlat, 4)
    lon = round(base_lon + dlon, 4)
    mag = round(random.uniform(7.8, 8.6), 1)
    depth = round(random.uniform(10.0, 40.0), 1)
    return {"place": "Simulated (NW Pacific, far)", "lat": lat, "lon": lon,
            "magnitude": mag, "depth": depth, "tsunami": False}

SCENARIOS = [
    ("inland", inland_thailand_strong),
    ("andaman", andaman_tsunami),
    ("far_big", far_big_event),
]

def build_event(scn):
    now_iso = iso_now_utc()
    return {
        "id": rand_id("sim"),
        "magnitude": scn["magnitude"],
        "depth": scn["depth"],
        "lat": scn["lat"],
        "lon": scn["lon"],
        "place": scn["place"],
        "time": now_iso,
        "tsunami": scn["tsunami"]
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_SEC,
                    help="วินาทีระหว่างการอัปเดต (ดีฟอลต์ 60)")
    ap.add_argument("--branch", default=DEFAULT_BRANCH, help="branch สำหรับ push (ดีฟอลต์ main)")
    ap.add_argument("--keep", type=int, default=DEFAULT_KEEP,
                    help="เก็บเหตุการณ์ล่าสุดกี่รายการ (ดีฟอลต์ 120)")
    ap.add_argument("--once", action="store_true", help="สร้างเหตุการณ์ครั้งเดียวแล้วออก")
    ap.add_argument("--scenario", choices=[n for n, _ in SCENARIOS],
                    help="บังคับ scenario (inland/andaman/far_big)")
    ap.add_argument("--token-push", action="store_true",
                    help="push ด้วย https://<GITHUB_TOKEN>@github.com/<GITHUB_REPO>.git")
    args = ap.parse_args()

    repo_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    quake_path = os.path.join(repo_dir, "dist", "quake.json")
    idx = 0

    while True:
        if args.scenario:
            scn = dict(SCENARIOS)[args.scenario]()
        else:
            name, fn = SCENARIOS[idx % len(SCENARIOS)]
            scn = fn()
            if idx % 3 == 2:
                scn = andaman_tsunami()

        new_event = build_event(scn)

        arr = load_legacy_array(quake_path)
        arr.insert(0, new_event)
        if len(arr) > args.keep:
            arr = arr[:args.keep]
        write_json(quake_path, arr)

        try:
            git_commit_and_push(repo_dir, args.branch, token_push=args.token_push)
            print("✅ pushed dist/quake.json")
        except Exception as e:
            print(f"❌ push failed: {e}", file=sys.stderr)

        if args.once:
            break

        now = time.time()
        wait = args.interval - (now % args.interval)
        idx += 1
        time.sleep(wait)

if __name__ == "__main__":
    main()
