import mysql.connector
import subprocess
import os
from datetime import datetime
from typing import Tuple, List, Dict
import json

class DatabaseManager:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def connect(self, database: str = None) -> mysql.connector.connection.MySQLConnection:
        """Veritabanına bağlan"""
        return mysql.connector.connect(
            host=self.host,
            port=self.port,
            user=self.username,
            password=self.password,
            database=database
        )

    def create_database(self, name: str, charset: str = "utf8mb4", collation: str = "utf8mb4_unicode_ci") -> bool:
        """Yeni veritabanı oluştur"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE {name} CHARACTER SET {charset} COLLATE {collation}")
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Database creation error: {str(e)}")
            return False

    def create_user(self, username: str, password: str, host: str = "localhost") -> bool:
        """Yeni kullanıcı oluştur"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(f"CREATE USER '{username}'@'{host}' IDENTIFIED BY '{password}'")
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"User creation error: {str(e)}")
            return False

    def grant_privileges(self, username: str, database: str, privileges: List[str], host: str = "localhost") -> bool:
        """Kullanıcıya yetki ver"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            privs = ", ".join(privileges)
            cursor.execute(f"GRANT {privs} ON {database}.* TO '{username}'@'{host}'")
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Privilege grant error: {str(e)}")
            return False

    def backup_database(self, database: str, backup_path: str, backup_type: str = "full") -> Tuple[bool, str]:
        """Veritabanı yedeği al"""
        try:
            # Yedekleme komutunu oluştur
            if backup_type == "full":
                cmd = f"mysqldump -h {self.host} -P {self.port} -u {self.username} -p{self.password} {database} > {backup_path}"
            elif backup_type == "structure":
                cmd = f"mysqldump -h {self.host} -P {self.port} -u {self.username} -p{self.password} --no-data {database} > {backup_path}"
            elif backup_type == "data":
                cmd = f"mysqldump -h {self.host} -P {self.port} -u {self.username} -p{self.password} --no-create-info {database} > {backup_path}"
            else:
                return False, "Invalid backup type"

            # Yedekleme işlemini çalıştır
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                return True, "Backup completed successfully"
            else:
                return False, f"Backup failed: {stderr.decode()}"

        except Exception as e:
            return False, f"Backup error: {str(e)}"

    def restore_database(self, database: str, backup_path: str) -> Tuple[bool, str]:
        """Veritabanı yedeğini geri yükle"""
        try:
            cmd = f"mysql -h {self.host} -P {self.port} -u {self.username} -p{self.password} {database} < {backup_path}"
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                return True, "Restore completed successfully"
            else:
                return False, f"Restore failed: {stderr.decode()}"

        except Exception as e:
            return False, f"Restore error: {str(e)}"

    def optimize_database(self, database: str) -> Tuple[bool, str, Dict]:
        """Veritabanını optimize et"""
        try:
            conn = self.connect(database)
            cursor = conn.cursor()

            # Tabloları listele
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()

            results = {
                "analyzed": [],
                "optimized": [],
                "repaired": []
            }

            # Her tablo için optimize işlemi
            for table in tables:
                table_name = table[0]
                
                # ANALYZE
                cursor.execute(f"ANALYZE TABLE {table_name}")
                results["analyzed"].append(table_name)
                
                # OPTIMIZE
                cursor.execute(f"OPTIMIZE TABLE {table_name}")
                results["optimized"].append(table_name)
                
                # REPAIR
                cursor.execute(f"REPAIR TABLE {table_name}")
                results["repaired"].append(table_name)

            cursor.close()
            conn.close()

            return True, "Database optimization completed", results

        except Exception as e:
            return False, f"Optimization error: {str(e)}", {}

    def get_database_size(self, database: str) -> int:
        """Veritabanı boyutunu hesapla (bytes)"""
        try:
            conn = self.connect(database)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT SUM(data_length + index_length) 
                FROM information_schema.TABLES 
                WHERE table_schema = %s
            """, (database,))
            
            size = cursor.fetchone()[0] or 0
            cursor.close()
            conn.close()
            
            return size

        except Exception as e:
            print(f"Size calculation error: {str(e)}")
            return 0

    def get_database_tables(self, database: str) -> List[Dict]:
        """Veritabanı tablolarını listele"""
        try:
            conn = self.connect(database)
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT 
                    table_name,
                    table_rows,
                    data_length,
                    index_length,
                    update_time
                FROM information_schema.TABLES 
                WHERE table_schema = %s
            """, (database,))
            
            tables = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return tables

        except Exception as e:
            print(f"Table list error: {str(e)}")
            return [] 