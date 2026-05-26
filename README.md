# ANİSTREAM - Hibrit Anime Tavsiye Sistemi

Bu proje, LightFM kütüphanesi kullanılarak geliştirilmiş, hem içerik tabanlı (Content-Based) hem de işbirlikçi filtreleme (Collaborative Filtering) yöntemlerini birleştiren gelişmiş bir hibrit anime öneri platformudur.

## 🚀 Özellikler

- **Hibrit Öneri Motoru:** 275.000+ kullanıcı etkileşimi ve anime türleri kullanılarak eğitilmiş LightFM modeli.
- **Kişiselleştirilmiş Bildirimler:** Her girişte kullanıcıya özel, puanlama geçmişine dayalı film önerileri.
- **Dinamik Puanlama:** 1-10 arası puanlama sistemi ve puanlara göre anlık güncellenen tavsiyeler.
- **Sinematik Arayüz:** Modern Dark-Mode Glassmorphism tasarımı.
- **Gelişmiş Filtreleme:** Serinin diğer yapımları (franchise) ve benzer seriler arasındaki ayrımı yapabilen akıllı algoritma.
- **Gerçek Zamanlı Veri:** Jikan API entegrasyonu ile yüksek çözünürlüklü kapak resimleri.

## 🛠️ Kurulum ve Çalıştırma

Projeyi yerel bilgisayarınızda çalıştırmak için aşağıdaki adımları izleyin:

### 1. Gereksinimler
- Python 3.9 veya üzeri
- `pip` (Python paket yöneticisi)
- PostgreSQL (Sistemde kurulu ve çalışır durumda olmalıdır)

### 2. Hazırlık ve Bağımlılıklar
Terminali açın ve proje ana dizinine gidin:

```bash
# Backend dizinine girin
cd backend

# Sanal ortam oluşturun
python -m venv venv

# Sanal ortamı aktif edin
# Windows için:
venv\Scripts\activate
# macOS/Linux için:
source venv/bin/activate

# Gerekli kütüphaneleri yükleyin
pip install -r requirements.txt
```

### 3. Veritabanı Yapılandırması
`backend/config.py` dosyasını açın ve `SQLALCHEMY_DATABASE_URI` satırındaki veritabanı şifresini kendi PostgreSQL şifrenizle güncelleyin.

### 4. Uygulamayı Başlatma
Bağımlılıklar yüklendikten sonra uygulamayı çalıştırabilirsiniz:

```bash
python app.py
```

Uygulama varsayılan olarak `http://127.0.0.1:8080` adresinde çalışacaktır.

## 📂 Proje Yapısı

- `/backend`: Flask sunucusu, veritabanı modelleri (PostgreSQL) ve öneri motoru.
- `/frontend`: HTML şablonları ve CSS dosyaları.
- `/data`: `anime.csv` (Veritabanını besleyen ham veri).
- `/models`: Eğitilmiş LightFM modelleri (`.pkl` dosyaları).

## 💡 Önemli Notlar

- **İlk Çalıştırma:** Uygulama ilk kez çalıştırıldığında `anime.csv` dosyasındaki verileri otomatik olarak PostgreSQL veritabanına işleyecektir. Bu işlem veri setinin büyüklüğüne göre 30-60 saniye sürebilir. Terminalde "Populating Anime table..." yazısını göreceksiniz.
- **Modeller:** `/models` dizinindeki `.pkl` dosyalarının mevcut olduğundan emin olun. Bu dosyalar öneri sisteminin kalbidir.
- **Giriş Yapma:** Kayıt olduktan sonra sizi karşılayan anketi doldurmanız, hibrit öneri sisteminin sizi tanıması için önemlidir.

---
