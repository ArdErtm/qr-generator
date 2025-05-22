from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from .models import QRCode

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="E-posta")
    
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(RegisterForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Kullanıcı Adı")
    password = forms.CharField(label="Şifre", widget=forms.PasswordInput)
    
    error_messages = {
        'invalid_login': "Kullanıcı adı veya şifre hatalı. Lütfen tekrar deneyin.",
        'inactive': "Bu hesap pasif durumda.",
    }
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            
            if self.user_cache is None:
                # Check if the username exists
                try:
                    user = User.objects.get(username=username)
                    # Username exists, so password is wrong
                    self.add_error('password', "Şifre hatalı, lütfen tekrar deneyin.")
                except User.DoesNotExist:
                    # Username doesn't exist
                    self.add_error('username', "Bu kullanıcı adı ile kayıtlı bir hesap bulunamadı.")
                
                raise self.get_invalid_login_error()
            
            elif not self.user_cache.is_active:
                raise ValidationError(
                    self.error_messages['inactive'],
                    code='inactive',
                )
                
        return self.cleaned_data

class QRCodeForm(forms.ModelForm):
    class Meta:
        model = QRCode
        fields = ['title', 'redirect_url']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'QR Kod Başlığı'}),
            'redirect_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'})
        }
        labels = {
            'title': 'Başlık',
            'redirect_url': 'Yönlendirilecek URL'
        }
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(QRCodeForm, self).__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        # Kullanıcının haftalık QR kod sayısını kontrol et
        if self.user and not self.instance.pk:  # Yeni bir QR kodu oluşturuluyorsa
            weekly_count = QRCode.user_weekly_qr_count(self.user)
            if weekly_count >= 10:
                raise forms.ValidationError("Bu hafta için QR kod oluşturma limitine ulaştınız (10/10). Yeni bir hafta başladığında tekrar deneyebilirsiniz.")
        return cleaned_data 