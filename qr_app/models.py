from django.db import models
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
import os
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse

class QRCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='qr_codes', verbose_name="Kullanıcı", null=True, blank=True)
    title = models.CharField(max_length=200, verbose_name="Başlık")
    redirect_url = models.URLField(verbose_name="Yönlendirilecek URL")
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, verbose_name="QR Kod Görseli")
    slug = models.SlugField(unique=True, blank=True, verbose_name="QR Kod Slug")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    is_deleted = models.BooleanField(default=False, verbose_name="Silinmiş mi")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Silinme Tarihi")
    
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
        # QR içeriği, doğrudan hedef URL'i içerecek
        qr.add_data(self.redirect_url)
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
    
    def soft_delete(self):
        """QR kodunu silmek yerine is_deleted olarak işaretler"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def get_secure_qr_url(self):
        """QR kod dosyası için güvenli URL döndürür"""
        if self.qr_code and self.qr_code.name:
            return reverse('qr_app:secure_media', args=[self.qr_code.name])
        return None
    
    @classmethod
    def user_weekly_qr_count(cls, user):
        """Kullanıcının bu hafta oluşturduğu QR kod sayısını döndürür"""
        # Bu haftanın başlangıcını bul (Pazartesi)
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        start_datetime = timezone.make_aware(timezone.datetime.combine(start_of_week, timezone.datetime.min.time()))
        
        # Bu hafta oluşturulan tüm QR kodlarını say (silinmiş olsa bile)
        return cls.objects.filter(
            user=user,
            created_at__gte=start_datetime
        ).count()
    
    @classmethod
    def user_qr_stats(cls, user):
        """Kullanıcının QR kod istatistiklerini döndürür"""
        total_qr_count = cls.objects.filter(user=user).count()
        active_qr_count = cls.objects.filter(user=user, is_deleted=False).count()
        deleted_qr_count = cls.objects.filter(user=user, is_deleted=True).count()
        
        # Bu haftanın başlangıcını bul (Pazartesi)
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        start_datetime = timezone.make_aware(timezone.datetime.combine(start_of_week, timezone.datetime.min.time()))
        
        # Bu hafta oluşturulan QR sayısı
        weekly_qr_count = cls.objects.filter(
            user=user,
            created_at__gte=start_datetime
        ).count()
        
        # Kalan haftalık limit
        remaining_weekly_limit = 10 - weekly_qr_count
        
        return {
            'total_qr_count': total_qr_count,
            'active_qr_count': active_qr_count,
            'deleted_qr_count': deleted_qr_count,
            'weekly_qr_count': weekly_qr_count,
            'remaining_weekly_limit': max(0, remaining_weekly_limit)
        }
        
    class Meta:
        verbose_name = "QR Kodu"
        verbose_name_plural = "QR Kodları"
