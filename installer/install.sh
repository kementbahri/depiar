#!/bin/bash

# Hata durumunda betiği durdur
set -e

# Renkli çıktı için
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Kullanıcıdan domain veya IP adresi al
read -p "Domain adını veya IP adresini girin: " DOMAIN_OR_IP

# Kullanıcıdan admin kullanıcı adı ve şifre al
read -p "Admin kullanıcı adını girin: " ADMIN_USERNAME
read -s -p "Admin şifresini girin: " ADMIN_PASSWORD
echo

# Sistem güncellemelerini yap
echo -e "${YELLOW}Sistem güncellemeleri yapılıyor...${NC}"
apt update && apt upgrade -y

# MySQL kontrolü ve kaldırma
echo -e "${YELLOW}MySQL durumu kontrol ediliyor...${NC}"
if systemctl is-active --quiet mysql || systemctl is-active --quiet mysqld; then
    echo -e "${YELLOW}MySQL servisi çalışıyor, durduruluyor...${NC}"
    systemctl stop mysql 2>/dev/null || true
    systemctl stop mysqld 2>/dev/null || true
fi

if dpkg -l | grep -E 'mysql|mariadb' > /dev/null; then
    echo -e "${YELLOW}MySQL paketleri bulundu, kaldırılıyor...${NC}"
    apt remove --purge mysql-server mysql-client mysql-common mysql-server-core-* mysql-client-core-* -y
    apt remove --purge mariadb-server mariadb-client mariadb-common mariadb-server-core-* mariadb-client-core-* -y
    apt remove --purge mysql-* mariadb-* -y
    apt autoremove -y
    apt autoclean
fi

# MySQL dizinlerini temizle
echo -e "${YELLOW}MySQL dizinleri temizleniyor...${NC}"
rm -rf /var/lib/mysql*
rm -rf /var/log/mysql*
rm -rf /etc/mysql*
rm -rf /var/run/mysqld
rm -rf /run/mysqld
rm -rf /usr/share/mysql*
rm -rf /usr/lib/mysql*

# MySQL kullanıcılarını temizle
echo -e "${YELLOW}MySQL kullanıcıları temizleniyor...${NC}"
deluser mysql 2>/dev/null || true
deluser mysql-* 2>/dev/null || true
delgroup mysql 2>/dev/null || true
delgroup mysql-* 2>/dev/null || true

# MySQL'i yeniden yükle
echo -e "${YELLOW}MySQL yeniden yükleniyor...${NC}"
apt install -y mysql-server

# MySQL socket dizinini oluştur ve izinlerini ayarla
echo -e "${YELLOW}MySQL socket dizini oluşturuluyor...${NC}"
mkdir -p /var/run/mysqld
chown mysql:mysql /var/run/mysqld
chmod 755 /var/run/mysqld

# MySQL yapılandırmasını düzenle
echo -e "${YELLOW}MySQL yapılandırması düzenleniyor...${NC}"
cat > /etc/mysql/mysql.conf.d/mysqld.cnf << 'EOL'
[mysqld]
pid-file        = /var/run/mysqld/mysqld.pid
socket          = /var/run/mysqld/mysqld.sock
datadir         = /var/lib/mysql
log-error       = /var/log/mysql/error.log
bind-address    = 0.0.0.0
mysqlx-bind-address = 0.0.0.0

# Karakter seti ayarları
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# Performans ayarları
innodb_buffer_pool_size = 256M
innodb_redo_log_capacity = 134217728
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT

# Bağlantı ayarları
max_connections = 100
wait_timeout = 28800
interactive_timeout = 28800

# Güvenlik ayarları
default_authentication_plugin = caching_sha2_password

[client]
default-character-set = utf8mb4

[mysql]
default-character-set = utf8mb4
EOL

# MySQL servisini başlat
echo -e "${YELLOW}MySQL servisi başlatılıyor...${NC}"
systemctl start mysql
systemctl enable mysql

# Gerekli paketleri yükle
echo -e "${YELLOW}Gerekli paketler yükleniyor...${NC}"
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    php8.1-fpm \
    php8.1-mysql \
    php8.1-curl \
    php8.1-gd \
    php8.1-mbstring \
    php8.1-xml \
    php8.1-zip \
    php8.1-bcmath \
    php8.1-intl \
    php8.1-soap \
    php8.1-ldap \
    php8.1-imap \
    php8.1-cli \
    php8.1-common \
    php8.1-opcache \
    php8.1-readline \
    php8.1-sqlite3 \
    php8.1-xmlrpc \
    php8.1-xsl

# MySQL root şifresini oluştur
echo -e "${YELLOW}MySQL root şifresi oluşturuluyor...${NC}"
# Özel karakterler içermeyen güvenli şifre oluştur
MYSQL_ROOT_PASSWORD=$(openssl rand -base64 12 | tr -dc 'a-zA-Z0-9' | head -c 16)
MYSQL_DEPIAR_PASSWORD=$(openssl rand -base64 12 | tr -dc 'a-zA-Z0-9' | head -c 16)

# Şifreleri göster
echo -e "${GREEN}Oluşturulan şifreler:${NC}"
echo -e "MySQL Root Şifresi: ${GREEN}$MYSQL_ROOT_PASSWORD${NC}"
echo -e "MySQL Depiar Şifresi: ${GREEN}$MYSQL_DEPIAR_PASSWORD${NC}"
echo -e "${YELLOW}Bu şifreleri not alın!${NC}"
sleep 5

# MySQL'i yapılandır
echo -e "${YELLOW}MySQL yapılandırılıyor...${NC}"

# MySQL servisini durdur
systemctl stop mysql

# MySQL'i güvenli modda başlat
echo -e "${YELLOW}MySQL güvenli modda başlatılıyor...${NC}"
mkdir -p /var/run/mysqld
chown mysql:mysql /var/run/mysqld
mysqld_safe --skip-grant-tables --skip-networking &
sleep 5

# Root şifresini sıfırla
echo -e "${YELLOW}Root şifresi sıfırlanıyor...${NC}"
mysql -u root << EOF
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED WITH caching_sha2_password BY '$MYSQL_ROOT_PASSWORD';
FLUSH PRIVILEGES;
EOF

# MySQL'i durdur ve normal modda başlat
echo -e "${YELLOW}MySQL normal modda başlatılıyor...${NC}"
killall mysqld
sleep 2
systemctl start mysql
sleep 5

# Veritabanı ve kullanıcı oluştur
echo -e "${YELLOW}Veritabanı ve kullanıcı oluşturuluyor...${NC}"
mysql -u root -p"$MYSQL_ROOT_PASSWORD" << EOF
CREATE DATABASE IF NOT EXISTS depiar CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
DROP USER IF EXISTS 'depiar'@'localhost';
CREATE USER 'depiar'@'localhost' IDENTIFIED WITH caching_sha2_password BY '$MYSQL_DEPIAR_PASSWORD';
GRANT ALL PRIVILEGES ON depiar.* TO 'depiar'@'localhost';
FLUSH PRIVILEGES;
EOF

# Proje dizinini oluştur
echo -e "${YELLOW}Proje dizini oluşturuluyor...${NC}"
rm -rf /var/www/depiar
mkdir -p /var/www/depiar
cd /var/www/depiar

# Projeyi GitHub'dan klonla
echo -e "${YELLOW}Proje GitHub'dan klonlanıyor...${NC}"
git clone https://github.com/kementbahri/depiar.git .

# requirements.txt dosyasını oluştur
echo -e "${YELLOW}requirements.txt dosyası oluşturuluyor...${NC}"
cat > requirements.txt << 'EOL'
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
pymysql==1.1.0
python-jose==3.3.0
passlib==1.7.4
python-multipart==0.0.6
bcrypt==4.0.1
python-dotenv==1.0.0
requests==2.31.0
aiofiles==23.2.1
jinja2==3.1.2
slowapi==0.1.8
EOL

chown -R www-data:www-data /var/www/depiar

# Python sanal ortamı oluştur
echo -e "${YELLOW}Python sanal ortamı oluşturuluyor...${NC}"
python3 -m venv venv
source venv/bin/activate

# Gerekli Python paketlerini yükle
echo -e "${YELLOW}Python paketleri yükleniyor...${NC}"
pip install -r requirements.txt

# PYTHONPATH'i ayarla
echo -e "${YELLOW}PYTHONPATH ayarlanıyor...${NC}"
export PYTHONPATH=/var/www/depiar:$PYTHONPATH

# Servis dosyasını kopyala
echo -e "${YELLOW}Servis dosyası kopyalanıyor...${NC}"
cat > /etc/systemd/system/depiar.service << 'EOL'
[Unit]
Description=Depiar API Service
After=network.target mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/depiar
Environment="PATH=/var/www/depiar/venv/bin"
Environment="PYTHONPATH=/var/www/depiar"
Environment="MYSQL_DEPIAR_PASSWORD=$MYSQL_DEPIAR_PASSWORD"
ExecStart=/var/www/depiar/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

systemctl daemon-reload
systemctl enable depiar

# Nginx yapılandırmasını kopyala
echo -e "${YELLOW}Nginx yapılandırması kopyalanıyor...${NC}"
cat > /etc/nginx/sites-available/depiar << 'EOL'
server {
    listen 80;
    server_name _;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
    }

    location /static {
        alias /var/www/depiar/static;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location /media {
        alias /var/www/depiar/media;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
EOL

ln -s /etc/nginx/sites-available/depiar /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Dizin izinlerini ayarla
echo -e "${YELLOW}Dizin izinleri ayarlanıyor...${NC}"
chown -R www-data:www-data /var/www/depiar
chmod -R 755 /var/www/depiar
chmod -R 775 /var/www/depiar/media
chmod -R 775 /var/www/depiar/static

# Servisleri başlat
echo -e "${YELLOW}Servisler başlatılıyor...${NC}"
systemctl restart nginx
systemctl restart depiar

# Servislerin durumunu kontrol et
echo -e "${YELLOW}Servislerin durumu kontrol ediliyor...${NC}"
if ! systemctl is-active --quiet nginx; then
    echo -e "${RED}Nginx başlatılamadı!${NC}"
    journalctl -u nginx -n 50
    exit 1
fi

if ! systemctl is-active --quiet depiar; then
    echo -e "${RED}Depiar servisi başlatılamadı!${NC}"
    journalctl -u depiar -n 50
    exit 1
fi

# SSL sertifikası al (eğer domain girilmişse)
if [[ $DOMAIN_OR_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${YELLOW}IP adresi girildi, SSL sertifikası alınmayacak.${NC}"
else
    echo -e "${YELLOW}SSL sertifikası alınıyor...${NC}"
    apt install -y certbot python3-certbot-nginx
    certbot --nginx -d $DOMAIN_OR_IP --non-interactive --agree-tos --email admin@$DOMAIN_OR_IP
fi

# Admin kullanıcısını oluştur
echo -e "${YELLOW}Admin kullanıcısı oluşturuluyor...${NC}"
cd /var/www/depiar
source venv/bin/activate
export PYTHONPATH=/var/www/depiar:$PYTHONPATH
python3 -c "
from backend.models import User
from backend.database import SessionLocal
from backend.auth import get_password_hash

db = SessionLocal()
admin = User(
    username='$ADMIN_USERNAME',
    email='admin@$DOMAIN_OR_IP',
    hashed_password=get_password_hash('$ADMIN_PASSWORD'),
    is_admin=True
)
db.add(admin)
db.commit()
db.close()
"

# Kurulum tamamlandı
echo -e "${GREEN}Kurulum tamamlandı!${NC}"
echo -e "${YELLOW}Önemli Bilgiler:${NC}"
echo -e "Domain/IP: ${GREEN}$DOMAIN_OR_IP${NC}"
echo -e "Admin Kullanıcı Adı: ${GREEN}$ADMIN_USERNAME${NC}"
echo -e "MySQL Root Şifresi: ${GREEN}$MYSQL_ROOT_PASSWORD${NC}"
echo -e "MySQL Depiar Şifresi: ${GREEN}$MYSQL_DEPIAR_PASSWORD${NC}"

# Servislerin durumunu göster
echo -e "${YELLOW}Servislerin durumu:${NC}"
systemctl status nginx
systemctl status mysql
systemctl status depiar 