#!/usr/bin/env python3
import os
import subprocess
import logging
import secrets
import string
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_password(length=16):
    """Güvenli şifre oluştur"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_secret_key(length=32):
    """Güvenli secret key oluştur"""
    return secrets.token_hex(length)

def run_command(command):
    """Komut çalıştır ve çıktıyı logla"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        logger.info(f"Komut başarılı: {command}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Komut başarısız: {command}")
        logger.error(f"Hata: {e.stderr}")
        return False

def install_requirements():
    """Gerekli paketleri yükle"""
    commands = [
        "sudo apt update",
        "sudo apt install -y python3-pip python3-venv nginx php8.1-fpm mariadb-server",
        "sudo mysql_secure_installation <<EOF\n\n\n\n\n\n\nEOF"  # Otomatik MariaDB güvenlik ayarları
    ]
    
    for command in commands:
        run_command(command)

def setup_directories():
    """Gerekli dizinleri oluştur ve izinleri ayarla"""
    directories = [
        "/var/www",
        "/var/log/php",
        "/var/log/nginx",
        "/run/php"
    ]
    
    for directory in directories:
        # Dizini oluştur
        if not os.path.exists(directory):
            run_command(f"sudo mkdir -p {directory}")
        
        # İzinleri ayarla
        run_command(f"sudo chown -R www-data:www-data {directory}")
        run_command(f"sudo chmod -R 755 {directory}")

def setup_php_fpm():
    """PHP-FPM yapılandırması"""
    # PHP-FPM havuz dizini için özel izinler
    run_command("sudo chmod 775 /run/php")
    run_command("sudo chown www-data:www-data /run/php")

def setup_web_server():
    """Web sunucusu yapılandırması"""
    # Nginx yapılandırma dizini
    nginx_conf_dir = "/etc/nginx/conf.d"
    if not os.path.exists(nginx_conf_dir):
        run_command(f"sudo mkdir -p {nginx_conf_dir}")
    
    # Nginx sites-available ve sites-enabled dizinleri
    for dir_name in ["sites-available", "sites-enabled"]:
        dir_path = f"/etc/nginx/{dir_name}"
        if not os.path.exists(dir_path):
            run_command(f"sudo mkdir -p {dir_path}")

def setup_mariadb():
    """MariaDB yapılandırması"""
    # Rastgele şifre oluştur
    db_password = generate_password()
    
    # MariaDB kullanıcısı ve veritabanı oluştur
    commands = [
        "sudo mysql -e 'CREATE DATABASE IF NOT EXISTS depiar;'",
        f"sudo mysql -e 'CREATE USER IF NOT EXISTS \"depiar\"@\"localhost\" IDENTIFIED BY \"{db_password}\";'",
        "sudo mysql -e 'GRANT ALL PRIVILEGES ON depiar.* TO \"depiar\"@\"localhost\";'",
        "sudo mysql -e 'FLUSH PRIVILEGES;'"
    ]
    
    for command in commands:
        run_command(command)
    
    return db_password

def create_env_file(db_password):
    """Çevre değişkenleri dosyası oluştur"""
    secret_key = generate_secret_key()
    
    env_content = f"""# Veritabanı ayarları
DB_USER=depiar
DB_PASSWORD={db_password}
DB_HOST=localhost
DB_NAME=depiar

# Uygulama ayarları
SECRET_KEY={secret_key}
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Web sunucusu ayarları
WEB_SERVER_TYPE=nginx
PHP_VERSION=8.1
"""
    
    # .env dosyasını oluştur
    with open('.env', 'w') as f:
        f.write(env_content)
    
    # Dosya izinlerini güvenli hale getir
    run_command("chmod 600 .env")
    
    # Şifreleri logla (güvenlik için)
    logger.info("Veritabanı şifresi: " + db_password)
    logger.info("Secret key: " + secret_key)

def setup_python_environment():
    """Python sanal ortamı kur"""
    commands = [
        "python3 -m venv venv",
        "source venv/bin/activate && pip install -r requirements.txt"
    ]
    
    for command in commands:
        run_command(command)

def create_systemd_service():
    """Systemd servisi oluştur"""
    # Projenin tam yolunu al
    project_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    # Servis dosyası içeriği
    service_content = f"""[Unit]
Description=Depiar Hosting Control Panel
After=network.target mariadb.service nginx.service

[Service]
User=www-data
Group=www-data
WorkingDirectory={project_path}
Environment="PATH={project_path}/venv/bin"
ExecStart={project_path}/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    
    # Servis dosyasını oluştur
    with open('/tmp/depiar.service', 'w') as f:
        f.write(service_content)
    
    # Servis dosyasını systemd dizinine taşı ve izinleri ayarla
    commands = [
        "sudo mv /tmp/depiar.service /etc/systemd/system/",
        "sudo chmod 644 /etc/systemd/system/depiar.service",
        "sudo systemctl daemon-reload",
        "sudo systemctl enable depiar.service",
        "sudo systemctl start depiar.service"
    ]
    
    for command in commands:
        run_command(command)

def setup_nginx_ddos_protection():
    """Nginx DDOS koruması yapılandırması"""
    # Nginx DDOS koruma yapılandırması
    nginx_ddos_config = """
# DDOS Koruması - Daha yüksek limitler
limit_req_zone $binary_remote_addr zone=one:10m rate=10r/s;  # Saniyede 10 istek
limit_conn_zone $binary_remote_addr zone=addr:10m;

# Güvenlik başlıkları
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

# Rate limiting - Daha yüksek burst değeri
limit_req zone=one burst=20 nodelay;  # 20 istek burst
limit_conn addr 50;  # 50 eşzamanlı bağlantı

# Timeout ayarları - Daha uzun timeout
client_body_timeout 30s;
client_header_timeout 30s;
keepalive_timeout 65s;
send_timeout 30s;

# Buffer ayarları
client_body_buffer_size 256k;
client_max_body_size 50m;  # Daha büyük dosya yükleme limiti
client_header_buffer_size 2k;
large_client_header_buffers 4 8k;

# Dosya önbelleği
open_file_cache max=2000 inactive=20s;
open_file_cache_valid 30s;
open_file_cache_min_uses 2;
open_file_cache_errors on;
"""
    
    # Yapılandırma dosyasını oluştur
    with open('/tmp/nginx-ddos.conf', 'w') as f:
        f.write(nginx_ddos_config)
    
    # Yapılandırmayı uygula
    commands = [
        "sudo mv /tmp/nginx-ddos.conf /etc/nginx/conf.d/ddos.conf",
        "sudo chmod 644 /etc/nginx/conf.d/ddos.conf",
        "sudo nginx -t",
        "sudo systemctl restart nginx"
    ]
    
    for command in commands:
        run_command(command)

def setup_modsecurity():
    """ModSecurity WAF kurulumu ve yapılandırması"""
    # ModSecurity kur
    commands = [
        "sudo apt install -y libapache2-mod-security2 modsecurity-crs",
        "sudo a2enmod security2",
        "sudo a2enmod headers"
    ]
    
    for command in commands:
        run_command(command)
    
    # ModSecurity yapılandırması
    modsec_config = """
# ModSecurity yapılandırması
SecRuleEngine On
SecRequestBodyAccess On
SecResponseBodyAccess On
SecResponseBodyMimeType text/plain text/html text/xml application/json
SecResponseBodyLimit 524288
SecResponseBodyLimitAction Reject

# Temel güvenlik kuralları
SecRule REQUEST_HEADERS:Content-Type "text/xml" \
     "id:'200000',phase:1,t:none,t:lowercase,pass,nolog,ctl:requestBodyProcessor=XML"

# SQL Injection koruması - Sadece şüpheli karakterleri kontrol et
SecRule ARGS|ARGS_NAMES|REQUEST_COOKIES|REQUEST_COOKIES_NAMES|REQUEST_HEADERS|XML:/* "(?i:(\%27)|(\')|(\-\-)|(\%23)|(#))" \
     "id:'200001',phase:2,rev:'2',ver:'OWASP_CRS/3.0.0',maturity:'9',accuracy:'8',block,msg:'SQL Injection Attack',logdata:'Matched Data: %{TX.0} found within %{MATCHED_VAR_NAME}: %{MATCHED_VAR}',severity:'2',tag:'application-multi',tag:'language-multi',tag:'platform-multi',tag:'attack-sqli',tag:'OWASP_CRS/WEB_ATTACK/SQL_INJECTION',tag:'WASCTC/WASC-19',tag:'OWASP_TOP_10/A1',tag:'OWASP_AppSensor/CIE1',tag:'PCI/6.5.2',t:none,t:urlDecodeUni,t:htmlEntityDecode,t:lowercase,t:replaceComments,t:compressWhiteSpace"

# XSS koruması - Sadece tehlikeli HTML karakterlerini kontrol et
SecRule ARGS|ARGS_NAMES|REQUEST_COOKIES|REQUEST_COOKIES_NAMES|REQUEST_HEADERS|XML:/* "(?i:(<script|javascript:|<iframe|<object|data:))" \
     "id:'200002',phase:2,rev:'2',ver:'OWASP_CRS/3.0.0',maturity:'9',accuracy:'8',block,msg:'XSS Attack',logdata:'Matched Data: %{TX.0} found within %{MATCHED_VAR_NAME}: %{MATCHED_VAR}',severity:'2',tag:'application-multi',tag:'language-multi',tag:'platform-multi',tag:'attack-xss',tag:'OWASP_CRS/WEB_ATTACK/XSS',tag:'WASCTC/WASC-8',tag:'WASCTC/WASC-22',tag:'OWASP_TOP_10/A2',tag:'OWASP_AppSensor/IE1',tag:'PCI/6.5.1',t:none,t:urlDecodeUni,t:htmlEntityDecode,t:lowercase,t:replaceComments,t:compressWhiteSpace"

# Command Injection koruması - Sadece tehlikeli komutları kontrol et
SecRule ARGS|ARGS_NAMES|REQUEST_COOKIES|REQUEST_COOKIES_NAMES|REQUEST_HEADERS|XML:/* "(?i:(;|\\|`|\\$|\\&|\\|))" \
     "id:'200003',phase:2,rev:'2',ver:'OWASP_CRS/3.0.0',maturity:'9',accuracy:'8',block,msg:'Command Injection Attack',logdata:'Matched Data: %{TX.0} found within %{MATCHED_VAR_NAME}: %{MATCHED_VAR}',severity:'2',tag:'application-multi',tag:'language-multi',tag:'platform-multi',tag:'attack-cmdi',tag:'OWASP_CRS/WEB_ATTACK/COMMAND_INJECTION',tag:'WASCTC/WASC-31',tag:'OWASP_TOP_10/A1',tag:'OWASP_AppSensor/CIE1',tag:'PCI/6.5.2',t:none,t:urlDecodeUni,t:htmlEntityDecode,t:lowercase,t:replaceComments,t:compressWhiteSpace"

# Whitelist kuralları - Güvenli IP'ler ve kullanıcı ajanları
SecRule REMOTE_ADDR "^192\\.168\\.1\\.\\d+$" "id:'200004',phase:1,t:none,nolog,allow,ctl:ruleEngine=Off"
SecRule REQUEST_HEADERS:User-Agent "^(Mozilla|Chrome|Safari|Firefox|Edge)" "id:'200005',phase:1,t:none,nolog,allow,ctl:ruleEngine=Off"
"""
    
    # Yapılandırma dosyasını oluştur
    with open('/tmp/modsecurity.conf', 'w') as f:
        f.write(modsec_config)
    
    # Yapılandırmayı uygula
    commands = [
        "sudo mv /tmp/modsecurity.conf /etc/modsecurity/modsecurity.conf",
        "sudo chmod 644 /etc/modsecurity/modsecurity.conf",
        "sudo systemctl restart apache2"
    ]
    
    for command in commands:
        run_command(command)

def setup_fail2ban():
    """Fail2ban kurulumu ve yapılandırması"""
    # Fail2ban kur
    commands = [
        "sudo apt install -y fail2ban",
        "sudo systemctl enable fail2ban",
        "sudo systemctl start fail2ban"
    ]
    
    for command in commands:
        run_command(command)
    
    # Fail2ban yapılandırması - Daha yüksek limitler
    fail2ban_config = """
[DEFAULT]
bantime = 1800  # 30 dakika ban
findtime = 1800  # 30 dakika içinde
maxretry = 10   # 10 başarısız deneme
destemail = root@localhost
sender = fail2ban@localhost
action = %(action_mwl)s

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5    # SSH için daha düşük limit
bantime = 3600  # SSH için 1 saat ban

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
bantime = 1800

[nginx-botsearch]
enabled = true
filter = nginx-botsearch
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 20   # Bot taraması için daha yüksek limit
bantime = 3600

[nginx-ddos]
enabled = true
filter = nginx-ddos
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 50   # DDOS için çok daha yüksek limit
bantime = 3600
"""
    
    # Yapılandırma dosyasını oluştur
    with open('/tmp/jail.local', 'w') as f:
        f.write(fail2ban_config)
    
    # Yapılandırmayı uygula
    commands = [
        "sudo mv /tmp/jail.local /etc/fail2ban/jail.local",
        "sudo chmod 644 /etc/fail2ban/jail.local",
        "sudo systemctl restart fail2ban"
    ]
    
    for command in commands:
        run_command(command)

def main():
    """Ana kurulum fonksiyonu"""
    logger.info("Sunucu kurulumu başlıyor...")
    
    # Gerekli paketleri yükle
    install_requirements()
    
    # Dizinleri ve izinleri ayarla
    setup_directories()
    
    # PHP-FPM yapılandırması
    setup_php_fpm()
    
    # Web sunucusu yapılandırması
    setup_web_server()
    
    # Nginx DDOS koruması
    setup_nginx_ddos_protection()
    
    # ModSecurity WAF kurulumu
    setup_modsecurity()
    
    # Fail2ban kurulumu
    setup_fail2ban()
    
    # MariaDB yapılandırması ve şifreyi al
    db_password = setup_mariadb()
    
    # .env dosyasını oluştur
    create_env_file(db_password)
    
    # Python ortamını kur
    setup_python_environment()
    
    # Systemd servisi oluştur ve başlat
    create_systemd_service()
    
    logger.info("Sunucu kurulumu tamamlandı!")
    logger.info("Lütfen yukarıdaki veritabanı şifresini ve secret key'i güvenli bir yerde saklayın!")
    logger.info("Uygulama otomatik olarak başlatıldı ve sistem başlangıcında otomatik başlayacak şekilde ayarlandı.")
    logger.info("Uygulama durumunu kontrol etmek için: sudo systemctl status depiar")
    logger.info("Uygulamayı yeniden başlatmak için: sudo systemctl restart depiar")
    logger.info("Fail2ban durumunu kontrol etmek için: sudo fail2ban-client status")
    logger.info("ModSecurity loglarını kontrol etmek için: sudo tail -f /var/log/modsecurity/modsec_audit.log")

if __name__ == "__main__":
    main() 