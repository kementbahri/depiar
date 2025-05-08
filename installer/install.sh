#!/bin/bash

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Bu script root yetkisi gerektirir.${NC}"
    exit 1
fi

# Check system requirements
echo -e "${YELLOW}Sistem gereksinimleri kontrol ediliyor...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 bulunamadı. Lütfen Python3'ü yükleyin.${NC}"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}pip3 bulunamadı. Lütfen pip3'ü yükleyin.${NC}"
    exit 1
fi

# Install system dependencies
echo -e "${YELLOW}Sistem bağımlılıkları yükleniyor...${NC}"
apt-get update
apt-get install -y python3-venv python3-dev build-essential libssl-dev libffi-dev nginx mysql-server

# Create application directory
echo -e "${YELLOW}Uygulama dizini oluşturuluyor...${NC}"
mkdir -p /var/www/depiar
cd /var/www/depiar

# Create and activate virtual environment
echo -e "${YELLOW}Python sanal ortamı oluşturuluyor...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${YELLOW}Python bağımlılıkları yükleniyor...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Configure MySQL
echo -e "${YELLOW}MySQL yapılandırılıyor...${NC}"
mysql -e "CREATE DATABASE IF NOT EXISTS depiar CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -e "CREATE USER IF NOT EXISTS 'depiar'@'localhost' IDENTIFIED BY '${MYSQL_DEPIAR_PASSWORD}';"
mysql -e "GRANT ALL PRIVILEGES ON depiar.* TO 'depiar'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

# Create systemd service file
echo -e "${YELLOW}Systemd servis dosyası oluşturuluyor...${NC}"
cat > /etc/systemd/system/depiar.service << EOL
[Unit]
Description=Depiar API Service
After=network.target mysql.service
Requires=mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/depiar
Environment="PYTHONPATH=/var/www/depiar"
Environment="MYSQL_DEPIAR_PASSWORD=${MYSQL_DEPIAR_PASSWORD}"
ExecStart=/var/www/depiar/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload --log-level debug
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

# Set permissions
echo -e "${YELLOW}Dizin izinleri ayarlanıyor...${NC}"
chown -R www-data:www-data /var/www/depiar
chmod -R 755 /var/www/depiar

# Enable and start services
echo -e "${YELLOW}Servisler etkinleştiriliyor ve başlatılıyor...${NC}"
systemctl daemon-reload
systemctl enable mysql
systemctl enable nginx
systemctl enable depiar

systemctl restart mysql
systemctl restart nginx
systemctl restart depiar

# Check service status
echo -e "${YELLOW}Servis durumları kontrol ediliyor...${NC}"
if systemctl is-active --quiet mysql; then
    echo -e "${GREEN}MySQL başarıyla başlatıldı!${NC}"
else
    echo -e "${RED}MySQL başlatılamadı!${NC}"
    journalctl -u mysql -n 50
    exit 1
fi

if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}Nginx başarıyla başlatıldı!${NC}"
else
    echo -e "${RED}Nginx başlatılamadı!${NC}"
    journalctl -u nginx -n 50
    exit 1
fi

if systemctl is-active --quiet depiar; then
    echo -e "${GREEN}Depiar API servisi başarıyla başlatıldı!${NC}"
else
    echo -e "${RED}Depiar API servisi başlatılamadı!${NC}"
    journalctl -u depiar -n 50
    exit 1
fi

echo -e "${GREEN}Kurulum tamamlandı!${NC}"
echo -e "${YELLOW}Panel arayüzüne http://localhost adresinden erişebilirsiniz.${NC}" 