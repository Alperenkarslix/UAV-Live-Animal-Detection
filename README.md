# UAV Live Animal Detection

UAV (Unmanned Aerial Vehicle) kameralarıyla yaban hayatı tespit, takip ve konum görselleştirme sistemi. Uçuş sırasındaki canlı görüntüde hayvanları YOLO26 ile tespit eder; bir harita üzerinden girilen kamera/hayvan GPS koordinatlarını pikselle eşler ve kamera görüş açısı dışındaki hayvanları okla + mesafeyle gösterir.

---

## Özellikler

- **Fine-tuned YOLO26** — 6 Afrika safari hayvanı üzerinde eğitilmiş (mAP50 = **0.911**)
  - `Elephant`, `Giraffe`, `Impala`, `Lechwe`, `Tsessebe`, `Zebra`
- **Gerçek-zamanlı takip** — ByteTrack ile kalıcı nesne ID'leri
- **GPS → piksel dönüşümü** — Haversine formülüyle kamera çokgen içinde/dışında ayrımı
- **Web tabanlı simülasyon** — Flask + Yandex Maps ile hayvan/kamera koordinatları
- **Otomatik video yönü** — portre çekimler otomatik yatay döndürülür

---

## Kurulum

```bash
git clone https://github.com/Alperenkarslix/UAV-Live-Animal-Detection.git
cd UAV-Live-Animal-Detection

python3 -m venv env
source env/bin/activate           # Windows: env\Scripts\activate

pip install -r requirements.txt
```

### Fine-tuned ağırlıklar

Mevcut repoda `yolomodel/yolo26_animals/weights/best.pt` (~19 MB) bulunur. Kendin eğitmek istersen `yolo_train.ipynb`'ı aç (Kaggle / Colab / local).

---

## Kullanım

### 1) Web arayüzünden koordinat oluştur

```bash
python web_app.py
```
→ `http://localhost:5000` → hayvan sayısını gir, haritaya marker yerleştir, kamera dikdörtgenini sürükle, **Kaydet** → `output.json` oluşur.

### 2) (opsiyonel) Hayvan hareketini simüle et

```bash
python simulate_movement.py
```
`output.json`'daki koordinatları küçük rastgele ofsetlerle günceller. Canlı UAV akışı yokken görsel doğrulama için kullanışlı.

### 3) Video / webcam üzerinden tespit

```bash
# Kaydedilmiş video üzerinden
python videoproc_video.py

# Canlı webcam'den
python videoproc_realtime.py
```
Pencere açıldığında **`y`** → YOLO aç/kapa, **`q`** → çık.

---

## Yapılandırma

Tüm değerler `config.py` içinde, ortam değişkeniyle override edilebilir:

| Değişken | Default | Açıklama |
|---|---|---|
| `UAV_MODEL` | `yolomodel/yolo26_animals/weights/best.pt` | Model yolu |
| `UAV_CONF` | `0.4` | Confidence eşiği |
| `UAV_IMGSZ` | `640` | Inference görüntü boyutu |
| `UAV_DEVICE` | *(auto)* | `cpu` / `mps` / `0` (cuda:0) |
| `UAV_STRIDE` | `1` | Her N frame'de bir YOLO çalışsın |
| `UAV_VIDEO` | `videos/testvideo.mp4` | Video dosyası yolu |
| `UAV_CAM` | `0` | Webcam index |

**Örnek kullanımlar:**

```bash
# Apple Silicon'da MPS hızlandırması
UAV_DEVICE=mps python videoproc_realtime.py

# Küçük nesneler için yüksek çözünürlük + düşük eşik
UAV_CONF=0.3 UAV_IMGSZ=960 python videoproc_video.py

# Farklı bir video denemek
UAV_VIDEO=videos/safari.mp4 python videoproc_video.py

# COCO baseline karşılaştırması (Afrika hayvanlarında çok zayıftır!)
UAV_MODEL=yolo26s.pt python videoproc_video.py
```

---

## Model Eğitimi

Detaylı Kaggle/Colab akışı için `yolo_train.ipynb`'a bak.

**Hızlı özet (Kaggle, 2× T4 ücretsiz, ~1 saat):**
1. Kaggle'da yeni notebook → `yolo_train.ipynb`'ı yükle
2. Settings → Accelerator: **GPU T4 x2**, Internet: **On**
3. Tüm hücreleri çalıştır
4. Bitince sağ paneldeki **Output** sekmesinden `yolo26_animals.zip` indir
5. `unzip -o yolo26_animals.zip -d yolomodel/`

Repo'daki mevcut model zaten bu akışla eğitildi:

| Sınıf | mAP50 |
|---|---|
| Lechwe | 0.966 |
| Giraffe | 0.951 |
| Impala | 0.942 |
| Tsessebe | 0.929 |
| Elephant | 0.885 |
| Zebra | 0.792 |
| **Ortalama** | **0.911** |

Inference: ~3ms/frame (T4).

---

## Proje Yapısı

```
.
├── config.py                  # Merkezi yapılandırma + env var override
├── web_app.py                 # Flask: harita → output.json
├── simulate_movement.py       # output.json için hayvan hareket simülatörü
├── video_common.py            # Paylaşılan helper'lar (YOLO, overlay, cache)
├── videoproc_video.py         # Video dosyasından YOLO + overlay
├── videoproc_realtime.py      # Webcam'den YOLO + overlay
├── yolo_test_video.py         # Bağımsız YOLO tester (video)
├── yolo_test_realtime.py      # Bağımsız YOLO tester (webcam)
├── yolo_train.ipynb           # Kaggle/Colab/Local YOLO26 fine-tune notebook
├── yolomodel/                 # Eğitilmiş ağırlıklar (best.pt, best.onnx, .mlpackage)
├── templates/                 # Flask şablonları (index.html, sonuc.html)
├── videos/                    # Örnek girdi videoları
├── output.json                # Kamera çokgeni + hayvan koordinatları (paylaşılan durum)
├── requirements.txt
└── ROADMAP.md                 # Geliştirme fazları
```

---

## Yol Haritası

Sonraki geliştirme fazları (`ROADMAP.md`'e bak):
- Homografi tabanlı gerçek piksel ↔ GPS eşlemesi
- WebSocket ile canlı video yayını
- PostGIS ile kalıcı iz / ısı haritası
- Edge deployment (Jetson/RPi, Docker)
- LLM ile saha raporu üretimi

---

## Katkı

Fork et, branch aç, pull request gönder.

## İletişim

- Anıl Taha ADAK — tahaadak94@gmail.com
- Alperen KARSLI — alperenkarsliceng@gmail.com
- Asil FINDIK — asilfndk@gmail.com

**Akademik Danışman:** Doç. Dr. Fatih AYDIN
**Endüstri Danışmanı:** Dr. Muhterem Özgür KIZILKAYA
