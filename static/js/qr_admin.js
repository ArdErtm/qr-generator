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