# Depiar

Depiar, web hosting ve sunucu yönetimi için geliştirilmiş açık kaynaklı kapsamlı bir kontrol panelidir.

## Özellikler

- Domain yönetimi
- DNS yönetimi
- SSL sertifika yönetimi
- Veritabanı yönetimi
- Dosya yönetimi
- FTP hesap yönetimi
- E-posta yönetimi
- Yedekleme ve geri yükleme
- Performans izleme
- Güvenlik yönetimi

## Kurulum

Detaylı kurulum talimatları için [Kurulum Kılavuzu](docs/deployment.md) dosyasını inceleyebilirsiniz.

### Gereksinimler

- Python 3.8+
- MySQL 5.7+
- Nginx
- Redis
- Node.js 14+

### Hızlı Başlangıç

1. Projeyi klonlayın:
```bash
git clone https://github.com/kementbahri/depiar.git
cd depiar
```

2. Backend bağımlılıklarını yükleyin:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Frontend bağımlılıklarını yükleyin:
```bash
cd ../frontend
npm install
```

4. Geliştirme sunucusunu başlatın:
```bash
# Backend
cd ../backend
uvicorn main:app --reload

# Frontend
cd ../frontend
npm start
```

## Katkıda Bulunma

1. Bu depoyu fork edin
2. Yeni bir branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Bir Pull Request oluşturun

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasını inceleyebilirsiniz.

## İletişim

Kement Bahri - [@kementbahri](https://github.com/kementbahri)

Proje Linki: [https://github.com/kementbahri/depiar](https://github.com/kementbahri/depiar)

## API Dokümantasyonu

API dokümantasyonu için [API Dokümantasyonu](backend/docs/api.md) dosyasını inceleyin.

## Teşekkürler

- FastAPI
- React
- Material-UI
- SQLAlchemy
- Ve diğer tüm açık kaynak projelere teşekkürler
