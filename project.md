# Django ve Vue.js ile QR Kod Yönlendirme Sistemi

## 1. Proje Ortamının Hazırlanması

```bash
# Proje klasörü oluştur
mkdir qr_redirect_project
cd qr_redirect_project

# Virtual environment oluştur
python -m venv venv

# Virtual environment aktifleştir
# Windows için:
venv\Scripts\activate
# macOS/Linux için:
source venv/bin/activate

# Gerekli paketleri yükle
pip install django qrcode pillow
```

## 2. Django Projesi Oluşturma

```bash
# Django projesi oluştur
django-admin startproject qr_redirect .

# Uygulama oluştur
python manage.py startapp qr_app
```

## 3. Django Ayarlarını Yapılandırma

`qr_redirect/settings.py` dosyasını aç ve aşağıdaki değişiklikleri yap:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'qr_app',  # Uygulamayı ekle
]

# Dil ve zaman dilimi ayarları (isteğe bağlı)
LANGUAGE_CODE = 'tr-tr'
TIME_ZONE = 'Europe/Istanbul'

# Statik dosya ayarları
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media dosya ayarları (QR kodları için)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Template dizinini ekle
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # templates dizinini ekle
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
```

## 4. QR Kod Modeli Oluşturma

`qr_app/models.py` dosyasını aşağıdaki gibi düzenle:

```python
from django.db import models
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
import os

class QRCode(models.Model):
    title = models.CharField(max_length=200, verbose_name="Başlık")
    redirect_url = models.URLField(verbose_name="Yönlendirilecek URL")
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, verbose_name="QR Kod Görseli")
    slug = models.SlugField(unique=True, blank=True, verbose_name="QR Kod Slug")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Slug oluştur (eğer yoksa)
        if not self.slug:
            import uuid
            self.slug = str(uuid.uuid4())[:8]
        
        # QR kodu oluştur
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        # QR içeriği, redirect URL'ini içerecek
        qr_url = f"http://127.0.0.1:8000/redirect/{self.slug}/"
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        # Eski QR kodu silelim eğer güncelleme yapıyorsak
        if self.qr_code:
            if os.path.isfile(self.qr_code.path):
                os.remove(self.qr_code.path)
        
        # Yeni QR kodunu kaydedelim
        self.qr_code.save(f'qr_code_{self.slug}.png', 
                          File(buffer), save=False)
        
        super().save(*args, **kwargs)
        
    class Meta:
        verbose_name = "QR Kodu"
        verbose_name_plural = "QR Kodları"
```

## 5. Admin Panelini Özelleştirme

`qr_app/admin.py` dosyasını düzenle:

```python
from django.contrib import admin
from django.utils.html import mark_safe
from .models import QRCode

@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ('title', 'redirect_url', 'created_at', 'qr_preview')
    search_fields = ('title', 'redirect_url')
    readonly_fields = ('qr_preview', 'slug')
    fields = ('title', 'redirect_url', 'slug', 'qr_preview')
    
    def qr_preview(self, obj):
        if obj.qr_code:
            return mark_safe(f'<img src="{obj.qr_code.url}" width="150" height="150" />')
        return "QR kod henüz oluşturulmadı."
    
    qr_preview.short_description = 'QR Kod Önizleme'
```

## 6. QR Kod Yönlendirme View'ını Oluşturma

`qr_app/views.py` dosyasını düzenle:

```python
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
import json
from .models import QRCode

def redirect_qr(request, slug):
    """QR kodu tarandığında bu view çalışır ve kullanıcıyı ilgili URL'e yönlendirir"""
    qr_code = get_object_or_404(QRCode, slug=slug)
    return redirect(qr_code.redirect_url)

@csrf_protect
@require_POST
def create_qr_api(request):
    """Vue.js uygulamasından QR kod oluşturmak için API endpoint'i"""
    try:
        data = json.loads(request.body)
        title = data.get('title')
        redirect_url = data.get('redirect_url')
        
        if not title or not redirect_url:
            return JsonResponse({'error': 'Başlık ve URL alanları zorunludur'}, status=400)
        
        qr_code = QRCode(title=title, redirect_url=redirect_url)
        qr_code.save()
        
        return JsonResponse({
            'success': True,
            'id': qr_code.id,
            'slug': qr_code.slug,
            'qr_code_url': qr_code.qr_code.url
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
```

## 7. URL Yapılandırması

`qr_app/urls.py` dosyasını oluştur:

```python
from django.urls import path
from . import views

app_name = 'qr_app'

urlpatterns = [
    path('redirect/<str:slug>/', views.redirect_qr, name='redirect_qr'),
    path('api/create-qr/', views.create_qr_api, name='create_qr_api'),
]
```

Ana URL yapılandırması için `qr_redirect/urls.py` dosyasını düzenle:

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('qr_app.urls')),
]

# Media dosyaları için URL yapılandırması
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## 8. Klasör Yapılarını Oluşturma

```bash
# Static ve media klasörlerini oluştur
mkdir -p static/js static/css media/qr_codes
mkdir -p templates/admin/qr_app/qrcode
```

## 9. Vue.js ile Frontend Entegrasyonu

### 9.1. Vue.js Dosyalarını Hazırlama

`static/js/qr_admin.js` dosyasını oluştur:

```javascript
const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'], // Django template tag'leri ile çakışmasını önlemek için
    data() {
        return {
            title: '',
            redirectUrl: '',
            loading: false,
            message: '',
            error: '',
        }
    },
    methods: {
        async createQRCode() {
            if (!this.title || !this.redirectUrl) {
                this.error = 'Başlık ve URL alanları zorunludur';
                return;
            }
            
            this.loading = true;
            this.error = '';
            this.message = '';
            
            try {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                
                const response = await fetch('/api/create-qr/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        title: this.title,
                        redirect_url: this.redirectUrl
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    this.message = 'QR kod başarıyla oluşturuldu!';
                    this.title = '';
                    this.redirectUrl = '';
                    // Admin paneli yenileme için isteğe bağlı
                    // window.location.reload();
                } else {
                    this.error = data.error || 'QR kod oluşturulurken bir hata oluştu';
                }
            } catch (err) {
                this.error = 'Bir hata oluştu: ' + err.message;
            } finally {
                this.loading = false;
            }
        }
    }
}).mount('#qr-app');
```

### 9.2. Admin Paneline Vue.js Entegrasyonu için Template Oluşturma

`templates/admin/qr_app/qrcode/change_list.html` dosyasını oluştur:

```html
{% extends "admin/change_list.html" %}
{% load static %}

{% block extrahead %}
{{ block.super }}
<script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
<style>
    .qr-app {
        margin: 20px 0;
        padding: 20px;
        background-color: #f8f8f8;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .form-group {
        margin-bottom: 15px;
    }
    .form-group label {
        display: block;
        margin-bottom: 5px;
        font-weight: bold;
    }
    .form-control {
        width: 100%;
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
    }
    .btn-primary {
        background-color: #417690;
        color: white;
        border: none;
        padding: 10px 15px;
        border-radius: 4px;
        cursor: pointer;
    }
    .btn-primary:hover {
        background-color: #2b5070;
    }
    .alert {
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
    }
    .alert-success {
        background-color: #dff0d8;
        color: #3c763d;
    }
    .alert-danger {
        background-color: #f2dede;
        color: #a94442;
    }
</style>
{% endblock %}

{% block content %}
<div id="qr-app" class="qr-app">
    <h2>Hızlı QR Kod Oluştur</h2>
    
    <div v-if="message" class="alert alert-success">
        [[ message ]]
    </div>
    
    <div v-if="error" class="alert alert-danger">
        [[ error ]]
    </div>
    
    <form @submit.prevent="createQRCode">
        {% csrf_token %}
        <div class="form-group">
            <label for="title">Başlık</label>
            <input type="text" id="title" v-model="title" class="form-control" placeholder="QR Kod Başlığı">
        </div>
        
        <div class="form-group">
            <label for="redirectUrl">Yönlendirilecek URL</label>
            <input type="url" id="redirectUrl" v-model="redirectUrl" class="form-control" placeholder="https://example.com">
        </div>
        
        <button type="submit" class="btn-primary" :disabled="loading">
            <span v-if="loading">İşleniyor...</span>
            <span v-else>QR Kod Oluştur</span>
        </button>
    </form>
</div>

{{ block.super }}

<script src="{% static 'js/qr_admin.js' %}"></script>
{% endblock %}
```

## 10. Veritabanı Migrasyonları ve Admin Kullanıcısı Oluşturma

```bash
# Migrasyonları oluştur
python manage.py makemigrations

# Migrasyonları uygula
python manage.py migrate

# Admin kullanıcısı oluştur
python manage.py createsuperuser
# (İstenilen kullanıcı adı, e-posta ve şifre bilgilerini gir)
```

## 11. Projeyi Çalıştırma

```bash
python manage.py runserver
```

Tarayıcıda `http://127.0.0.1:8000/admin/` adresine giderek admin paneline erişebilirsin.

## 12. QR Kod Oluşturma ve Test Etme

1. Admin paneline giriş yap
2. "QR Kodları" bölümüne git
3. "Hızlı QR Kod Oluştur" formunu kullanarak veya "QR KODU EKLE" butonuyla yeni bir QR kodu oluştur
4. Oluşturulan QR kodu bir QR kod okuyucu ile tarandığında, belirtilen URL'e otomatik olarak yönlendirileceksin

## Notlar ve İpuçları

1. Canlı ortama geçerken, `models.py` dosyasındaki `qr_url` değişkenini gerçek domain adresinle güncellemelisin:
   ```python
   qr_url = f"https://senindomain.com/redirect/{self.slug}/"
   ```

2. Canlı ortamda SQLite yerine PostgreSQL gibi daha güçlü bir veritabanı kullanmak daha iyi olabilir.

3. QR kod görüntülerinin büyüklüğünü ve diğer özelliklerini `models.py` dosyasındaki QR kod oluşturma kodunda düzenleyebilirsin.

4. Güvenlik için, yönlendirme URL'lerini kontrol eden bir sistem ekleyebilirsin (zararlı URL'lere yönlendirmeyi önlemek için).

5. Oluşturulan QR kodlarının istatistiklerini tutmak için (kaç kez tarandığı gibi) modele istatistik alanları ekleyebilirsin.

## Başlangıç Proje yapısı 

qr_redirect_project/
├── qr_redirect/          # Ana proje klasörü
│   ├── settings.py       # Proje ayarları
│   ├── urls.py           # Ana URL yapılandırması
│   └── wsgi.py           # WSGI yapılandırması
├── qr_app/               # Uygulama klasörü
│   ├── admin.py          # Admin panel yapılandırması
│   ├── models.py         # QR kod modeli
│   ├── views.py          # View fonksiyonları
│   └── urls.py           # Uygulama URL yapılandırması
├── static/               # Statik dosyalar
│   ├── js/               # JavaScript dosyaları
│   │   └── qr_admin.js   # Vue.js uygulaması
│   └── css/              # CSS dosyaları
├── templates/            # Şablonlar
│   └── admin/            # Admin şablonları
│       └── qr_app/       
│           └── qrcode/   
│               └── change_list.html  
# Özelleştirilmiş admin şablonu
├── media/                # Yüklenen dosyalar (QR kodları)
│   └── qr_codes/         # QR kod görselleri
├── manage.py             # Django yönetim aracı
└── README.md             # Bu dosya

