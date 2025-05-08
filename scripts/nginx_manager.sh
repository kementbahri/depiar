#!/bin/bash

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to create a new virtual host
create_vhost() {
    local domain=$1
    local root_path=$2

    # Create virtual host configuration
    cat > "/etc/nginx/sites-available/${domain}" << EOL
server {
    listen 80;
    server_name ${domain};
    root ${root_path};
    index index.html index.htm index.php;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
    }

    location ~ /\.ht {
        deny all;
    }
}
EOL

    # Enable the site
    ln -sf "/etc/nginx/sites-available/${domain}" "/etc/nginx/sites-enabled/${domain}"
    
    # Test Nginx configuration
    nginx -t
    
    # Reload Nginx
    systemctl reload nginx
    
    echo -e "${GREEN}Virtual host created for ${domain}${NC}"
}

# Function to remove a virtual host
remove_vhost() {
    local domain=$1
    
    # Remove symlink
    rm -f "/etc/nginx/sites-enabled/${domain}"
    
    # Remove configuration file
    rm -f "/etc/nginx/sites-available/${domain}"
    
    # Reload Nginx
    systemctl reload nginx
    
    echo -e "${GREEN}Virtual host removed for ${domain}${NC}"
}

# Function to enable SSL for a domain
enable_ssl() {
    local domain=$1
    
    # Check if domain exists
    if [ ! -f "/etc/nginx/sites-available/${domain}" ]; then
        echo -e "${RED}Virtual host not found for ${domain}${NC}"
        exit 1
    }
    
    # Obtain SSL certificate
    certbot --nginx -d ${domain} --non-interactive --agree-tos --email admin@${domain}
    
    echo -e "${GREEN}SSL enabled for ${domain}${NC}"
}

# Main script
case "$1" in
    create)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Usage: $0 create <domain> <root_path>"
            exit 1
        fi
        create_vhost "$2" "$3"
        ;;
    remove)
        if [ -z "$2" ]; then
            echo "Usage: $0 remove <domain>"
            exit 1
        fi
        remove_vhost "$2"
        ;;
    ssl)
        if [ -z "$2" ]; then
            echo "Usage: $0 ssl <domain>"
            exit 1
        fi
        enable_ssl "$2"
        ;;
    *)
        echo "Usage: $0 {create|remove|ssl} [domain] [root_path]"
        exit 1
        ;;
esac

# Nginx dizinlerini oluştur
echo -e "${YELLOW}Nginx dizinleri oluşturuluyor...${NC}"
mkdir -p /etc/nginx/sites-available
mkdir -p /etc/nginx/sites-enabled
mkdir -p /var/log/nginx
chown -R www-data:www-data /var/log/nginx

# Nginx ana yapılandırmasını oluştur
echo -e "${YELLOW}Nginx ana yapılandırması oluşturuluyor...${NC}"
cat > /etc/nginx/nginx.conf << 'EOL'
user www-data;
worker_processes auto;
pid /run/nginx.pid;

events {
    worker_connections 768;
}

http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    gzip on;
    gzip_disable "msie6";

    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
EOL

# Nginx site yapılandırmasını oluştur
echo -e "${YELLOW}Nginx site yapılandırması oluşturuluyor...${NC}"
cat > /etc/nginx/sites-available/depiar << 'EOL'
server {
    listen 80 default_server;
    server_name _;

    client_max_body_size 100M;
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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

# Nginx site yapılandırmasını etkinleştir
echo -e "${YELLOW}Nginx site yapılandırması etkinleştiriliyor...${NC}"
ln -sf /etc/nginx/sites-available/depiar /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Nginx yapılandırmasını test et
echo -e "${YELLOW}Nginx yapılandırması test ediliyor...${NC}"
nginx -t

# Nginx servisini yeniden başlat
echo -e "${YELLOW}Nginx servisi yeniden başlatılıyor...${NC}"
systemctl restart nginx

# Servis durumunu kontrol et
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}Nginx başarıyla başlatıldı!${NC}"
else
    echo -e "${RED}Nginx başlatılamadı!${NC}"
    journalctl -u nginx -n 50
    exit 1
fi

exit 0 