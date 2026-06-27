# AI Destekli LMS (Öğrenme Yönetim Sistemi)

Bu proje, öğrencilerin ders içeriklerini çalışabileceği, yapay zeka ile hazırlanan özetleri okuyabileceği ve yaptıkları ödev teslimlerini LLM (Gemini / Groq) entegrasyonuyla anında değerlendirip geri bildirim alabileceği yapay zeka destekli modern bir LMS (Learning Management System) uygulamasıdır.

## 🚀 Proje Yapısı

```text
lms-yapayzeka-final/
├── app.py              # Ana Uygulama (Streamlit Arayüzü)
├── api.py              # FastAPI Web Servisleri ve Uç Noktaları
├── ai_service.py       # LLM API Mantığı (Gemini & Groq Entegrasyonu)
├── database.py         # SQLite & Veritabanı Hashing/Bağlantı İşlemleri
├── models.py           # Veri Modelleri ve Şemalar (SQLAlchemy & Pydantic)
├── requirements.txt    # Gerekli Kütüphaneler
├── .env                # API Anahtarları (Yerelde kullanım için)
└── README.md           # Proje Tanımı ve Kurulum Notları
```

## 🛠️ Teknolojiler
- **Arayüz (Frontend):** Streamlit (Premium Glassmorphic CSS Tasarımı)
- **Arka Plan Servisi (Backend):** FastAPI (Uvicorn sunucusu)
- **Veritabanı (Database):** SQLite (SQLAlchemy ORM)
- **Yapay Zeka (AI / NLP):** Google Gemini API (`gemini-1.5-flash`) & Groq API (`llama3-8b-8192`)
- **Güvenlik:** `passlib` & `bcrypt` (Şifrelerin veritabanında güvenli şekilde hash'lenmesi)

---

## ⚡ Kurulum ve Çalıştırma Adımları

### 1. Gerekli Kütüphaneleri Yükleyin
Öncelikle projenin bulunduğu klasörde bir terminal açın ve gerekli tüm paketleri yükleyin:

```bash
pip install -r requirements.txt
```

### 2. API Anahtarlarını Yapılandırın
Kök dizindeki `.env` dosyasını açıp kendi API anahtarlarınızı girin veya uygulamayı çalıştırdıktan sonra Streamlit sol menüsündeki ayarlar kısmından doğrudan girin:

```env
GEMINI_API_KEY=kendi_gemini_api_anahtariniz
GROQ_API_KEY=kendi_groq_api_anahtariniz
```

*(Eğer API anahtarlarınız yoksa, sistem test edebilmeniz için otomatik olarak taslak/mock değerlendirmeler ve geri bildirimler oluşturacaktır.)*

### 3. FastAPI Sunucusunu Başlatın
Backend veritabanı işlemlerini ve AI servislerini yöneten FastAPI sunucusunu ayağa kaldırın:

```bash
uvicorn api:app --reload --port 8000
```
*Bu komuttan sonra veritabanı (`lms.db`) otomatik olarak oluşturulacak ve FastAPI sunucusu `http://127.0.0.1:8000` adresinde çalışmaya başlayacaktır.*

### 4. Streamlit Arayüzünü Başlatın
Yeni bir terminal sekmesi/penceresi açarak Streamlit uygulamasını çalıştırın:

```bash
streamlit run app.py
```
*Tarayıcınızda otomatik olarak `http://localhost:8501` adresi açılacaktır.*

---

## 💡 Temel Özellikler ve Kullanım Senaryoları

### 🔐 Kullanıcı Yönetimi
- Sisteme **Eğitmen (Teacher)** veya **Öğrenci (Student)** rolüyle kayıt olabilirsiniz.
- Şifreleriniz veritabanına kaydedilmeden önce modern standartlara uygun olarak hash'lenir.

### 📚 Eğitmen Paneli
- **Yeni Kurs Oluşturma:** Eğitmenler diledikleri kadar kurs/müfredat ekleyebilir.
- **Ders Ekleme:** Kursların içerisine detaylı metin içerikleri barındıran dersler eklenebilir.
- **AI Ders Özetleme:** Eklenen ders içeriklerine tek tıklamayla Gemini veya Groq üzerinden yapay zeka özeti üretilip sisteme kaydedilir.
- **Ödev Değerlendirme Takibi:** Öğrencilerden gelen ödevlerin, AI notlarının ve AI geri bildirimlerinin toplu listesi görüntülenebilir.

### 📖 Öğrenci Paneli
- **Ders Çalışma:** Mevcut tüm kurslara erişebilir, ders içeriklerini ve eğitmenin hazırlattığı yapay zeka özetlerini okuyabilir.
- **Yapay Zeka Destekli Ödev Teslimi:** Dersin altındaki alana cevap yazarak ödevini gönderebilir. Yapay zeka öğrencinin cevabını ders içeriğiyle karşılaştırarak:
  1. Anında 100 üzerinden **Not (Grade)** belirler.
  2. Yapıcı ve yönlendirici **Geri Bildirim (Feedback)** üretir.
- **Ödev Geçmişi:** Öğrenci geçmişte teslim ettiği ödevleri ve yapay zeka notlarını rapor halinde izleyebilir.
