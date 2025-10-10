# -*- coding: utf-8 -*-
"""
Script simple para verificar las variables de entorno
"""

from dotenv import load_dotenv
import os

print("\n" + "="*60)
print("🔍 VERIFICACIÓN DE VARIABLES DE ENTORNO")
print("="*60)

# Cargar .env
load_dotenv()

# Variables requeridas
vars_requeridas = {
    'ODOO_URL': os.getenv('ODOO_URL'),
    'ODOO_DB': os.getenv('ODOO_DB'),
    'ODOO_USER': os.getenv('ODOO_USER'),
    'ODOO_PASSWORD': os.getenv('ODOO_PASSWORD'),
    'SECRET_KEY': os.getenv('SECRET_KEY')
}

print("\n📋 Estado de variables:")
print("-" * 60)

todas_ok = True
for var, valor in vars_requeridas.items():
    if valor:
        # Ocultar contraseñas
        if 'PASSWORD' in var or 'KEY' in var:
            display = "***configurada***"
        else:
            display = valor
        print(f"✅ {var:<20} = {display}")
    else:
        print(f"❌ {var:<20} = NO CONFIGURADA")
        todas_ok = False

print("-" * 60)

if todas_ok:
    print("\n✅ Todas las variables están configuradas correctamente")
    print("\nAhora ejecuta: python conectar_odoo.py")
else:
    print("\n❌ FALTAN VARIABLES EN EL ARCHIVO .env")
    print("\nAsegúrate de tener un archivo .env con este formato:")
    print("""
ODOO_URL=tu-servidor-odoo.com
ODOO_DB=nombre_base_datos
ODOO_USER=tu_usuario
ODOO_PASSWORD=tu_contraseña
SECRET_KEY=clave_secreta_123
    """)

print("="*60 + "\n")

