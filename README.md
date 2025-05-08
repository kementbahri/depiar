# Depiar - Hosting Control Panel

Depiar, modern ve kullanıcı dostu bir hosting kontrol panelidir. PHP, MySQL, Nginx/Apache yönetimi, SSL sertifikaları, e-posta hesapları ve daha fazlasını tek bir arayüzden yönetmenizi sağlar.

## Özellikler

- 🚀 Modern ve Hızlı Arayüz
- 🔒 Güvenli Kimlik Doğrulama
- 🌐 Domain ve DNS Yönetimi
- 📧 E-posta Hesap Yönetimi
- 💾 Veritabanı Yönetimi
- 🔐 SSL Sertifika Yönetimi
- 📁 Dosya Yöneticisi
- 📊 İstatistik ve Raporlama
- 🔄 Otomatik Yedekleme
- 🌍 Çoklu Dil Desteği

## Kurulum

Detaylı kurulum talimatları için [Deployment Kılavuzu](docs/deployment.md) dosyasını inceleyin.

### Hızlı Başlangıç

1. Gereksinimleri yükleyin:
```bash
pip install -r requirements.txt
```

2. Veritabanını oluşturun:
```bash
python backend/setup_server.py
```

3. Uygulamayı başlatın:
```bash
cd backend
uvicorn main:app --reload
```

4. Frontend'i başlatın:
```bash
cd frontend
npm install
npm start
```

## API Dokümantasyonu

API dokümantasyonu için [API Dokümantasyonu](backend/docs/api.md) dosyasını inceleyin.

## Katkıda Bulunma

1. Bu depoyu fork edin
2. Yeni bir branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Bir Pull Request oluşturun

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasını inceleyin.

## İletişim

- Website: [https://depiar.com](https://depiar.com)
- E-posta: support@depiar.com
- GitHub: [https://github.com/your-repo/depiar](https://github.com/your-repo/depiar)

## Teşekkürler

- FastAPI
- React
- Material-UI
- SQLAlchemy
- Ve diğer tüm açık kaynak projelere teşekkürler 