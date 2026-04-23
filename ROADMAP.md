# UAV Live Animal Detection — Geliştirme Yol Haritası

Bu belge, mevcut prototipi (Flask harita + `output.json` + OpenCV overlay + YOLO) saha-kullanılabilir bir ürüne taşımak için önerilen faz planını içerir. Her faz bir önceki fazın üstüne inşa edilir; ara bırakmak iş akışını bozmaz.

---

## Faz 0 — Temel Sağlamlaştırma (tamamlandı ✅)

Bu faz mevcut repoda uygulandı.

- `output.json` için atomic write + dosya kilidi
- Video işleyicilerde frame loop + auto-orient + fit-to-screen
- Kritik hataların düzeltilmesi (ters frame-skip mantığı, yanlış model yolu, asimetrik random, sıfıra bölme)
- Ortak modül (`video_common.py`) ile DRY
- `requirements.txt`, `.gitignore`, debug logları
- 12/12 smoke test geçiyor

---

## Faz 1 — Model Modernizasyonu (1–2 hafta)

**Hedef:** Tespit doğruluğu ve hızı güncel teknolojiyle yükseltmek.

### 1.1 YOLO26'ya geçiş
- `ultralytics >= 8.3` yükselt (YOLO26 desteği).
- Varsayılan model `yolo26n.pt` / `yolo26s.pt` / `yolo26m.pt`.
- Mevcut `best.pt` veri setiyle **transfer learning**: YOLO26 mimarisini fine-tune et.
- Inference'ı tek konfigürasyon üstünden yönet (`config.py` veya `.env`).
- Export: `model.export(format='onnx'|'coreml'|'engine'|'tflite')` ile edge deploy seçenekleri.

### 1.2 Object tracking
- `model.track(..., tracker='bytetrack.yaml')` ile kalıcı hayvan ID'si.
- Hayvanın son N kare trajektörisi overlay'e çizilir.
- ID → `output.json`'daki `animal_coords_*` key'leriyle eşleştir.

### 1.3 Küçük / uzak hayvan
- SAHI (Slicing Aided Hyper Inference) entegrasyonu 4K video için.
- Test-time augmentation (TTA) opsiyonu.

### 1.4 Model değerlendirme
- `model.val()` ile mAP50/mAP50-95 raporu.
- Canlı video üstünde FPS benchmark (`opencv-python` + `time.perf_counter`).

---

## Faz 2 — Gerçek Geometri (2–3 hafta)

**Hedef:** Kadrajdaki hayvanın gerçek dünya koordinatını doğru hesaplamak.

### 2.1 Homografi tabanlı projeksiyon
- `calculate_pixel_coordinates`'i `cv2.getPerspectiveTransform` + `cv2.perspectiveTransform` ile değiştir.
- 4 GPS köşe ↔ 4 piksel köşe eşlemesi → trapez kadraj desteği.

### 2.2 Kamera intrinsik/ekstrinsik
- Kamera kalibrasyonu (`cv2.calibrateCamera`) — bir kerelik.
- Gimbal açıları (pitch/roll/yaw) + İHA irtifası + GPS → tam projeksiyon matrisi.
- Kütüphaneler: `pymap3d`, `pyproj` (geodetic ↔ ENU).

### 2.3 Arazi yüksekliği (DEM)
- SRTM / ASTER GDEM yükle, hayvan noktasındaki yükseklik farkı hesaba kat.
- Dik arazide yataydan farklı 3B mesafe.

### 2.4 Telemetri entegrasyonu
- `pymavlink` ile PX4/ArduPilot, `olympe` ile Parrot, DJI MSDK ile DJI.
- Her karede canlı `lat/lon/alt/pitch/roll/yaw`.
- Manuel "dikdörtgen sürükle" aşaması ihtiyaç dışı kalır.

---

## Faz 3 — Canlı Video + Gerçek Zamanlı UI (2–3 hafta)

**Hedef:** Saha operatörünün canlı izleyip müdahale ettiği bir arayüz.

### 3.1 RTSP / RTMP / WebRTC girişi
- `cv2.VideoCapture("rtsp://...")` + GStreamer backend (low-latency H.264/H.265).
- Parrot ANAFI, DJI Lightbridge, Autel test matrisleri.

### 3.2 Web UI modernizasyonu
- Yandex Maps → **Leaflet + OSM** (açık, offline cache mümkün) veya **MapLibre GL JS** (vektör, 60 FPS).
- Polling (1 Hz) → **WebSocket / SSE** (30 Hz gerçek zamanlı).
- React veya Svelte + Tailwind.
- Canlı video WebRTC ile tarayıcıya (<300 ms gecikme).

### 3.3 Çoklu operatör / çoklu dron
- Redis pub/sub veya Kafka ile event stream.
- Her dron kendi `output.json`'ı yerine merkezi veritabanı (aşağıda).

---

## Faz 4 — Veri Kalıcılığı ve Coğrafi Sorgular (1–2 hafta)

**Hedef:** Tek JSON dosyası yerine ölçeklenebilir depolama.

### 4.1 PostgreSQL + PostGIS
- `observations(id, ts, drone_id, animal_id, species, lat, lon, confidence, frame_uri)`.
- `ST_DWithin`, `ST_Intersects` gibi mekânsal sorgular.
- TimescaleDB hypertable: günlük milyonlarca gözleme dayanıklı.

### 4.2 Geo-fencing
- Milli park sınırları, askeri bölgeler GeoJSON olarak yüklenir.
- Hayvan / İHA yasaklı bölgeye girerse uyarı.

### 4.3 Kayıt + yeniden oynatma
- Ham video + telemetri CSV + tespit logu → S3 / MinIO.
- Web'de "görev oynat" modu, post-flight re-inference.

---

## Faz 5 — Edge & Deploy (2–3 hafta)

**Hedef:** İHA'nın yanında çalışan optimize sistem.

### 5.1 Edge inference
- **Jetson Orin Nano/NX**: TensorRT export, `YOLO('best.engine')`.
- **Coral TPU** veya **Hailo-8**: mobil/dron üstü.
- **Apple Silicon MPS** / **CoreML** export.

### 5.2 Konteynerleştirme
- `Dockerfile` (nvidia/cuda tabanlı).
- `docker-compose`: Flask + simülasyon + PostgreSQL tek komut.
- Helm chart (K8s) çoklu dron SaaS için.

### 5.3 CI/CD
- GitHub Actions: ruff + mypy + pytest + regresyon video testleri.
- `pyproject.toml` + `uv` / `poetry`.

---

## Faz 6 — AI Üst Katman (3+ ay)

**Hedef:** Ham tespitin ötesinde anlam çıkarmak.

### 6.1 Davranış sınıflandırma
- Pose estimation (DeepLabCut) + LSTM/Transformer → "normal/yaralı/stresli".
- Sürüden kopmuş birey anomali tespiti.

### 6.2 Re-identification
- Aynı hayvanı farklı uçuşlarda tekil ID ver (MegaDetector, MiewID).
- Popülasyon tahmini.

### 6.3 Kaçak av / anomali tespiti
- Gece + insan + araç + silah kombinasyonu → otomatik alarm.
- Push bildirim / SMS / WhatsApp entegrasyonu.

### 6.4 Multi-modal füzyon
- RGB + termal (FLIR Boson, DJI Zenmuse H20T) eş-zamanlı işleme.
- Termal "sıcak nokta" RGB tespit confidence'ını yükseltir.

### 6.5 LLM köprüsü (Claude 4.7 Opus tool-calling)
- "Son 24 saatte vadi X'te geyik sayısı?" → tool-call → SQL → grafik.
- Canlı video özetleme, doğal dil görev planlama.

---

## Faz 7 — Güvenlik & Regülasyon (sürekli)

- Authentication: OAuth2 (Google/Keycloak), rol bazlı erişim (pilot/araştırmacı/admin).
- HTTPS zorunlu, CSRF + rate-limit.
- Türkiye SHGM uzaktan pilot lisansı uyumu.
- EU EASA UAS Regulation (Open / Specific / Certified sınıfları).
- No-fly zone API'leri (AirMap, Altitude Angel).
- Nadir tür konumları için **coordinate jittering** (kaçak avcı koruması).

---

## Faz 8 — Ürünleştirme (6+ ay)

| Hedef Kitle | Ürün |
|---|---|
| Park görevlileri | Flutter mobil uygulama |
| Bakanlık / STK | SaaS multi-tenant dashboard |
| Araştırmacı | Jetson + dron + tablet sahada kurulabilir kit |
| Biyolog | GBIF'e otomatik veri kayıt |
| Gece operasyonu | Termal ek modül |

---

## Önerilen Başlangıç Sırası

1. **Faz 1** — hızlı kazanç, mevcut akışı bozmaz.
2. **Faz 2.1** (homografi) — tek geometri fonksiyonu değişikliği, sonuç kalitesi sıçrar.
3. **Faz 3.2** (WebSocket + Leaflet) — kullanıcı deneyimi modernleşir.
4. **Faz 4.1** (PostgreSQL) — veri birikmeye başlar, analitik açılır.
5. **Faz 5.1** (TensorRT) — sahada gerçek FPS.

Diğer fazlar paralel akabilir; bütün ekip aynı fazda olmak zorunda değil.

---

## Akademik Çıktı Potansiyeli

- IEEE IGARSS / Remote Sensing dergisi: "Edge-optimized UAV animal tracking with homography-corrected geolocation".
- Balıkesir bölgesi yerel tür veri seti → açık yayın → yüksek atıf.
- YOLOv8 vs YOLO26 vs RT-DETR vs Grounding-DINO karşılaştırma.
- TÜBİTAK 1001, 1005, 2209-B çağrı uyumu; TAGEM & DKMP ortaklık fırsatı.
