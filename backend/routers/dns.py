from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from ..database import get_db
from ..services.dns_service import DNSService
from ..models import DNSRecord, SPFRecord, DKIMRecord, DMARCRecord, DNSType
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(
    prefix="/api/dns",
    tags=["dns"]
)

# Request Models
class DNSRecordCreate(BaseModel):
    name: str
    type: DNSType
    content: str
    ttl: int = 3600
    priority: Optional[int] = None

class DNSRecordUpdate(BaseModel):
    content: str
    ttl: Optional[int] = None
    priority: Optional[int] = None

class SPFRecordCreate(BaseModel):
    mechanisms: List[str]
    qualifier: str = "+"

class DKIMRecordCreate(BaseModel):
    selector: str
    public_key: str
    algorithm: str = "rsa-sha256"
    key_type: str = "rsa"
    key_size: int = 2048

class DMARCRecordCreate(BaseModel):
    policy: str = "none"
    subdomain_policy: str = "none"
    percentage: int = 100
    report_aggregate: Optional[str] = None
    report_forensic: Optional[str] = None

# Response Models
class DNSRecordResponse(BaseModel):
    id: int
    domain_id: int
    name: str
    type: DNSType
    content: str
    ttl: int
    priority: Optional[int]
    is_active: bool
    is_managed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class SPFRecordResponse(BaseModel):
    id: int
    domain_id: int
    mechanisms: List[str]
    qualifier: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class DKIMRecordResponse(BaseModel):
    id: int
    domain_id: int
    selector: str
    public_key: str
    algorithm: str
    key_type: str
    key_size: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class DMARCRecordResponse(BaseModel):
    id: int
    domain_id: int
    policy: str
    subdomain_policy: str
    percentage: int
    report_aggregate: Optional[str]
    report_forensic: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class DNSVerificationResponse(BaseModel):
    spf: Dict
    dkim: Dict
    dmarc: Dict

# Routes
@router.post("/records/{domain_id}", response_model=DNSRecordResponse)
def create_dns_record(
    domain_id: int,
    record: DNSRecordCreate,
    db: Session = Depends(get_db)
):
    """DNS kaydı oluştur"""
    service = DNSService(db)
    try:
        return service.create_dns_record(
            domain_id=domain_id,
            name=record.name,
            type=record.type,
            content=record.content,
            ttl=record.ttl,
            priority=record.priority
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/records/{record_id}", response_model=DNSRecordResponse)
def update_dns_record(
    record_id: int,
    record: DNSRecordUpdate,
    db: Session = Depends(get_db)
):
    """DNS kaydını güncelle"""
    service = DNSService(db)
    try:
        return service.update_dns_record(
            record_id=record_id,
            content=record.content,
            ttl=record.ttl,
            priority=record.priority
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/records/{record_id}")
def delete_dns_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    """DNS kaydını sil"""
    service = DNSService(db)
    try:
        service.delete_dns_record(record_id)
        return {"message": "DNS record deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/spf/{domain_id}", response_model=SPFRecordResponse)
def create_spf_record(
    domain_id: int,
    record: SPFRecordCreate,
    db: Session = Depends(get_db)
):
    """SPF kaydı oluştur"""
    service = DNSService(db)
    try:
        return service.create_spf_record(
            domain_id=domain_id,
            mechanisms=record.mechanisms,
            qualifier=record.qualifier
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/dkim/{domain_id}", response_model=DKIMRecordResponse)
def create_dkim_record(
    domain_id: int,
    record: DKIMRecordCreate,
    db: Session = Depends(get_db)
):
    """DKIM kaydı oluştur"""
    service = DNSService(db)
    try:
        return service.create_dkim_record(
            domain_id=domain_id,
            selector=record.selector,
            public_key=record.public_key,
            algorithm=record.algorithm,
            key_type=record.key_type,
            key_size=record.key_size
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/dmarc/{domain_id}", response_model=DMARCRecordResponse)
def create_dmarc_record(
    domain_id: int,
    record: DMARCRecordCreate,
    db: Session = Depends(get_db)
):
    """DMARC kaydı oluştur"""
    service = DNSService(db)
    try:
        return service.create_dmarc_record(
            domain_id=domain_id,
            policy=record.policy,
            subdomain_policy=record.subdomain_policy,
            percentage=record.percentage,
            report_aggregate=record.report_aggregate,
            report_forensic=record.report_forensic
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/verify/{domain_id}", response_model=DNSVerificationResponse)
def verify_dns_records(
    domain_id: int,
    db: Session = Depends(get_db)
):
    """DNS kayıtlarını doğrula"""
    service = DNSService(db)
    try:
        return service.verify_dns_records(domain_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 