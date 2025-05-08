# Depiar Kurulum Kılavuzu

## 1. Sunucu Hazırlığı

### 1.1. Sistem Gereksinimleri
- Ubuntu 20.04 LTS veya üzeri
- En az 2 CPU çekirdek
- En az 4GB RAM
- En az 20GB disk alanı

### 1.2. Sistem Güncellemesi
```bash
# Sistemi güncelle
sudo apt update
sudo apt upgrade -y

# Gerekli paketleri yükle
sudo apt install -y python3.10 python3.10-venv python3-pip nginx mysql-server redis-server git
```

## 2. Depiar Kurulumu

### 2.1. Proje Dosyalarını İndirme
```bash
# Proje dizinini oluştur
sudo mkdir -p /opt/depiar
cd /opt/depiar

# Projeyi GitHub'dan indir
sudo git clone https://github.com/your-repo/depiar.git .
```

### 2.2. Python Ortamı Hazırlama
```bash
# Python sanal ortam oluştur
python3.10 -m venv venv
source venv/bin/activate

# Gerekli paketleri yükle
pip install -r requirements.txt
```

### 2.3. Veritabanı Kurulumu
```bash
# MySQL güvenlik ayarları
sudo mysql_secure_installation

# Veritabanı oluştur
mysql -u root -p
```

MySQL içinde şu komutları çalıştırın:
```sql
CREATE DATABASE depiar CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'depiar'@'localhost' IDENTIFIED BY 'güçlü-bir-şifre-seçin';
GRANT ALL PRIVILEGES ON depiar.* TO 'depiar'@'localhost';
FLUSH PRIVILEGES;
exit;
```

### 2.4. Ortam Değişkenleri
```bash
# .env dosyası oluştur
sudo nano /opt/depiar/.env
```

Aşağıdaki içeriği ekleyin (şifreleri kendi seçtiğiniz değerlerle değiştirin):
```env
DATABASE_URL=mysql://depiar:güçlü-bir-şifre-seçin@localhost/depiar
SECRET_KEY=rastgele-uzun-bir-string-oluşturun
ALLOWED_HOSTS=sizin-domain.com
ALLOWED_ORIGINS=https://sizin-domain.com
```

### 2.5. Nginx Yapılandırması
```bash
# Nginx konfigürasyonu oluştur
sudo nano /etc/nginx/sites-available/depiar
```

Aşağıdaki konfigürasyonu ekleyin:
```nginx
server {
    listen 80;
    server_name sizin-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /opt/depiar/static;
    }
}
```

```bash
# Nginx konfigürasyonunu etkinleştir
sudo ln -s /etc/nginx/sites-available/depiar /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 2.6. SSL Sertifikası
```bash
# Certbot kurulumu
sudo apt install -y certbot python3-certbot-nginx

# SSL sertifikası al
sudo certbot --nginx -d sizin-domain.com
```

### 2.7. Systemd Servis Dosyası
```bash
# Servis dosyası oluştur
sudo nano /etc/systemd/system/depiar.service
```

Aşağıdaki içeriği ekleyin:
```ini
[Unit]
Description=Depiar Web Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/depiar
Environment="PATH=/opt/depiar/venv/bin"
ExecStart=/opt/depiar/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app

[Install]
WantedBy=multi-user.target
```

```bash
# Servisi başlat
sudo systemctl enable depiar
sudo systemctl start depiar
```

## 3. Güvenlik Ayarları

### 3.1. Güvenlik Duvarı
```bash
# Güvenlik duvarını yapılandır
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3.2. Fail2ban Kurulumu
```bash
# Fail2ban kurulumu
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## 4. Kurulum Kontrolü

### 4.1. Servis Durumu Kontrolü
```bash
# Depiar servisinin durumunu kontrol et
sudo systemctl status depiar

# Nginx durumunu kontrol et
sudo systemctl status nginx
```

### 4.2. Log Kontrolü
```bash
# Depiar loglarını kontrol et
sudo journalctl -u depiar -n 50

# Nginx loglarını kontrol et
sudo tail -f /var/log/nginx/error.log
```

## 5. Sorun Giderme

### 5.1. Yaygın Sorunlar

1. **Servis Başlatılamıyor**
```bash
# Logları kontrol et
sudo journalctl -u depiar -n 50

# Dizin izinlerini kontrol et
sudo chown -R www-data:www-data /opt/depiar
```

2. **Nginx 502 Hatası**
```bash
# Nginx konfigürasyonunu kontrol et
sudo nginx -t

# Depiar servisinin çalıştığından emin ol
sudo systemctl status depiar
```

3. **Veritabanı Bağlantı Hatası**
```bash
# MySQL bağlantısını test et
mysql -u depiar -p
```

### 5.2. Destek

Teknik destek için:
- Email: support@depiar.com
- Dokümantasyon: https://docs.depiar.com
- GitHub Issues: https://github.com/your-repo/depiar/issues 