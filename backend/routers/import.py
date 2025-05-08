from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
import os
import shutil
import xml.etree.ElementTree as ET
import tarfile
import zipfile
import json
from datetime import datetime
from ..database import get_db
from ..models import Customer, Domain, EmailAccount, Database, SSL
from sqlalchemy.orm import Session
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def process_cpanel_import(file_path: str, db: Session):
    """cPanel dışa aktarma dosyasını işle"""
    try:
        # Dosya türünü belirle
        if file_path.endswith('.tar.gz'):
            with tarfile.open(file_path, 'r:gz') as tar:
                tar.extractall(path=UPLOAD_DIR)
        elif file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(UPLOAD_DIR)

        # cPanel yapılandırma dosyasını bul
        config_file = os.path.join(UPLOAD_DIR, 'cpanel.json')
        if not os.path.exists(config_file):
            raise HTTPException(status_code=400, detail="Geçersiz cPanel dışa aktarma dosyası")

        with open(config_file, 'r') as f:
            config = json.load(f)

        # Müşteri bilgilerini içe aktar
        customer = Customer(
            name=config.get('user', ''),
            email=config.get('email', ''),
            status='active',
            package='basic'
        )
        db.add(customer)
        db.flush()

        # Domainleri içe aktar
        for domain in config.get('domains', []):
            domain_obj = Domain(
                customer_id=customer.id,
                name=domain['name'],
                status='active'
            )
            db.add(domain_obj)

        # E-posta hesaplarını içe aktar
        for email in config.get('email_accounts', []):
            email_obj = EmailAccount(
                customer_id=customer.id,
                domain_id=domain_obj.id,
                username=email['username'],
                password=email['password'],
                quota=email.get('quota', 0)
            )
            db.add(email_obj)

        # Veritabanlarını içe aktar
        for db_info in config.get('databases', []):
            db_obj = Database(
                customer_id=customer.id,
                name=db_info['name'],
                username=db_info['username'],
                password=db_info['password']
            )
            db.add(db_obj)

        # SSL sertifikalarını içe aktar
        for ssl in config.get('ssl_certificates', []):
            ssl_obj = SSL(
                customer_id=customer.id,
                domain_id=domain_obj.id,
                certificate=ssl['certificate'],
                private_key=ssl['private_key'],
                expiry_date=datetime.fromisoformat(ssl['expiry_date'])
            )
            db.add(ssl_obj)

        db.commit()
        return True

    except Exception as e:
        logger.error(f"cPanel içe aktarma hatası: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def process_plesk_import(file_path: str, db: Session):
    """Plesk dışa aktarma dosyasını işle"""
    try:
        # Dosya türünü belirle
        if file_path.endswith('.xml'):
            with open(file_path, 'r') as f:
                xml_content = f.read()
        elif file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                xml_file = [f for f in zip_ref.namelist() if f.endswith('.xml')][0]
                xml_content = zip_ref.read(xml_file).decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail="Geçersiz Plesk dışa aktarma dosyası")

        # XML'i parse et
        root = ET.fromstring(xml_content)

        # Müşteri bilgilerini içe aktar
        customer = Customer(
            name=root.find('.//client/name').text,
            email=root.find('.//client/email').text,
            status='active',
            package='basic'
        )
        db.add(customer)
        db.flush()

        # Domainleri içe aktar
        for domain_elem in root.findall('.//domain'):
            domain_obj = Domain(
                customer_id=customer.id,
                name=domain_elem.find('name').text,
                status='active'
            )
            db.add(domain_obj)

            # E-posta hesaplarını içe aktar
            for mail_elem in domain_elem.findall('.//mail'):
                email_obj = EmailAccount(
                    customer_id=customer.id,
                    domain_id=domain_obj.id,
                    username=mail_elem.find('name').text,
                    password=mail_elem.find('password').text,
                    quota=int(mail_elem.find('quota').text)
                )
                db.add(email_obj)

            # Veritabanlarını içe aktar
            for db_elem in domain_elem.findall('.//database'):
                db_obj = Database(
                    customer_id=customer.id,
                    name=db_elem.find('name').text,
                    username=db_elem.find('username').text,
                    password=db_elem.find('password').text
                )
                db.add(db_obj)

            # SSL sertifikalarını içe aktar
            for ssl_elem in domain_elem.findall('.//ssl'):
                ssl_obj = SSL(
                    customer_id=customer.id,
                    domain_id=domain_obj.id,
                    certificate=ssl_elem.find('certificate').text,
                    private_key=ssl_elem.find('private_key').text,
                    expiry_date=datetime.fromisoformat(ssl_elem.find('expiry_date').text)
                )
                db.add(ssl_obj)

        db.commit()
        return True

    except Exception as e:
        logger.error(f"Plesk içe aktarma hatası: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
async def import_data(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    type: str = "cpanel"
):
    """Dışa aktarma dosyasını içe aktar"""
    try:
        # Dosya uzantısını kontrol et
        file_ext = os.path.splitext(file.filename)[1].lower()
        if type == "cpanel" and file_ext not in ['.tar.gz', '.zip']:
            raise HTTPException(status_code=400, detail="Geçersiz dosya formatı. TAR.GZ veya ZIP dosyası yükleyin.")
        elif type == "plesk" and file_ext not in ['.xml', '.zip']:
            raise HTTPException(status_code=400, detail="Geçersiz dosya formatı. XML veya ZIP dosyası yükleyin.")

        # Dosyayı kaydet
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Veritabanı bağlantısını al
        db = next(get_db())

        # İçe aktarma işlemini başlat
        if type == "cpanel":
            success = await process_cpanel_import(file_path, db)
        else:
            success = await process_plesk_import(file_path, db)

        # Geçici dosyaları temizle
        background_tasks.add_task(lambda: os.remove(file_path))
        background_tasks.add_task(lambda: shutil.rmtree(UPLOAD_DIR, ignore_errors=True))

        return JSONResponse(
            content={"success": success, "message": "İçe aktarma başarıyla tamamlandı"}
        )

    except Exception as e:
        logger.error(f"İçe aktarma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 