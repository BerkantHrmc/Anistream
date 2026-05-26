# 🌌 ANİSTREAM - Hibrit Anime Tavsiye Sistemi Proje Dokümantasyonu

Bu doküman, AniStream projesinin teknik mimarisini, kullanılan teknolojileri, uygulanan algoritmaları ve sistemin çalışma prensiplerini detaylandırmaktadır.

---

## 1. 📋 Proje Özeti
AniStream, kullanıcıların geçmiş izleme ve puanlama alışkanlıklarını analiz ederek onlara kişiselleştirilmiş anime önerileri sunan modern bir web platformudur. Proje, sadece popüler içerikleri değil, kullanıcının spesifik zevklerine hitap eden "gizli kalmış cevherleri" bulmak için geliştirilmiştir.

---

## 2. 🛠️ Teknoloji Yığını (Tech Stack)

### Backend
- **Python 3.11:** Ana programlama dili.
- **Flask 3.0:** Hafif ve esnek web çatısı.
- **Flask-SQLAlchemy:** ORM (Object-Relational Mapping) aracı.
- **Flask-Login:** Kullanıcı oturum yönetimi ve güvenliği.
- **Flask-Bcrypt:** Şifreleme ve güvenlik işlemleri.

### Veri Bilimi ve Makine Öğrenmesi
- **LightFM 1.17:** Hibrit öneri motorunun kalbi. Matrix Factorization tabanlı bir kütüphane.
- **NumPy & SciPy:** Matris işlemleri ve veri manipülasyonu.
- **Pickle:** Eğitilmiş modellerin kaydedilmesi ve hızlı yüklenmesi.

### Frontend
- **HTML5 & CSS3:** Modern, sinematik ve duyarlı (responsive) tasarım.
- **Vanilla JavaScript:** Dinamik arayüz etkileşimleri ve puanlama sistemi.
- **Google Fonts (Inter, Outfit):** Tipografi ve estetik.
- **FontAwesome:** İkonografi.

### Veri Kaynakları
- **Jikan API (Unofficial MyAnimeList API):** Anime kapak resimleri ve güncel meta verilerin çekilmesi.
- **CSV Dataset:** 275.000+ kullanıcı etkileşimi içeren temel eğitim verisi.

---

## 3. 🧠 Öneri Algoritmaları ve Yöntemler

Sistem, üç temel yöntemi birleştiren **Hibrit (Hybrid)** bir yaklaşım kullanır:

### A. İşbirlikçi Filtreleme (Collaborative Filtering)
Sistem, "kullanıcılar arasındaki benzerlikleri" kullanır. Eğer A ve B kullanıcısı benzer animeleri beğendiyse, A'nın izlediği ama B'nin henüz görmediği bir içerik B'ye önerilir. Matrix Factorization (Matris Ayrıştırma) tekniği ile kullanıcı ve içerik etkileşimleri gizli katmanlara (latent factors) indirgenir.

### B. İçerik Tabanlı Filtreleme (Content-Based Filtering)
Sistem, animelerin türlerini (Genres), puanlarını ve synopsis (özet) bilgilerini analiz eder. Bu sayede, kullanıcının sevdiği bir seriye yapısal olarak benzeyen diğer serileri tespit eder.

### C. Hibrit Model (LightFM Implementation)
LightFM kütüphanesi sayesinde, hem kullanıcı etkileşimleri hem de içerik özellikleri (features) aynı anda işlenir. Bu durum, sistemin daha doğru tahmin yapmasını sağlar.

### D. Cold-Start (Soğuk Başlangıç) Çözümü
Yeni kayıt olan kullanıcıların henüz hiç puanı olmadığı için sistem şu yöntemleri kullanır:
1. **Tercih Anketi:** Kullanıcı kayıt olduğunda sevdiği türleri seçer.
2. **Ağırlıklı Puanlama:** İlk öneriler, kullanıcının seçtiği türler ile sistemdeki en yüksek puanlı içeriklerin harmanlanmasıyla oluşur.
3. **Gerçek Zamanlı Öğrenme:** Kullanıcı bir animeye puan verdiği an, model bu puanı dikkate alarak ana sayfa önerilerini anında günceller.

---

## 4. 🗄️ Veritabanı Mimarisi

Sistem aşağıdaki veri modelleri üzerine kuruludur:
- **User:** Kullanıcı adı, e-posta ve şifrelenmiş parola bilgileri.
- **Anime:** MAL_ID, isim, tür, puan ve özet bilgileri.
- **Rating:** Kullanıcıların animelere verdiği 1-10 arası puanlar ve zaman damgası.
- **SurveyAnswer:** Kullanıcının başlangıçta seçtiği tercihlerin saklandığı tablo.
- **Liked/Watched Anime:** Kullanıcının listesine eklediği içerikler.

---

## 5. 🎨 UI/UX Tasarım İlkeleri

- **Glassmorphism:** Yarı saydam arka planlar ve yumuşak blur efektleri.
- **Cinematic Experience:** Büyük hero-bannerlar ve görsel odaklı kart tasarımları.
- **Dark Mode:** Kullanıcı gözünü yormayan modern koyu tema.
- **Micro-Animations:** Hover efektleri ve yumuşak geçişler ile artırılmış kullanıcı deneyimi.

---

## 6. 🚀 Önemli Fonksiyonlar

### `Recommender.get_recommendations()`
Kullanıcının veritabanındaki puanlarını alır, eğitim setindeki en benzer kullanıcıyı bulur ve LightFM modelini kullanarak kişiselleştirilmiş bir liste üretir.

### `Recommender.get_similar_items()`
Belirli bir animeye benzer olanları bulurken, "Franchise" (aynı serinin devam yapımları) ve "Similar" (yapısal olarak benzer farklı seriler) ayrımını akıllıca yapar.

---

## 7. 🛠️ Geliştirme Notları
- **Performans:** 275 bin satırlık veri seti CSR (Compressed Sparse Row) matris formatında işlenerek bellek kullanımı optimize edilmiştir.
- **Hata Yönetimi:** Jikan API'nin hız limitlerine karşı otomatik geciktirme ve retry mekanizmaları eklenmiştir.

---

