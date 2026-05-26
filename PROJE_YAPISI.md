# ANİSTREAM - Proje Yapısı ve Hibrit Öneri Sistemi Mimarisi

Bu belge, projenin teknik yapısını ve hibrit öneri algoritmasının nasıl çalıştığını detaylandırmak için oluşturulmuştur.

## 🛠️ Teknik Mimari

Proje üç ana katmandan oluşur:
1.  **Veri Katmanı:** `anime.csv` üzerinden beslenen ve SQLite veritabanında saklanan anime ve kullanıcı etkileşim verileri.
2.  **Model Katmanı (Hibrit Motor):** LightFM kütüphanesi ile eğitilmiş, `/models` dizinindeki hibrit zeka dosyaları.
3.  **Sunum Katmanı:** Flask tabanlı web arayüzü ve Jikan API ile dinamik içerik çekimi.

---

## 🧠 Hibrit Sistem Nerede ve Nasıl Çalışıyor?

Sistem, "Hibrit" ismini iki farklı veri türünü ve iki farklı algoritmayı harmanlamasından alır.

### 1. LightFM'in Kendi İçindeki Hibrit Yapısı
Eğitilmiş modelimiz (`hybrid_lightfm_model.pkl`), öğrenme aşamasında şu iki veriyi birleştirmiştir:
-   **İşbirlikçi Filtreleme (Collaborative):** 275.473 gerçek kullanıcının hangi animeleri izleyip beğendiği bilgisi.
-   **İçerik Tabanlı Filtreleme (Content):** Animelerin türleri (Action, Romance, vb.) ve özellikleri.

Model, bir animeyi önerirken sadece "başkaları da bunu izledi" demez, aynı zamanda "senin sevdiğin türlere de uyuyor" diyerek iki sinyali birleştirir.

### 2. Web Sitesindeki Dinamik Hibrit Akış
Siz web sitesinde bir animeyi puanladığınızda (`recommender.py` içinde) şu hibrit süreç işler:

1.  **Kullanıcı Eşleştirme (Nearest Neighbor):** Sizin web sitesinde verdiğiniz puanlar, modelin eğitim verisindeki 275k gerçek kullanıcıyla karşılaştırılır.
2.  **Profil Analizi:** Sizin zevkinize en çok benzeyen (en yakın komşu) gerçek kullanıcı bulunur.
3.  **Model Tahmini:** Model, o kullanıcının profilini ve animelerin içerik özelliklerini kullanarak size özel bir skor üretir.
4.  **Yumuşak Filtreleme (Survey Weighting):** Modelden gelen bu hibrit skor, sizin anket (Survey) tercihlerinizle (sevdiğiniz türler vb.) harmanlanarak %30 ek bonus alır.

### 3. Kullanım Alanları

-   **Ana Sayfa (Sizin İçin Önerilenler):** Tam hibrit motoru kullanır. Hem geçmiş puanlarınızdan benzer kullanıcıları bulur hem de anket tercihlerinizi skora yansıtır.
-   **Sevdiyseniz Bunları da Sevebilirsiniz:** İçerik tabanlı benzerlik (Content-based Similarity) kullanır. LightFM'in "item embedding"leri üzerinden matematiksel benzerlik hesaplar.
-   **Bildirim Sistemi:** Hibrit motorun ürettiği en yüksek skorlu animelerden rastgele birini seçerek "Her girişte yeni bir keşif" sunar.

### 4. ❤️ Beğendim ve ✅ İzlendi Butonlarının Rolü

Bu butonlar sadece görsel bir liste tutmakla kalmaz, öneri algoritmasını doğrudan etkiler:
-   **Filtreleme:** Bir animeyi beğendiğinizde veya izlendi olarak işaretlediğinizde, bu anime "Sizin İçin Önerilenler" listesinden otomatik olarak çıkarılır. Böylece sistem size sürekli daha önce görmediğiniz, keşfedilmeyi bekleyen yeni içerikler sunar.
-   **Profil Oluşturma:** Bu veriler profil sayfanızda listelenerek zevk haritanızı çıkarmanıza yardımcı olur.


---

## 📂 Dosya Görevleri

-   `recommender.py`: Hibrit mantığının kalbi. Benzer kullanıcı bulma ve model tahmini burada yapılır.
-   `app.py`: Web isteklerini yönetir ve öneri sonuçlarını arayüze aktarır.
-   `models.py`: Puanların (Rating) ve kullanıcı tercihlerinin veritabanı şeması.
-   `base.html`: Bildirim dropdown'u ve navigasyon yapısı.
-   `index.html`: Hibrit önerilerin (Slider) son kullanıcıya sunulduğu vitrin.

---
Bu yapı sayesinde sistem, siz hiç puan vermeseniz bile anket sonuçlarınızla çalışmaya başlar (Cold Start); puan verdikçe ise gerçek bir zevk profili oluşturarak size özel "İnsan + İçerik" odaklı öneriler sunar.
