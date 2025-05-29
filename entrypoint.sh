#!/bin/sh

# Hata durumunda script'i sonlandır
set -e

# Veritabanı migration'larını uygula
echo "Veritabanı migration'ları uygulanıyor..."
python manage.py migrate --noinput

# Süper kullanıcıyı oluştur (eğer mevcut değilse)
echo "Süper kullanıcı oluşturuluyor..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
username = 'admin'
email = 'admin@example.com' # E-posta adresini isteğe bağlı olarak değiştirebilirsiniz
password = 'GüvenliŞifre' # ŞİFREYİ GÜVENLİ BİR YERDE SAKLAYIN VE BURADA KULLANMAYIN!
                          # Coolify ortam değişkenlerinden almanız daha güvenlidir.

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Süper kullanıcı '{username}' oluşturuldu.")
else:
    print(f"Süper kullanıcı '{username}' zaten mevcut.")
EOF

# Gunicorn'u başlat
echo "Gunicorn başlatılıyor..."
exec "$@" 