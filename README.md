# simulate-quake (Legacy Array)

ปล่อยเหตุการณ์แผ่นดินไหวจำลอง **ทุก 1 นาที** ในฟอร์แมต array ที่ SafeQuake ใช้ได้ทันที

## Pages URL
- https://<YOUR-USERNAME>.github.io/simulate-quake/quake.json
- สำหรับ repo นี้: https://chael-bb.github.io/simulate-quake/quake.json

## เปิด GitHub Pages
Settings → **Pages** → Build and deployment = **GitHub Actions**  
(มี workflow ที่ `.github/workflows/deploy-pages.yml` แล้ว)

## Run uploader
### Windows (PowerShell)
```powershell
$env:GITHUB_TOKEN="ใส่โทเคนถ้าใช้ --token-push"
$env:GITHUB_REPO="Chael-BB/simulate-quake"
python scripts\quake_uploader.py --interval 60 --branch main --keep 120 --token-push
