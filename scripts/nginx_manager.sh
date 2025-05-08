#!/bin/bash

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
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

exit 0 