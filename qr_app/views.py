from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
import json
from .models import QRCode
from .forms import RegisterForm, LoginForm, QRCodeForm
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from PIL import Image
import os
from django.utils import timezone
from datetime import timedelta
import mimetypes
from django.conf import settings

def redirect_qr(request, slug):
    """QR kodu tarandığında bu view çalışır ve kullanıcıyı ilgili URL'e yönlendirir"""
    qr_code = get_object_or_404(QRCode, slug=slug, is_deleted=False)
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
        
        # Haftalık limiti kontrol et
        weekly_count = QRCode.user_weekly_qr_count(request.user)
        if weekly_count >= 10:
            return JsonResponse({'error': 'Bu hafta için QR kod oluşturma limitine ulaştınız'}, status=400)
        
        qr_code = QRCode(title=title, redirect_url=redirect_url, user=request.user)
        qr_code.save()
        
        return JsonResponse({
            'success': True,
            'id': qr_code.id,
            'slug': qr_code.slug,
            'qr_code_url': qr_code.get_secure_qr_url()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def register_view(request):
    """Kullanıcı kayıt sayfası"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Kayıt başarıyla tamamlandı!')
            return redirect('qr_app:dashboard')
    else:
        form = RegisterForm()
    
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    """Kullanıcı giriş sayfası"""
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('qr_app:dashboard')
    else:
        form = LoginForm()
    
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    """Kullanıcı çıkış işlemi"""
    logout(request)
    return redirect('qr_app:login')

@login_required
def dashboard(request):
    """Kullanıcı kontrol paneli"""
    # Aktif QR kodlarını getir
    user_qr_codes = QRCode.objects.filter(user=request.user, is_deleted=False).order_by('-created_at')
    
    # Kullanıcı istatistiklerini getir
    stats = QRCode.user_qr_stats(request.user)
    
    # Haftanın başlangıç ve bitiş tarihlerini hesapla
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    if request.method == 'POST':
        form = QRCodeForm(request.POST, user=request.user)
        if form.is_valid():
            qr_code = form.save(commit=False)
            qr_code.user = request.user
            qr_code.save()
            messages.success(request, 'QR kodu başarıyla oluşturuldu!')
            return redirect('qr_app:dashboard')
    else:
        form = QRCodeForm(user=request.user)
    
    context = {
        'qr_codes': user_qr_codes,
        'stats': stats,
        'form': form,
        'start_of_week': start_of_week.strftime('%d.%m.%Y'),
        'end_of_week': end_of_week.strftime('%d.%m.%Y'),
    }
    
    return render(request, 'qr_app/dashboard.html', context)

@login_required
def delete_qr(request, pk):
    """QR kodu silme işlemi (soft delete)"""
    qr_code = get_object_or_404(QRCode, pk=pk, user=request.user)
    if request.method == 'POST':
        qr_code.soft_delete()
        messages.success(request, 'QR kodu başarıyla silindi!')
    return redirect('qr_app:dashboard')

@login_required
def export_qr_pdf(request, pk):
    """QR kodunu PDF olarak dışa aktarma"""
    qr_code = get_object_or_404(QRCode, pk=pk, user=request.user, is_deleted=False)
    
    # PDF oluştur
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    # Başlık ekle
    p.setFont("Helvetica-Bold", 16)
    p.drawString(inch, 10*inch, f"QR Kodu: {qr_code.title}")
    
    # URL bilgisi ekle
    p.setFont("Helvetica", 12)
    p.drawString(inch, 9.5*inch, f"URL: {qr_code.redirect_url}")
    
    # QR kodu ekle
    qr_img_path = qr_code.qr_code.path
    if os.path.exists(qr_img_path):
        p.drawImage(qr_img_path, inch, 4*inch, width=5*inch, height=5*inch)
    
    # Tarih bilgisi ekle
    p.setFont("Helvetica", 10)
    p.drawString(inch, 3*inch, f"Oluşturulma Tarihi: {qr_code.created_at.strftime('%d.%m.%Y %H:%M')}")
    
    p.showPage()
    p.save()
    
    # PDF'i response olarak döndür
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="qr_code_{qr_code.slug}.pdf"'
    
    return response

def secure_media_view(request, file_path):
    """Media dosyalarını güvenli bir şekilde servis eder"""
    try:
        # Güvenlik kontrolleri
        # Path traversal saldırılarını önle
        if '..' in file_path or file_path.startswith('/'):
            raise Http404("Güvenlik hatası: Geçersiz dosya yolu")
        
        # Sadece qr_codes klasöründeki dosyalara erişim izni ver
        if not file_path.startswith('qr_codes/'):
            raise Http404("Güvenlik hatası: Bu dizine erişim izniniz yok")
        
        # Tam dosya yolunu oluştur
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        
        # Dosya varlığını kontrol et
        if not os.path.exists(full_path):
            raise Http404("Dosya bulunamadı")
        
        # Dosya türünü belirle
        content_type, encoding = mimetypes.guess_type(full_path)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        # Sadece resim dosyalarına izin ver
        if not content_type.startswith('image/'):
            raise Http404("Güvenlik hatası: Sadece resim dosyalarına erişim izni var")
        
        # Dosyayı oku ve response oluştur
        with open(full_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
            
        # Güvenlik header'ları ekle
        response['Cache-Control'] = 'max-age=3600'  # 1 saat cache
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        return response
        
    except Exception as e:
        raise Http404("Dosya servisi sırasında hata oluştu")
