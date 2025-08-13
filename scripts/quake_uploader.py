#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simulate-Quake Uploader (LEGACY ARRAY FORMAT) — Significance-Matched
- เขียน dist/quake.json เป็นลิสต์เหตุการณ์ [ {...}, {...}, ... ] โดยใส่รายการใหม่ไว้บนสุด
- "สุ่มทั้งมีและไม่มีสึนามิ" ตามสัดส่วน --tsu-ratio (ดีฟอลต์ 0.5)
- ทุกเหตุการณ์จะถูก "คัด" ด้วย heuristic significance ให้ผ่านเกณฑ์ --target (ดีฟอลต์ 230)
- commit + push → GitHub Actions deploy -> GitHub Pages

การยืนยันตัวตน:
- ใช้ credential ปกติ หรือ
- ตั้ง env: GITHUB_TOKEN และ GITHUB_REPO แล้วใส่ --token-push
"""

import argparse
import json
import math
import os
import random
import string
import subprocess
import sys
import time
from datetime import datetime, timezone
from math import cos, radians

# -----------------------------
# ค่าตั้งต้น
# -----------------------------
DEFAULT_BRANCH = "main"
DEFAULT_INTERVAL_SEC = 60
DEFAULT_KEEP = 120            # เก็บเหตุการณ์ล่าสุดกี่รายการ
DEFAULT_TARGET = 230.0        # เกณฑ์ significance (ยืดหยุ่นตามแอปรับจริง)
DEFAULT_TSU_RATIO = 0.5       # โอกาสเป็น tsunami event (0.0 - 1.0)
DEFAULT_MAX_TRIES = 25        # จำนวนครั้งสูงสุดในการสุ่มให้ทะลุเป้า

# พิกัดอ้างอิงผู้ใช้ (ให้คะแนนขึ้นกับระยะทางจากผู้ใช้)
BKK_LAT, BKK_LON = 13.86, 100.52

# -----------------------------
# Utils
# -----------------------------
def iso_now_utc():
    # มี timezone +00:00 แบบตัวอย่าง
    return datetime.now(timezone.utc).isoformat()

def rand_id(prefix="sim"):
    salt = "".join(random.choices(string.digits, k=6))
    return f"{prefix}-{salt}"

def jitter_deg(lat, km_lat=10.0, km_lon=10.0):
    """ ขยับ lat/lon เป็นกิโลเมตร -> องศา (ประมาณการ) """
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
            return data if isinstance(data, list) else []
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

# -----------------------------
# Distance & Significance Heuristic
# -----------------------------
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlmb/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def heuristic_significance(mag: float, dist_km: float, tsunami: bool) -> float:
    """
    แบบจำลองคะแนน (ใกล้เคียงแนวคิดในแอป: magnitude↑, distance↓, tsunami bonus)
    ปรับค่าคงที่ได้ด้วย --target เพื่อแมทช์พฤติกรรมจริงใน SafeQuake
    """
    # term ของ magnitude ขึ้นแรงแบบกำลัง (ให้ M7+ เด้งชัด)
    mag_term = (mag ** 3) * 1.05          # ~350–500+ เมื่อ M~7–8
    # ระยะทางลดคะแนนแบบลอการิทึม (ไม่ให้ 1–10 km โดดเวอร์เกิน)
    dist_term = -35.0 * math.log10(dist_km + 1.0)
    # โบนัสสึนามิ (ทดสอบสายทะเล)
    tsu_term = 120.0 if tsunami else 0.0
    return mag_term + dist_term + tsu_term

# -----------------------------
# Scenarios (ตัวสร้าง candidate)
# -----------------------------
def inland_thailand_candidate():
    """ เหตุการณ์ในแผ่นดินไทย (ทดสอบ shake) """
    base_lat, base_lon = 15.5, 101.8
    dlat, dlon = jitter_deg(base_lat, km_lat=150, km_lon=150)
    lat = round(base_lat + dlat, 4)
    lon = round(base_lon + dlon, 4)
    # แมกนิจูดค่อนสูงเพื่อให้ผ่านเกณฑ์ง่ายขึ้น
    mag = round(random.uniform(6.9, 8.2), 1)
    depth = round(random.uniform(8.0, 28.0), 1)
    return {"place": "Simulated (Inland Thailand)", "lat": lat, "lon": lon,
            "magnitude": mag, "depth": depth, "tsunami": False}

def andaman_candidate():
    """ เหตุการณ์ทะเลอันดามัน (ทดสอบ tsunami) """
    base_lat, base_lon = 8.2, 97.2
    dlat, dlon = jitter_deg(base_lat, km_lat=160, km_lon=160)
    lat = round(base_lat + dlat, 4)
    lon = round(base_lon + dlon, 4)
    mag = round(random.uniform(7.2, 8.6), 1)  # ทะเลให้แมกนิจูดสูงกว่า
    depth = round(random.uniform(8.0, 30.0), 1)
    return {"place": "Simulated (Andaman Sea)", "lat": lat, "lon": lon,
            "magnitude": mag, "depth": depth, "tsunami": True}

def build_event(obj):
    return {
        "id": rand_id("sim"),
        "magnitude": obj["magnitude"],
        "depth": obj["depth"],
        "lat": obj["lat"],
        "lon": obj["lon"],
        "place": obj["place"],
        "time": iso_now_utc(),
        "tsunami": obj["tsunami"]
    }

def sample_significance_matched(tsunami_first: bool, target: float, max_tries: int):
    """
    พยายามสุ่ม candidate แล้วคัดให้คะแนน >= target
    ถ้าไม่ถึงเป้า จะค่อยๆ ดันแมกนิจูด/เข้าใกล้ผู้ใช้มากขึ้น
    """
    for i in range(max_tries):
        if tsunami_first:
            cand = andaman_candidate()
        else:
            cand = inland_thailand_candidate()

        dist = haversine_km(BKK_LAT, BKK_LON, cand["lat"], cand["lon"])
        score = heuristic_significance(cand["magnitude"], dist, cand["tsunami"])

        if score >= target:
            return build_event(cand)

        # ปรับเพิ่มความแรง/เข้าใกล้ แล้วลองใหม่
        #  - สำหรับ inland: เพิ่ม mag เล็กน้อย และดึงเข้าหา BKK
        #  - สำหรับ tsunami: เพิ่ม mag ให้แรงขึ้น
        if not cand["tsunami"]:
            # ดึงตำแหน่งเข้าใกล้กทม. ~20–60 กม.
            dlat, dlon = jitter_deg(BKK_LAT, km_lat=60, km_lon=60)
            cand["lat"] = round(BKK_LAT + dlat, 4)
            cand["lon"] = round(BKK_LON + dlon, 4)
            cand["magnitude"] = round(min(8.7, cand["magnitude"] + random.uniform(0.2, 0.5)), 1)
        else:
            cand["magnitude"] = round(min(8.9, cand["magnitude"] + random.uniform(0.2, 0.4)), 1)

    # ถ้ามีเหตุสุดวิสัยยังไม่ถึงเป้า ให้ยิง "ค้อนใหญ่" เพื่อการันตี
    if tsunami_first:
        fallback = {"place": "Simulated (Andaman Sea)", "lat": 8.4, "lon": 97.1,
                    "magnitude": 8.6, "depth": 12.0, "tsunami": True}
    else:
        fallback = {"
