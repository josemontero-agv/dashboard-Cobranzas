# -*- coding: utf-8 -*-
"""
Script de Diagnóstico - Dashboard Cobranzas
Verifica la configuración y conexión con Odoo
"""

import os
from dotenv import load_dotenv

def verificar_env():
    """Verifica las variables de entorno"""
    print("\n" + "="*60)
    print("🔍 DIAGNÓSTICO DE CONFIGURACIÓN")
    print("="*60)
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Variables requeridas
    vars_requeridas = {
        'ODOO_URL': os.getenv('ODOO_URL'),
        'ODOO_DB': os.getenv('ODOO_DB'),
        'ODOO_USER': os.getenv('ODOO_USER'),
        'ODOO_PASSWORD': os.getenv('ODOO_PASSWORD'),
        'SECRET_KEY': os.getenv('SECRET_KEY')
    }
    
    print("\n📋 Variables de Entorno:")
    print("-" * 60)
    
    todas_configuradas = True
    for var, valor in vars_requeridas.items():
        if valor:
            # Ocultar contraseñas
            if 'PASSWORD' in var or 'KEY' in var:
                display = f"{valor[:3]}...{valor[-3:]}" if len(valor) > 6 else "***"
            else:
                display = valor
            print(f"  ✅ {var:<20} = {display}")
        else:
            print(f"  ❌ {var:<20} = [NO CONFIGURADA]")
            todas_configuradas = False
    
    if not todas_configuradas:
        print("\n⚠️  ADVERTENCIA: Faltan variables de entorno")
        print("   Crea un archivo .env con todas las variables requeridas")
        return False
    
    print("\n✅ Todas las variables están configuradas")
    return True


def probar_conexion():
    """Prueba la conexión con Odoo"""
    print("\n" + "="*60)
    print("🔌 PROBANDO CONEXIÓN A ODOO")
    print("="*60)
    
    try:
        from services.odoo_connection import OdooConnection
        
        print("\n⏳ Intentando conectar...")
        conn = OdooConnection()
        
        if conn.is_connected():
            print("✅ ¡CONEXIÓN EXITOSA!")
            print(f"   URL: {conn.url}")
            print(f"   Base de datos: {conn.db}")
            print(f"   Usuario: {conn.username}")
            print(f"   UID: {conn.uid}")
            return True
        else:
            print("❌ NO SE PUDO CONECTAR")
            print("   Verifica tus credenciales en el archivo .env")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def probar_extraccion_datos():
    """Prueba la extracción de datos básicos"""
    print("\n" + "="*60)
    print("📊 PROBANDO EXTRACCIÓN DE DATOS")
    print("="*60)
    
    try:
        from odoo_manager import OdooManager
        from datetime import datetime, timedelta
        
        manager = OdooManager()
        
        if not manager.connection.is_connected():
            print("❌ No hay conexión a Odoo")
            return False
        
        # Probar obtener vendedores
        print("\n⏳ Obteniendo vendedores...")
        vendedores = manager.get_all_sellers()
        print(f"✅ Se encontraron {len(vendedores)} vendedores")
        if vendedores:
            print(f"   Ejemplo: {vendedores[0]['name']}")
        
        # Probar obtener líneas de venta
        print("\n⏳ Obteniendo líneas de venta...")
        fecha_fin = datetime.now().strftime('%Y-%m-%d')
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        ventas = manager.get_sales_lines(
            date_from=fecha_inicio,
            date_to=fecha_fin,
            limit=10
        )
        
        print(f"✅ Se encontraron {len(ventas)} líneas de venta (últimos 30 días, límite 10)")
        if ventas:
            venta = ventas[0]
            print(f"   Ejemplo:")
            print(f"   - Producto: {venta.get('name', 'N/A')}")
            print(f"   - Balance: {venta.get('balance', 0)}")
            print(f"   - Fecha: {venta.get('date', 'N/A')}")
        
        # Probar opciones de filtro
        print("\n⏳ Obteniendo opciones de filtro...")
        opciones = manager.get_filter_options()
        print(f"✅ Líneas comerciales: {len(opciones.get('lineas', []))}")
        print(f"✅ Clientes: {len(opciones.get('clientes', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def verificar_archivos():
    """Verifica que existan los archivos necesarios"""
    print("\n" + "="*60)
    print("📁 VERIFICANDO ARCHIVOS")
    print("="*60)
    
    archivos_requeridos = [
        'app.py',
        'odoo_manager.py',
        'requirements.txt',
        '.env',
        'services/odoo_connection.py',
        'services/report_service.py',
        'services/cobranza_service.py',
        'utils/calculators.py',
        'utils/filters.py'
    ]
    
    print("\n📂 Archivos requeridos:")
    print("-" * 60)
    
    todos_existen = True
    for archivo in archivos_requeridos:
        existe = os.path.exists(archivo)
        icono = "✅" if existe else "❌"
        print(f"  {icono} {archivo}")
        if not existe:
            todos_existen = False
    
    if todos_existen:
        print("\n✅ Todos los archivos existen")
    else:
        print("\n⚠️  Faltan algunos archivos")
    
    return todos_existen


def main():
    """Ejecuta todos los diagnósticos"""
    print("\n╔" + "="*58 + "╗")
    print("║  🔧 DIAGNÓSTICO COMPLETO - DASHBOARD COBRANZAS          ║")
    print("╚" + "="*58 + "╝")
    
    # 1. Verificar archivos
    archivos_ok = verificar_archivos()
    
    # 2. Verificar variables de entorno
    env_ok = verificar_env()
    
    # 3. Probar conexión
    if env_ok:
        conexion_ok = probar_conexion()
    else:
        print("\n⚠️  Saltando prueba de conexión (falta configuración)")
        conexion_ok = False
    
    # 4. Probar extracción de datos
    if conexion_ok:
        datos_ok = probar_extraccion_datos()
    else:
        print("\n⚠️  Saltando prueba de datos (no hay conexión)")
        datos_ok = False
    
    # Resumen final
    print("\n" + "="*60)
    print("📊 RESUMEN DEL DIAGNÓSTICO")
    print("="*60)
    
    print(f"\n  {'✅' if archivos_ok else '❌'} Archivos del proyecto")
    print(f"  {'✅' if env_ok else '❌'} Variables de entorno")
    print(f"  {'✅' if conexion_ok else '❌'} Conexión a Odoo")
    print(f"  {'✅' if datos_ok else '❌'} Extracción de datos")
    
    if archivos_ok and env_ok and conexion_ok and datos_ok:
        print("\n✅ ¡TODO ESTÁ FUNCIONANDO CORRECTAMENTE!")
        print("   La aplicación debería extraer datos sin problemas")
    else:
        print("\n⚠️  HAY PROBLEMAS QUE RESOLVER:")
        if not archivos_ok:
            print("   - Verifica que todos los archivos estén presentes")
        if not env_ok:
            print("   - Configura el archivo .env con las credenciales correctas")
        if not conexion_ok:
            print("   - Verifica la URL y credenciales de Odoo")
        if not datos_ok:
            print("   - Revisa los logs de error anteriores")
    
    print("\n" + "="*60)
    print("💡 Para más información, consulta EXPLICACION_PROYECTO.md")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()

