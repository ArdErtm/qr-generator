# Python'un resmi imajını temel al
FROM python:3.11-slim

# Çalışma dizinini ayarla
WORKDIR /app

# Ortam değişkenlerini ayarla
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Sistem bağımlılıklarını kur (gerekirse)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc

# requirements.txt dosyasını kopyala ve bağımlılıkları kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Proje dosyalarını kopyala
COPY . .

# entrypoint.sh script'ini kopyala ve çalıştırılabilir yap
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Statik dosyaları topla
RUN python manage.py collectstatic --noinput

# Veritabanı migration'larını uygula (entrypoint.sh içine taşındı)
# RUN python manage.py migrate --noinput

# Gunicorn'u kur (veya başka bir WSGI sunucusu)
RUN pip install gunicorn

# Portu dışa aktar
EXPOSE 8000

# Uygulamayı entrypoint script'i ile çalıştır
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "--bind", ":8000", "--workers", "3", "qr_redirect.wsgi:application"] 