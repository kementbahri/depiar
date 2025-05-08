from sqlalchemy.orm import Session
from models.notification_page import NotificationPage
import os
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.template_dir = "/var/www/notifications"
        self._ensure_template_dir()

    def _ensure_template_dir(self):
        """Bildirim şablonları dizinini oluştur"""
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir, mode=0o755)
            # Varsayılan şablonları oluştur
            self._create_default_templates()

    def _create_default_templates(self):
        """Varsayılan bildirim şablonlarını oluştur"""
        default_templates = {
            "suspended": {
                "title": "Hesap Askıya Alındı",
                "content": """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hesap Askıya Alındı</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 600px;
            margin: 40px auto;
            padding: 20px;
            background-color: #fff;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h1 {
            color: #e74c3c;
            margin-bottom: 20px;
        }
        p {
            color: #333;
            margin-bottom: 15px;
        }
        .contact {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Hesap Askıya Alındı</h1>
        <p>Sayın müşterimiz,</p>
        <p>Hesabınız şu anda askıya alınmış durumdadır. Bu durum genellikle aşağıdaki nedenlerden kaynaklanabilir:</p>
        <ul>
            <li>Ödeme gecikmesi</li>
            <li>Hizmet sözleşmesinin sona ermesi</li>
            <li>Kullanım şartlarının ihlali</li>
        </ul>
        <p>Hesabınızı tekrar aktif hale getirmek için lütfen bizimle iletişime geçin.</p>
        <div class="contact">
            <p>İletişim bilgileri:</p>
            <p>E-posta: support@example.com</p>
            <p>Telefon: +90 123 456 7890</p>
        </div>
    </div>
</body>
</html>
"""
            },
            "maintenance": {
                "title": "Bakım Çalışması",
                "content": """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bakım Çalışması</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 600px;
            margin: 40px auto;
            padding: 20px;
            background-color: #fff;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h1 {
            color: #3498db;
            margin-bottom: 20px;
        }
        p {
            color: #333;
            margin-bottom: 15px;
        }
        .estimated-time {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Bakım Çalışması</h1>
        <p>Sayın müşterimiz,</p>
        <p>Daha iyi hizmet verebilmek için sistemlerimizde planlı bakım çalışması yapılmaktadır.</p>
        <div class="estimated-time">
            <p><strong>Tahmini Süre:</strong> 2 saat</p>
            <p><strong>Başlangıç:</strong> {start_time}</p>
            <p><strong>Bitiş:</strong> {end_time}</p>
        </div>
        <p>Bakım çalışması sırasında hizmetlerimiz geçici olarak kullanılamayacaktır. Anlayışınız için teşekkür ederiz.</p>
    </div>
</body>
</html>
"""
            }
        }

        for template_type, template_data in default_templates.items():
            # Veritabanına kaydet
            notification = NotificationPage(
                type=template_type,
                title=template_data["title"],
                content=template_data["content"],
                is_active=True
            )
            self.db.add(notification)
            
            # HTML dosyasını oluştur
            file_path = os.path.join(self.template_dir, f"{template_type}.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(template_data["content"])
        
        self.db.commit()

    def get_notification_page(self, type: str) -> NotificationPage:
        """Bildirim sayfasını getir"""
        return self.db.query(NotificationPage).filter(
            NotificationPage.type == type,
            NotificationPage.is_active == True
        ).first()

    def update_notification_page(self, type: str, title: str, content: str) -> NotificationPage:
        """Bildirim sayfasını güncelle"""
        notification = self.get_notification_page(type)
        if not notification:
            notification = NotificationPage(type=type)
            self.db.add(notification)
        
        notification.title = title
        notification.content = content
        
        # HTML dosyasını güncelle
        file_path = os.path.join(self.template_dir, f"{type}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        self.db.commit()
        return notification

    def list_notification_pages(self):
        """Tüm bildirim sayfalarını listele"""
        return self.db.query(NotificationPage).all()

    def toggle_notification_page(self, type: str, is_active: bool) -> NotificationPage:
        """Bildirim sayfasını aktif/pasif yap"""
        notification = self.get_notification_page(type)
        if notification:
            notification.is_active = is_active
            self.db.commit()
        return notification 