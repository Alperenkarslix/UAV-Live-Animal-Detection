# UAV Live Animal Detection

UAV (İnsansız Hava Aracı) kameralarıyla yaban hayatı tespit, takip ve konum görselleştirme sistemi.
Canlı video üzerinde hayvanları YOLO26 ile tespit eder; haritadan girilen kamera/hayvan GPS
koordinatlarını piksele eşler ve kamera FOV dışındaki hayvanları okla + mesafeyle gösterir.

```
┌────────────────────┐    POST /api/state/build    ┌───────────────────┐
│  React + MapLibre  │ ─────────────────────────►  │     FastAPI       │
│   web/ (Vite)      │ ◄───────────────────────── │ src/uav/api/...   │
└────────────────────┘     WS /ws/state           └───────────────────┘
                                                          │
                              ┌───────────────────────────┤
                              ▼                           ▼
                       ┌─────────────┐            ┌──────────────┐
                       │  SQLite     │ ◄─sync──►  │  output.json │
                       │  (uav.db)   │            └──────────────┘
                       └─────────────┘                   │
                                                         ▼
                                              ┌────────────────────┐
                                              │  videoproc_*.py    │
                                              │  (OpenCV + YOLO26) │
                                              └────────────────────┘
```

---

## Özellikler

- **Fine-tuned YOLO26** — 6 Afrika safari hayvanı üzerinde eğitilmiş (mAP50 = **0.911**)
  `Elephant`, `Giraffe`, `Impala`, `Lechwe`, `Tsessebe`, `Zebra`
- **Gerçek-zamanlı takip** — ByteTrack ile kalıcı nesne ID'leri
- **GPS → piksel dönüşümü** — Haversine formülüyle kamera çokgen içinde/dışında ayrımı
- **Modern web UI** — React + MapLibre GL JS (vektör harita, dark theme, WebSocket canlı state)
- **FastAPI backend** — REST + WebSocket, Pydantic doğrulama, SQLite kalıcılık, OpenAPI docs (`/docs`)
- **Apple Silicon hızlandırma** — CoreML export (Neural Engine) veya PyTorch MPS
- **Otomatik video yönü** — portre çekimler otomatik yatay döndürülür

---

## Tech Stack

**Backend:** Python 3.11 · FastAPI · Pydantic v2 · SQLite (WAL) · Ultralytics YOLO26 · OpenCV · Shapely
**Frontend:** TypeScript · React 19 · Vite 6 · Tailwind CSS v4 · MapLibre GL JS
**Tooling:** uv · ruff · pytest · just · pre-commit · direnv

---

## Kurulum

### Gereksinimler

```bash
# Apple Silicon (önerilen)
brew install uv just direnv node@24
```

Linux/Windows: [`uv`](https://docs.astral.sh/uv/) ve [`just`](https://just.systems/) için resmi kurulum talimatları.

### Repoyu klonla ve kur

```bash
git clone https://github.com/Alperenkarslix/UAV-Live-Animal-Detection.git
cd UAV-Live-Animal-Detection

just install              # uv sync — Python sanal ortamı + tüm bağımlılıklar (.venv/)
cd web && npm install     # Node bağımlılıkları (web/node_modules/)
```

### Eğitilmiş model ağırlıkları

`yolomodel/` artık git ile dağıtılmıyor (313 MB). Modeli almak için:

- **Kendin eğit:** `yolo_train.ipynb` (Kaggle/Colab, 2× T4, ~1 saat)
- **Dışarıdan indir:** Releases sayfası veya proje yöneticisinden iste
- **Sadece test:** COCO baseline `yolo26n.pt` repo'da bulunuyor (`UAV_MODEL=yolo26n.pt`)

İndirilen ağırlıkları `yolomodel/yolo26_animals/weights/best.pt` yoluna yerleştir veya `UAV_MODEL` ile yolu belirt.

### (opsiyonel) direnv

```bash
cp .envrc.example .envrc
direnv allow              # her cd'de .venv otomatik aktif olur
```

---

## Kullanım

```bash
# Yeni stack (önerilen)
just dev                  # FastAPI :8000 (REST + WebSocket)
just web-dev              # Vite dev :5173 → tarayıcıda http://localhost:5173

# Klasik OpenCV pipeline'ı
just video                # videoproc_video.py — testvideo.mp4 üstünde
just realtime             # videoproc_realtime.py — webcam
just simulate             # rastgele GPS jitter (canlı UAV yokken)

# Komple komut listesi
just --list
```

OpenCV penceresinde: **`y`** YOLO inference aç/kapa, **`q`** çık.

### API uç noktaları

| Method | Path | Açıklama |
|---|---|---|
| `GET` | `/healthz` | Sağlık kontrolü |
| `GET` | `/api/state` | Mevcut world-state (404 = boş) |
| `POST` | `/api/state/build` | Hayvan + kamera koordinatlarından state oluştur |
| `POST` | `/api/state/camera` | Sadece kamera çokgenini güncelle |
| `WS` | `/ws/state` | Snapshot + canlı update push |

Legacy uyumluluk için `/sonuc`, `/get_data`, `/save_coordinates` rotaları da çalışmaya devam ediyor.
İnteraktif dökümantasyon: http://localhost:8000/docs

---

## Yapılandırma

Tüm parametreler `UAV_*` ortam değişkenleri ile (kaynak: `src/uav/core/config.py`).

| Değişken | Default | Açıklama |
|---|---|---|
| `UAV_MODEL` | `yolomodel/yolo26_animals/weights/best.pt` | Model yolu (`.pt`, `.onnx`, `.mlpackage`) |
| `UAV_CONF` | `0.4` | Confidence eşiği |
| `UAV_IMGSZ` | `640` | Inference görüntü boyutu |
| `UAV_DEVICE` | *(auto)* | `cpu`, `mps`, `0` (cuda:0) |
| `UAV_STRIDE` | `1` | Her N frame'de bir YOLO çalıştır |
| `UAV_VIDEO` | `videos/testvideo.mp4` | Video dosyası yolu |
| `UAV_CAM` | `0` | Webcam index |
| `UAV_API_HOST` | `127.0.0.1` | FastAPI host |
| `UAV_API_PORT` | `8000` | FastAPI port |
| `UAV_DB_PATH` | `uav.db` | SQLite veritabanı yolu |

### Apple Silicon hızlandırma

```bash
# 1. CoreML'e export (Neural Engine — en hızlı)
uv run python scripts/export_coreml.py
UAV_MODEL=yolomodel/yolo26_animals/weights/best.mlpackage just video

# 2. veya PyTorch MPS
UAV_DEVICE=mps just video

# 3. Benchmark karşılaştırma
uv run python scripts/benchmark.py videos/testvideo.mp4 --device mps
```

### Yaygın senaryolar

```bash
# Küçük/uzak hayvanlar için yüksek çözünürlük + düşük eşik
UAV_CONF=0.3 UAV_IMGSZ=960 just video

# Farklı bir video, daha az inference
UAV_VIDEO=videos/safari.mp4 UAV_STRIDE=3 just video

# COCO baseline karşılaştırması (Afrika hayvanlarında zayıf!)
UAV_MODEL=yolo26n.pt just video
```

---

## Geliştirme

```bash
just check                # ruff lint + format check + pytest (89% coverage)
just fix                  # ruff auto-fix + format
just test                 # sadece testler (kapsama raporlu)
just test-fast            # slow / yolo / integration etiketli olanları atla
```

`pre-commit install` ile her commit öncesi ruff otomatik çalışır.

### Proje yapısı

```
src/uav/                 # Yeni Python paketi
  core/                  # config, geo, dataset (saf — bağımsız)
  db/                    # WorldStateRepository + output.json mirror
  api/                   # FastAPI app, REST, WebSocket, state-bus
  inference/             # (yer tutucu — Faz 2)
scripts/
  export_coreml.py       # YOLO → CoreML
  benchmark.py           # ms/frame + FPS profili
web/                     # React + Vite + MapLibre frontend
tests/                   # pytest (geo, repository, REST, WS)

# --- Henüz src/uav/ altına taşınmamış legacy dosyalar ---
config.py                # eski config (artık src/uav/core/config.py'ye yönlendirme şart değil)
video_common.py          # OpenCV + YOLO yardımcıları
videoproc_video.py       # video → overlay + YOLO
videoproc_realtime.py    # webcam → overlay + YOLO
simulate_movement.py     # rastgele hayvan hareketi
web_app.py               # eski Flask UI (ileride emekliye)
yolo_test_*.py           # bağımsız YOLO testleri
templates/               # eski Yandex Maps şablonları
yolo_train.ipynb         # Kaggle/Colab fine-tune notebook'u
```

---

## Yol Haritası

`ROADMAP.md` 0–8 fazını listeliyor. Mevcut durum:

- ✅ **Faz 0** — Temel sağlamlaştırma
- ✅ **Faz 1.2** — ByteTrack tracking
- 🟡 **Faz 3.2 kısmen** — FastAPI + WebSocket + MapLibre (bu commit)
- 🔜 **Faz 2.1** — `cv2.getPerspectiveTransform` ile homografi (en büyük doğruluk kazancı)
- 🔜 **Faz 4.1** — PostgreSQL + PostGIS (mekânsal sorgular, geo-fencing)
- 🔜 **Faz 5.1** — Edge inference (Jetson + TensorRT veya CoreML INT8)

---

## Model Eğitimi

Detaylı akış için `yolo_train.ipynb`'a bak.

**Kaggle özet (2× T4, ~1 saat):**
1. Yeni notebook → `yolo_train.ipynb`'ı yükle
2. Settings → GPU T4 x2, Internet On
3. Tüm hücreleri çalıştır
4. Sağ paneldeki **Output** → `yolo26_animals.zip` indir
5. `unzip -o yolo26_animals.zip -d yolomodel/`

**Sınıf bazında mAP50:**

| Sınıf | mAP50 |
|---|---|
| Lechwe | 0.966 |
| Giraffe | 0.951 |
| Impala | 0.942 |
| Tsessebe | 0.929 |
| Elephant | 0.885 |
| Zebra | 0.792 |
| **Ortalama** | **0.911** |

Inference: ~3 ms/frame (T4), ~10–30 ms/frame (M-serisi MPS), ~5–15 ms/frame (M-serisi CoreML).

---

## Katkı

Fork → branch → pull request. `just check` geçmesi şart.

## İletişim

- Anıl Taha ADAK — tahaadak94@gmail.com
- Alperen KARSLI — alperenkarsliceng@gmail.com
- Asil FINDIK — asilfndk@gmail.com

**Akademik Danışman:** Doç. Dr. Fatih AYDIN
**Endüstri Danışmanı:** Dr. Muhterem Özgür KIZILKAYA
