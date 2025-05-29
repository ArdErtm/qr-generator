from django.contrib import admin
from django.utils.html import mark_safe
from .models import QRCode

@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'redirect_url', 'created_at', 'qr_preview')
    search_fields = ('title', 'redirect_url', 'user__username')
    readonly_fields = ('qr_preview', 'slug')
    fields = ('user', 'title', 'redirect_url', 'slug', 'qr_preview')
    list_filter = ('user',)
    
    def qr_preview(self, obj):
        secure_url = obj.get_secure_qr_url()
        if secure_url:
            return mark_safe(f'<img src="{secure_url}" width="150" height="150" alt="QR Kod" />')
        return "QR kod henüz oluşturulmadı."
    
    qr_preview.short_description = 'QR Kod Önizleme'
