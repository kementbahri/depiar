import psutil
import subprocess
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from ..models import ServerMetric, SecurityAlert, IPBlock, SystemUpdate, MalwareScan, MalwareThreat, SSHServer
import threading
import schedule
import time
import json
import requests
from ..utils.ssh import SSHManager

logger = logging.getLogger(__name__)

class MonitoringService:
    def __init__(self, db: Session):
        self.db = db
        self.alert_thresholds = {
            "cpu_usage": 90,  # %90 CPU kullanımı
            "memory_usage": 85,  # %85 RAM kullanımı
            "disk_usage": 90,  # %90 Disk kullanımı
        }

    def collect_metrics(self, server_id: int) -> ServerMetric:
        """Sunucu metriklerini topla"""
        server = self.db.query(SSHServer).filter(SSHServer.id == server_id).first()
        if not server:
            raise ValueError("Server not found")

        ssh = SSHManager(server.host, server.port, server.username, server.password)
        
        try:
            # CPU kullanımı
            cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'"
            cpu_usage = float(ssh.execute_command(cpu_cmd)[0].strip())

            # RAM kullanımı
            mem_cmd = "free | grep Mem | awk '{print $3/$2 * 100.0}'"
            memory_usage = float(ssh.execute_command(mem_cmd)[0].strip())

            # Disk kullanımı
            disk_cmd = "df / | tail -1 | awk '{print $5}' | sed 's/%//'"
            disk_usage = float(ssh.execute_command(disk_cmd)[0].strip())

            # Ağ trafiği
            net_cmd = "cat /proc/net/dev | grep eth0"
            net_info = ssh.execute_command(net_cmd)[0].split()
            network_in = int(net_info[1])
            network_out = int(net_info[9])

            # Uptime
            uptime_cmd = "cat /proc/uptime | awk '{print $1}'"
            uptime = int(float(ssh.execute_command(uptime_cmd)[0].strip()))

            # Load average
            load_cmd = "cat /proc/loadavg | awk '{print $1,$2,$3}'"
            load_average = ssh.execute_command(load_cmd)[0].strip()

            # Metrikleri kaydet
            metric = ServerMetric(
                server_id=server.id,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_in=network_in,
                network_out=network_out,
                uptime=uptime,
                load_average=load_average
            )
            self.db.add(metric)
            self.db.commit()

            # Uyarıları kontrol et
            self._check_alerts(server, metric)

            return metric

        except Exception as e:
            logger.error(f"Metric collection failed: {str(e)}")
            raise

    def check_security(self, server_id: int):
        """Güvenlik kontrollerini yap"""
        server = self.db.query(SSHServer).filter(SSHServer.id == server_id).first()
        if not server:
            raise ValueError("Server not found")

        ssh = SSHManager(server.host, server.port, server.username, server.password)

        try:
            # ModSecurity loglarını kontrol et
            modsec_cmd = "tail -n 100 /var/log/modsec_audit.log | grep -i 'attack'"
            modsec_logs = ssh.execute_command(modsec_cmd)
            for log in modsec_logs:
                self._create_security_alert(
                    server,
                    "modsecurity",
                    "high",
                    log,
                    log.split()[0] if log else None
                )

            # Fail2ban loglarını kontrol et
            fail2ban_cmd = "tail -n 100 /var/log/fail2ban.log | grep -i 'ban'"
            fail2ban_logs = ssh.execute_command(fail2ban_cmd)
            for log in fail2ban_logs:
                ip = log.split()[6] if len(log.split()) > 6 else None
                if ip:
                    self._block_ip(server, ip, "fail2ban")

            # Güvenlik duvarı durumunu kontrol et
            firewall_cmd = "ufw status | grep 'Status: active'"
            firewall_status = ssh.execute_command(firewall_cmd)
            if not firewall_status:
                self._create_security_alert(
                    server,
                    "firewall",
                    "high",
                    "Firewall is not active"
                )

        except Exception as e:
            logger.error(f"Security check failed: {str(e)}")
            raise

    def check_updates(self, server_id: int):
        """Sistem güncellemelerini kontrol et"""
        server = self.db.query(SSHServer).filter(SSHServer.id == server_id).first()
        if not server:
            raise ValueError("Server not found")

        ssh = SSHManager(server.host, server.port, server.username, server.password)

        try:
            # Güncellemeleri kontrol et
            update_cmd = "apt list --upgradable"
            updates = ssh.execute_command(update_cmd)

            for update in updates:
                if "Listing..." not in update:
                    package, version = update.split("/")[0], update.split(" ")[1]
                    self._create_system_update(server, package, version)

        except Exception as e:
            logger.error(f"Update check failed: {str(e)}")
            raise

    def scan_malware(self, server_id: int, scan_type: str = "quick"):
        """Malware taraması yap"""
        server = self.db.query(SSHServer).filter(SSHServer.id == server_id).first()
        if not server:
            raise ValueError("Server not found")

        ssh = SSHManager(server.host, server.port, server.username, server.password)

        try:
            # Tarama kaydı oluştur
            scan = MalwareScan(
                server_id=server.id,
                scan_type=scan_type,
                status="running",
                scan_path="/var/www"
            )
            self.db.add(scan)
            self.db.commit()

            # ClamAV ile tarama yap
            if scan_type == "full":
                scan_cmd = "clamscan -r /var/www"
            else:
                scan_cmd = "clamscan -r --quick /var/www"

            scan_result = ssh.execute_command(scan_cmd)
            
            # Sonuçları işle
            threats_found = 0
            for line in scan_result:
                if "FOUND" in line:
                    threats_found += 1
                    file_path = line.split(":")[0]
                    threat_type = line.split(":")[1].split(" ")[1]
                    
                    threat = MalwareThreat(
                        scan_id=scan.id,
                        file_path=file_path,
                        threat_type=threat_type,
                        severity="high"
                    )
                    self.db.add(threat)

            # Tarama sonuçlarını güncelle
            scan.status = "completed"
            scan.threats_found = threats_found
            scan.completed_at = datetime.utcnow()
            self.db.commit()

            return scan

        except Exception as e:
            scan.status = "failed"
            self.db.commit()
            logger.error(f"Malware scan failed: {str(e)}")
            raise

    def _check_alerts(self, server: SSHServer, metric: ServerMetric):
        """Metrikleri kontrol et ve gerekirse uyarı oluştur"""
        if metric.cpu_usage > self.alert_thresholds["cpu_usage"]:
            self._create_security_alert(
                server,
                "performance",
                "high",
                f"High CPU usage: {metric.cpu_usage}%"
            )

        if metric.memory_usage > self.alert_thresholds["memory_usage"]:
            self._create_security_alert(
                server,
                "performance",
                "high",
                f"High memory usage: {metric.memory_usage}%"
            )

        if metric.disk_usage > self.alert_thresholds["disk_usage"]:
            self._create_security_alert(
                server,
                "performance",
                "high",
                f"High disk usage: {metric.disk_usage}%"
            )

    def _create_security_alert(
        self,
        server: SSHServer,
        alert_type: str,
        severity: str,
        message: str,
        source_ip: Optional[str] = None
    ):
        """Güvenlik uyarısı oluştur"""
        alert = SecurityAlert(
            server_id=server.id,
            type=alert_type,
            severity=severity,
            message=message,
            source_ip=source_ip
        )
        self.db.add(alert)
        self.db.commit()

    def _block_ip(self, server: SSHServer, ip: str, reason: str):
        """IP adresini engelle"""
        block = IPBlock(
            server_id=server.id,
            ip_address=ip,
            reason=reason,
            expires_at=datetime.utcnow() + timedelta(days=1)
        )
        self.db.add(block)
        self.db.commit()

    def _create_system_update(
        self,
        server: SSHServer,
        package_name: str,
        available_version: str
    ):
        """Sistem güncellemesi kaydı oluştur"""
        update = SystemUpdate(
            server_id=server.id,
            package_name=package_name,
            available_version=available_version,
            update_type="security" if "security" in package_name.lower() else "bugfix"
        )
        self.db.add(update)
        self.db.commit()

def start_monitoring_scheduler():
    """İzleme zamanlayıcısını başlat"""
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)

    # Her 5 dakikada bir metrik topla
    schedule.every(5).minutes.do(collect_all_metrics)
    
    # Her saat güvenlik kontrolü yap
    schedule.every().hour.do(check_all_security)
    
    # Her gün güncelleme kontrolü yap
    schedule.every().day.at("03:00").do(check_all_updates)
    
    # Her hafta malware taraması yap
    schedule.every().monday.at("02:00").do(scan_all_malware)

    # Zamanlayıcıyı arka planda çalıştır
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

def collect_all_metrics():
    """Tüm sunucuların metriklerini topla"""
    db = Session()
    monitoring = MonitoringService(db)
    
    servers = db.query(SSHServer).all()
    for server in servers:
        try:
            monitoring.collect_metrics(server.id)
        except Exception as e:
            logger.error(f"Failed to collect metrics for server {server.id}: {str(e)}")
    
    db.close()

def check_all_security():
    """Tüm sunucuların güvenlik kontrolünü yap"""
    db = Session()
    monitoring = MonitoringService(db)
    
    servers = db.query(SSHServer).all()
    for server in servers:
        try:
            monitoring.check_security(server.id)
        except Exception as e:
            logger.error(f"Failed to check security for server {server.id}: {str(e)}")
    
    db.close()

def check_all_updates():
    """Tüm sunucuların güncellemelerini kontrol et"""
    db = Session()
    monitoring = MonitoringService(db)
    
    servers = db.query(SSHServer).all()
    for server in servers:
        try:
            monitoring.check_updates(server.id)
        except Exception as e:
            logger.error(f"Failed to check updates for server {server.id}: {str(e)}")
    
    db.close()

def scan_all_malware():
    """Tüm sunucularda malware taraması yap"""
    db = Session()
    monitoring = MonitoringService(db)
    
    servers = db.query(SSHServer).all()
    for server in servers:
        try:
            monitoring.scan_malware(server.id)
        except Exception as e:
            logger.error(f"Failed to scan malware for server {server.id}: {str(e)}")
    
    db.close() 