# Depiar Kurulum Kılavuzu

## 1. Otomatik Kurulum (Önerilen)

Tek komutla kurulum için:

```bash
wget -O install.sh https://raw.githubusercontent.com/kementbahri/depiar/main/installer/install.sh
chmod +x install.sh
./install.sh
```

Kurulum betiği sizden şu bilgileri isteyecektir:
- Domain adı veya IP adresi
- Admin kullanıcı adı
- Admin şifresi

Kurulum tamamlandığında size şu bilgiler verilecektir:
- MySQL root şifresi
- MySQL Depiar kullanıcı şifresi
- Secret key

Bu bilgileri güvenli bir yerde saklamayı unutmayın!

## 2. Manuel Kurulum

Eğer otomatik kurulum yerine manuel kurulum yapmak isterseniz:

### Sistem Gereksinimleri

- Ubuntu 20.04 LTS veya üzeri
- En az 1GB RAM
- En az 20GB disk alanı

### Adım 1: Sistem Güncellemesi

```bash
apt update && apt upgrade -y
```

### Adım 2: Gerekli Paketlerin Kurulumu

```bash
apt install -y python3 python3-pip python3-venv nginx mysql-server redis-server fail2ban ufw
```

### Adım 3: MySQL Kurulumu

```bash
# MySQL güvenli kurulum
mysql_secure_installation

# Depiar veritabanı ve kullanıcı oluşturma
mysql -u root -p
```

MySQL'de çalıştırılacak komutlar:
```sql
CREATE DATABASE depiar CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'depiar'@'localhost' IDENTIFIED BY 'şifreniz';
GRANT ALL PRIVILEGES ON depiar.* TO 'depiar'@'localhost';
FLUSH PRIVILEGES;
```

### Adım 4: Proje Dosyalarının Kurulumu

```bash
# Proje dizini oluştur
mkdir -p /var/www/depiar
cd /var/www/depiar

# Projeyi indir
git clone https://github.com/kementbahri/depiar.git .

# Python sanal ortamı oluştur
python3 -m venv venv
source venv/bin/activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

### Adım 5: Ortam Değişkenlerinin Ayarlanması

`.env` dosyası oluşturun:
```bash
cat > .env << EOL
DATABASE_URL=mysql://depiar:şifreniz@localhost/depiar
SECRET_KEY=güvenli-bir-anahtar
REDIS_URL=redis://localhost:6379/0
DOMAIN=alan-adınız
EOL
```

### Adım 6: Nginx Yapılandırması

```bash
# Nginx yapılandırma dosyasını kopyala
cp nginx.conf /etc/nginx/nginx.conf

# SSL sertifikası al (domain kullanıyorsanız)
certbot --nginx -d alan-adınız
```

### Adım 7: Servis Oluşturma

```bash
# Systemd servis dosyası oluştur
cat > /etc/systemd/system/depiar.service << EOL
[Unit]
Description=Depiar API Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/depiar
Environment="PATH=/var/www/depiar/venv/bin"
ExecStart=/var/www/depiar/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000

[Install]
WantedBy=multi-user.target
EOL

# Servisi başlat
systemctl daemon-reload
systemctl enable depiar
systemctl start depiar
```

### Adım 8: Güvenlik Ayarları

```bash
# Güvenlik duvarı ayarları
ufw allow ssh
ufw allow http
ufw allow https
ufw enable

# Fail2ban yapılandırması
cp fail2ban.conf /etc/fail2ban/jail.local
systemctl restart fail2ban
```

## Kurulum Sonrası

Kurulum tamamlandıktan sonra kontrol paneline şu adreslerden erişebilirsiniz:
- Domain kullanıyorsanız: `https://alan-adınız`
- IP adresi kullanıyorsanız: `http://ip-adresiniz`

## Sorun Giderme

1. Servis çalışmıyor:
```bash
systemctl status depiar
journalctl -u depiar
```

2. Nginx hataları:
```bash
nginx -t
systemctl status nginx
```

3. MySQL bağlantı sorunları:
```bash
systemctl status mysql
mysql -u depiar -p
```

## Destek

Sorun yaşarsanız:
1. GitHub Issues: https://github.com/kementbahri/depiar/issues
2. E-posta: kementbahri@gmail.com 