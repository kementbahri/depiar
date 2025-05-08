# Depiar API Dokümantasyonu

## Genel Bilgiler

- **Base URL**: `http://localhost:8000/api`
- **API Versiyonu**: 1.0.0
- **Format**: JSON
- **Kimlik Doğrulama**: JWT Bearer Token

## Kimlik Doğrulama

### Giriş Yapma
```http
POST /auth/login
```

**Request Body:**
```json
{
    "username": "string",
    "password": "string"
}
```

**Response:**
```json
{
    "access_token": "string",
    "token_type": "bearer"
}
```

## Bildirim Sayfaları

### Bildirim Sayfalarını Listeleme
```http
GET /notifications
```

**Response:**
```json
[
    {
        "id": 1,
        "type": "suspended",
        "title": "Hesap Askıya Alındı",
        "content": "string",
        "is_active": true
    }
]
```

### Bildirim Sayfası Oluşturma/Güncelleme
```http
PUT /notifications/{type}
```

**Request Body:**
```json
{
    "type": "string",
    "title": "string",
    "content": "string"
}
```

### Bildirim Sayfası Durumunu Değiştirme
```http
PATCH /notifications/{type}/toggle
```

**Query Parameters:**
- `is_active`: boolean

## Müşteri Yönetimi

### Müşteri Oluşturma
```http
POST /customers
```

**Request Body:**
```json
{
    "name": "string",
    "email": "string",
    "phone": "string",
    "address": "string"
}
```

### Müşteri Listeleme
```http
GET /customers
```

## Domain Yönetimi

### Domain Ekleme
```http
POST /domains
```

**Request Body:**
```json
{
    "name": "string",
    "customer_id": "integer",
    "server_id": "integer"
}
```

### Domain Listeleme
```http
GET /domains
```

## Rate Limiting

API'de rate limiting uygulanmıştır:

- Auth endpoints: 5 istek/dakika
- Domain endpoints: 10 istek/dakika
- Email endpoints: 10 istek/dakika
- Database endpoints: 10 istek/dakika
- Customer endpoints: 5 istek/dakika
- SSL endpoints: 5 istek/dakika
- Import endpoints: 2 istek/dakika

## Hata Kodları

- `400`: Bad Request - İstek formatı hatalı
- `401`: Unauthorized - Kimlik doğrulama gerekli
- `403`: Forbidden - Yetkisiz erişim
- `404`: Not Found - Kaynak bulunamadı
- `429`: Too Many Requests - Rate limit aşıldı
- `500`: Internal Server Error - Sunucu hatası

## Örnek Kullanım

### cURL ile Örnek
```bash
# Giriş yapma
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Bildirim sayfası oluşturma
curl -X PUT http://localhost:8000/api/notifications/suspended \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "suspended",
    "title": "Hesap Askıya Alındı",
    "content": "<html>...</html>"
  }'
```

### Python ile Örnek
```python
import requests

# Giriş yapma
response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"username": "admin", "password": "password"}
)
token = response.json()["access_token"]

# Bildirim sayfası oluşturma
headers = {"Authorization": f"Bearer {token}"}
response = requests.put(
    "http://localhost:8000/api/notifications/suspended",
    headers=headers,
    json={
        "type": "suspended",
        "title": "Hesap Askıya Alındı",
        "content": "<html>...</html>"
    }
) 