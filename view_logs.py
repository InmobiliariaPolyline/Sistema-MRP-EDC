#!/usr/bin/env python3
"""
Script para ver los registros de acceso a la BD
Ejecutar: python view_logs.py
"""

from database import SessionLocal
from models.login_log import LoginLog
from models.user import User
from datetime import datetime

def main():
    db = SessionLocal()
    
    print("\n" + "="*60)
    print("REGISTROS DE ACCESO AL SISTEMA MRP")
    print("="*60 + "\n")
    
    # Get login logs
    logs = db.query(LoginLog).order_by(LoginLog.login_time.desc()).all()
    
    if logs:
        print(f"Total de accesos registrados: {len(logs)}\n")
        print(f"{'ID':<5} | {'Usuario':<15} | {'Fecha y Hora':<25} | {'IP':<20}")
        print("-" * 75)
        
        for log in logs:
            ip = log.ip_address or "N/A"
            print(f"{log.id:<5} | {log.username:<15} | {log.login_time.strftime('%Y-%m-%d %H:%M:%S'):<25} | {ip:<20}")
    else:
        print("No hay registros de acceso aún.\n")
    
    print("\n" + "="*60)
    print("USUARIOS REGISTRADOS")
    print("="*60 + "\n")
    
    # Get users
    users = db.query(User).all()
    
    if users:
        print(f"Total de usuarios: {len(users)}\n")
        print(f"{'ID':<5} | {'Usuario':<20} | {'Email':<30} | {'Fecha Registro':<25}")
        print("-" * 85)
        
        for user in users:
            print(f"{user.id:<5} | {user.username:<20} | {user.email:<30} | {user.created_at.strftime('%Y-%m-%d %H:%M:%S'):<25}")
    else:
        print("No hay usuarios registrados.\n")
    
    db.close()

if __name__ == "__main__":
    main()
