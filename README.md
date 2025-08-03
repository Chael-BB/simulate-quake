# simulate-quake

A simulation data source for earthquake events, used for testing the **SafeQuake** app alert system.

## 🔧 What is this?

This repository provides simulated earthquake events for **SafeQuake** to consume via HTTP fetch.  
It's used to test emergency alert logic without relying on real-time seismic feeds.

## 📂 Files

| File                        | Purpose                                |
|----------------------------|----------------------------------------|
| `quake.json`               | Stores all simulated earthquake events |
| `simulate_quake_generator.py` | Python script to generate new events    |
| `README.md`                | This documentation file                |

---

## 🧪 How to use

### 1. Clone this repo or use raw link:
```bash
git clone https://github.com/Chael-BB/simulate-quake.git
```

Or fetch raw data:
```
https://raw.githubusercontent.com/Chael-BB/simulate-quake/main/quake.json
```

---

### 2. Run generator manually
```bash
python simulate_quake_generator.py
```

Each run appends a new simulated quake into `quake.json`.

---

### 3. Run generator repeatedly (Linux/Mac)
To simulate live data stream every 1–5 minutes:
```bash
watch -n 180 python simulate_quake_generator.py
```

Or use crontab:
```bash
*/3 * * * * /usr/bin/python3 /path/to/simulate_quake_generator.py
```

---

## 🌍 Simulated Event Format

Each event in `quake.json` looks like this:

```json
{
  "id": "sim-1725360505",
  "magnitude": 6.8,
  "depth": 10,
  "lat": 13.75,
  "lon": 100.52,
  "location": "Bangkok, Thailand",
  "utc_time": "2025-08-03T09:15:30Z",
  "source": "simulate"
}
```

---

## ⚠️ Notes

- Events are randomly generated in Southeast Asia region
- SafeQuake app uses these events as a 5th earthquake source
- All `id`s are prefixed with `sim-` and `source = "simulate"` for filtering

---

## 🤖 Author

Developed by [Chael-BB](https://github.com/Chael-BB) for the SafeQuake early warning system.

---

### 🟢 Status: Production-ready for simulation
