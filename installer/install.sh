#!/bin/bash

# Renk tanımlamaları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Root kontrolü
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Bu betik root yetkisi gerektirir.${NC}"
    exit 1
fi

# Domain veya IP adresi kontrolü
read -p "Domain adı veya IP adresi girin: " DOMAIN
if [ -z "$DOMAIN" ]; then
    echo -e "${RED}Domain adı veya IP adresi gereklidir.${NC}"
    exit 1
fi

# Admin kullanıcı bilgileri
read -p "Admin kullanıcı adı girin: " ADMIN_USER
if [ -z "$ADMIN_USER" ]; then
    echo -e "${RED}Admin kullanıcı adı gereklidir.${NC}"
    exit 1
fi

read -s -p "Admin şifresi girin: " ADMIN_PASS
echo
if [ -z "$ADMIN_PASS" ]; then
    echo -e "${RED}Admin şifresi gereklidir.${NC}"
    exit 1
fi

# Şifre oluşturma
MYSQL_ROOT_PASS=$(openssl rand -base64 32)
MYSQL_DEPIAR_PASS=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 32)

echo -e "${YELLOW}Sistem güncelleniyor...${NC}"
apt update && apt upgrade -y

echo -e "${YELLOW}Gerekli paketler yükleniyor...${NC}"
apt install -y python3 python3-pip python3-venv nginx mysql-server redis-server fail2ban ufw certbot python3-certbot-nginx

echo -e "${YELLOW}MySQL güvenlik ayarları yapılandırılıyor...${NC}"
mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '$MYSQL_ROOT_PASS';"
mysql -e "DELETE FROM mysql.user WHERE User='';"
mysql -e "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"
mysql -e "DROP DATABASE IF EXISTS test;"
mysql -e "DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';"
mysql -e "FLUSH PRIVILEGES;"

echo -e "${YELLOW}Depiar veritabanı oluşturuluyor...${NC}"
mysql -e "CREATE DATABASE depiar CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -e "CREATE USER 'depiar'@'localhost' IDENTIFIED BY '$MYSQL_DEPIAR_PASS';"
mysql -e "GRANT ALL PRIVILEGES ON depiar.* TO 'depiar'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

echo -e "${YELLOW}Proje dizini oluşturuluyor...${NC}"
mkdir -p /var/www/depiar
cd /var/www/depiar

echo -e "${YELLOW}Python sanal ortamı oluşturuluyor...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "${YELLOW}Bağımlılıklar yükleniyor...${NC}"
pip install -r requirements.txt

echo -e "${YELLOW}Ortam değişkenleri ayarlanıyor...${NC}"
cat > .env << EOL
DATABASE_URL=mysql://depiar:$MYSQL_DEPIAR_PASS@localhost/depiar
SECRET_KEY=$SECRET_KEY
REDIS_URL=redis://localhost:6379/0
DOMAIN=$DOMAIN
EOL

echo -e "${YELLOW}Nginx yapılandırması ayarlanıyor...${NC}"
cp nginx.conf /etc/nginx/nginx.conf
sed -i "s/domain.com/$DOMAIN/g" /etc/nginx/nginx.conf

echo -e "${YELLOW}SSL sertifikası alınıyor...${NC}"
if [[ $DOMAIN =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${YELLOW}IP adresi kullanıldığı için SSL sertifikası alınmayacak.${NC}"
else
    certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
fi

echo -e "${YELLOW}Fail2ban yapılandırması ayarlanıyor...${NC}"
cp fail2ban.conf /etc/fail2ban/jail.local
systemctl restart fail2ban

echo -e "${YELLOW}Güvenlik duvarı ayarlanıyor...${NC}"
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable

echo -e "${YELLOW}Systemd servisi oluşturuluyor...${NC}"
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

echo -e "${YELLOW}Servisler başlatılıyor...${NC}"
systemctl daemon-reload
systemctl enable depiar
systemctl start depiar
systemctl restart nginx

echo -e "${GREEN}Kurulum tamamlandı!${NC}"
echo -e "${YELLOW}Önemli bilgiler:${NC}"
echo "Domain: $DOMAIN"
echo "Admin Kullanıcı: $ADMIN_USER"
echo "MySQL Root Şifresi: $MYSQL_ROOT_PASS"
echo "MySQL Depiar Şifresi: $MYSQL_DEPIAR_PASS"
echo "Secret Key: $SECRET_KEY"
echo -e "${YELLOW}Bu bilgileri güvenli bir yerde saklayın!${NC}"

if [[ $DOMAIN =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${GREEN}Kontrol paneline http://$DOMAIN adresinden erişebilirsiniz.${NC}"
else
    echo -e "${GREEN}Kontrol paneline https://$DOMAIN adresinden erişebilirsiniz.${NC}"
fi

git config --global user.email "github-email-adresiniz"
git config --global user.name "github-kullanici-adiniz"

git remote add origin https://github.com/kementbahri/depiar.git
git push -u origin master 