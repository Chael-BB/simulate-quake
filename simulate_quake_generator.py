import json, random, time, datetime, subprocess, os

# === CONFIG ===
file_path = "quake.json"
push_interval_min = 1  # นาที
push_interval_max = 5  # นาที

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

while True:
    # โหลด quake.json เดิม หรือเริ่มใหม่
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                quake_list = json.load(f)
            except:
                quake_list = []
    else:
        quake_list = []

    # เพิ่ม quake ใหม่
    new_quake = random_quake()
    quake_list.append(new_quake)

    with open(file_path, "w") as f:
        json.dump(quake_list, f, indent=2)

    # Git push
    subprocess.run(["git", "add", file_path])
    subprocess.run(["git", "commit", "-m", f"Add {new_quake['id']}"])
    subprocess.run(["git", "push"])

    print(f"✅ Pushed: {new_quake['id']} | M{new_quake['magnitude']} | {new_quake['location']}")
    wait_sec = random.randint(push_interval_min * 60, push_interval_max * 60)
    print(f"⏳ Waiting {wait_sec} sec...\n")
    time.sleep(wait_sec)
