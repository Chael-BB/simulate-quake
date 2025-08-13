# quake_uploader.py
import json
import random
import time
import datetime
import subprocess
import os

# === CONFIG ===
file_path = "quake.json"
interval_seconds = 60  # ส่งทุก 1 นาที (60 วินาที)

def random_quake():
    now = datetime.datetime.utcnow()
    quake_id = f"sim_{now.strftime('%Y%m%d%H%M%S')}"
    quake = {
        "id": quake_id,
        "source": "simulate",
        "location": random.choice(["Bangkok", "Chiang Mai", "Phuket", "Tokyo", "Jakarta"]),
        "lat": round(random.uniform(-90, 90), 4),
        "lon": round(random.uniform(-180, 180), 4),
        "magnitude": round(random.uniform(4.5, 8.9), 1),
        "depth": random.randint(5, 70),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "tsunamiWarning": random.choice(["yes", "no"])
    }
    return quake

def safe_load_quakes(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            # ถ้าไฟล์เสีย/อ่านไม่ได้ ให้เริ่ม list ใหม่
            return []
    return []

def git_push(path, message):
    # ถ้าไม่มี git repo จะ error — ปล่อยให้ผ่านไปเพื่อไม่ให้ลูปหยุด
    try:
        subprocess.run(["git", "add", path], check=False)
        subprocess.run(["git", "commit", "-m", message], check=False)
        subprocess.run(["git", "push"], check=False)
    except Exception as e:
        print(f"⚠️ Git push error: {e}", flush=True)

def main():
    print("🚀 Quake uploader started (every 60s). Press Ctrl+C to stop.\n", flush=True)

    while True:
        loop_start = time.monotonic()  # ใช้ monotonic เพื่อความเที่ยงตรงของ interval

        # 1) โหลด quake.json เดิม (ถ้ามี)
        quake_list = safe_load_quakes(file_path)

        # 2) เพิ่ม quake ใหม่
        new_quake = random_quake()
        quake_list.append(new_quake)

        # 3) เขียนไฟล์
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(quake_list, f, indent=2, ensure_ascii=False)

        # 4) Git push
        commit_msg = f"Add {new_quake['id']}"
        git_push(file_path, commit_msg)

        # 5) Log
        print(
            f"✅ Pushed: {new_quake['id']} | M{new_quake['magnitude']} | {new_quake['location']} "
            f"| {new_quake['date']} {new_quake['time']}Z",
            flush=True
        )

        # 6) คำนวณเวลาที่เหลือให้ครบ 60 วินาทีพอดี
        elapsed = time.monotonic() - loop_start
        sleep_sec = max(0.0, interval_seconds - elapsed)
        print(f"⏳ Waiting {sleep_sec:.1f} sec...\n", flush=True)
        time.sleep(sleep_sec)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Stopped by user.", flush=True)
