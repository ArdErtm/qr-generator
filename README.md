# QR Kod Yönlendirme Sistemi

Django ve Vue.js ile oluşturulmuş bir QR kod oluşturma ve yönlendirme sistemi.

## Özellikler

- QR kod oluşturma ve yönetimi
- Kullanıcı kayıt ve giriş sistemi
- Haftalık QR kod limiti (10 QR kod)
- QR kodlarını PDF olarak dışa aktarma
- Analitik gösterge paneli
- QR kod silme ve arşivleme

## Kurulum Talimatları

Aşağıdaki adımları takip ederek projeyi local ortamınızda çalıştırabilirsiniz.

### Ön Gereksinimler

- Python 3.8 veya daha yüksek bir sürüm
- pip (Python paket yöneticisi)
- Git

### 1. Projeyi Klonlama

```bash
# Projeyi klonlayın
git clone https://github.com/kullaniciadi/qr-generator.git
cd qr-generator
```

### 2. Sanal Ortam Oluşturma

```bash
# Python sanal ortamı oluşturun
python3 -m venv venv

# Sanal ortamı aktifleştirin
# Windows için:
venv\Scripts\activate
# macOS/Linux için:
source venv/bin/activate
```

### 3. Bağımlılıkları Yükleme

```bash
# Gerekli paketleri yükleyin
pip install -r requirements.txt
```

### 4. Veritabanı Ayarları

```bash
# Veritabanı migrasyonlarını oluşturun
python manage.py migrate
```

### 5. Admin Kullanıcısı Oluşturma

```bash
# Admin kullanıcısı oluşturun
python manage.py createsuperuser
# (İstenilen kullanıcı adı, e-posta ve şifre bilgilerini girin)
```

### 6. Statik Dosyaları Toplama (Canlı ortam için)

```bash
# Statik dosyaları toplayın
python manage.py collectstatic
```

### 7. Sunucuyu Çalıştırma

```bash
# Geliştirme sunucusunu başlatın
python manage.py runserver
```

Tarayıcınızda `http://127.0.0.1:8000/` adresine giderek uygulamayı kullanmaya başlayabilirsiniz.

## Kullanım

1. Kayıt olun veya giriş yapın
2. Dashboard sayfasında yeni QR kodu oluşturun
3. Oluşturulan QR kodlarını görüntüleyin, PDF olarak indirin veya silin
4. Analitik panelinden kullanım istatistiklerinizi takip edin

## Canlı Ortama Geçiş

Canlı ortama geçiş için:

1. `.env` dosyası oluşturun ve gerekli çevre değişkenlerini ayarlayın
2. `settings.py` dosyasındaki ayarları güncelleyin:
   ```python
   DEBUG = False
   ALLOWED_HOSTS = ['sizindomain.com', 'www.sizindomain.com']
   ```
3. `qr_app/models.py` dosyasındaki QR URL oluşturma kodunu gerçek domain adresinizle güncelleyin
4. Güvenli bir veritabanı (PostgreSQL önerilir) kullanın
5. HTTPS kullanın
6. Bir WSGI sunucusu (Gunicorn, uWSGI vb.) kullanın

## Teknik Notlar

- Django 5.2.1 kullanılmıştır
- QR kod oluşturma için `qrcode` kütüphanesi kullanılmıştır
- PDF oluşturma için `reportlab` kütüphanesi kullanılmıştır
- Frontend için Bootstrap 5 ve Vue.js kullanılmıştır
- QR kodlar direkt olarak hedef URL'e yönlendirilir

## Sorun Giderme

**S: Kurulum sırasında paket hataları alıyorum.**

C: Python versiyonunuzu kontrol edin (3.8 veya üstü olmalı). Ayrıca pip'i güncellemek de yardımcı olabilir:
```bash
pip install --upgrade pip
```

**S: QR kodları tarayınca çalışmıyor.**

C: `qr_app/models.py` dosyasında `qr_url` değişkenini kendi sunucu adresinizle güncellediğinizden emin olun.

**S: Admin paneline erişemiyorum.**

C: `createsuperuser` komutu ile bir admin kullanıcısı oluşturduğunuzdan emin olun ve doğru kimlik bilgilerini kullandığınızı kontrol edin.
 