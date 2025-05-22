from django.urls import path
from . import views

app_name = 'qr_app'

urlpatterns = [
    path('redirect/<str:slug>/', views.redirect_qr, name='redirect_qr'),
    path('api/create-qr/', views.create_qr_api, name='create_qr_api'),
    
    # Kullanıcı kimlik doğrulama
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Kullanıcı paneli
    path('dashboard/', views.dashboard, name='dashboard'),
    path('delete-qr/<int:pk>/', views.delete_qr, name='delete_qr'),
    path('export-qr-pdf/<int:pk>/', views.export_qr_pdf, name='export_qr_pdf'),
    
    # Ana sayfa
    path('', views.dashboard, name='home'),
] 