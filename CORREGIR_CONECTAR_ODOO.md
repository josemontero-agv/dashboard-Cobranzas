# 🔧 CORRECCIÓN PARA conectar_odoo.py

## ⚠️ PROBLEMA DETECTADO

El archivo `conectar_odoo.py` tiene un bug en las líneas 23 y 37:

```python
common = xmlrpc.client.ServerProxy(f'https://{url}/xmlrpc/2/common')
#                                    ^^^^^^^^ PROBLEMA AQUÍ
```

**El problema**: Agrega `https://` automáticamente, pero tu `.env` podría ya incluirlo en `ODOO_URL`.

---

## ✅ SOLUCIÓN

### Opción 1: Modificar el .env (MÁS FÁCIL)

Asegúrate de que tu `.env` tenga la URL COMPLETA:

```env
ODOO_URL=https://tu-servidor.odoo.com
# NO DEBE SER: ODOO_URL=tu-servidor.odoo.com
```

Y luego modifica `conectar_odoo.py`:

**ANTES** (líneas 23 y 37):
```python
common = xmlrpc.client.ServerProxy(f'https://{url}/xmlrpc/2/common')
models = xmlrpc.client.ServerProxy(f'https://{url}/xmlrpc/2/object')
```

**DESPUÉS**:
```python
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
```

---

### Opción 2: Dejar conectar_odoo.py como está

Si tu URL NO incluye el protocolo, déjala así en el `.env`:

```env
ODOO_URL=tu-servidor.odoo.com
```

Y `conectar_odoo.py` agregará `https://` automáticamente.

---

## 🎯 ARCHIVO CORREGIDO COMPLETO

He creado una versión corregida. Copia este contenido completo:

```python
# -*- coding: utf-8 -*-
import xmlrpc.client
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Leer credenciales
url = os.getenv('ODOO_URL')
db = os.getenv('ODOO_DB')
username = os.getenv('ODOO_USER')
password = os.getenv('ODOO_PASSWORD')

# Verificar que todas las variables estén configuradas
if not all([url, db, username, password]):
    print("❌ Error: Faltan variables en el archivo .env")
    print("   Variables requeridas: ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD")
    exit()

print("\n" + "="*60)
print("🔍 PROBANDO CONEXIÓN A ODOO")
print("="*60)
print(f"\n📋 Configuración:")
print(f"   URL: {url}")
print(f"   Base de datos: {db}")
print(f"   Usuario: {username}")
print(f"   Contraseña: {'*' * len(password)}")

# Detectar si la URL ya incluye el protocolo
if not url.startswith('http://') and not url.startswith('https://'):
    url_completa = f'https://{url}'
    print(f"\n⚠️  Agregando protocolo HTTPS: {url_completa}")
else:
    url_completa = url
    print(f"\n✅ URL ya incluye protocolo: {url_completa}")

# Autenticación
print(f"\n⏳ Conectando a {url_completa}...")
common = xmlrpc.client.ServerProxy(f'{url_completa}/xmlrpc/2/common')

try:
    uid = common.authenticate(db, username, password, {})
    if uid:
        print(f"✅ ¡Conexión exitosa! Tu ID de usuario es: {uid}")
    else:
        print("❌ Error de autenticación. Credenciales incorrectas.")
        print("   Verifica ODOO_USER y ODOO_PASSWORD en tu archivo .env")
        exit()
except Exception as e:
    print(f"❌ No se pudo conectar al servidor.")
    print(f"   Error: {e}")
    print("\n💡 Posibles causas:")
    print("   1. La URL está mal escrita")
    print("   2. El servidor no está disponible")
    print("   3. No tienes conexión a internet")
    print("   4. El servidor usa HTTP en lugar de HTTPS")
    exit()

# Obtener datos de prueba
models = xmlrpc.client.ServerProxy(f'{url_completa}/xmlrpc/2/object')

print("\n⏳ Buscando los primeros 5 productos...")

try:
    product_ids = models.execute_kw(
        db, uid, password, 
        'product.product', 'search', 
        [[]], 
        {'limit': 5}
    )

    if not product_ids:
        print("⚠️  No se encontraron productos en Odoo.")
    else:
        products = models.execute_kw(
            db, uid, password, 
            'product.product', 'read', 
            [product_ids], 
            {'fields': ['id', 'name', 'default_code']}
        )
        
        print(f"✅ Se encontraron {len(products)} productos:")
        for product in products:
            print(f"   - ID: {product.get('id')}, "
                  f"Código: {product.get('default_code', 'N/A')}, "
                  f"Nombre: {product.get('name')}")

except Exception as e:
    print(f"❌ Error al consultar productos: {e}")

print("\n" + "="*60)
print("✅ Prueba de conexión completada")
print("="*60 + "\n")
```

---

## 📝 CÓMO APLICAR LA CORRECCIÓN

1. Abre el archivo `conectar_odoo.py`
2. **REEMPLAZA TODO EL CONTENIDO** con el código de arriba
3. Guarda el archivo
4. Ejecuta de nuevo: `python conectar_odoo.py`

---

## 🎯 AHORA DEBERÍA FUNCIONAR

El script corregido:
- ✅ Detecta automáticamente si la URL ya tiene protocolo
- ✅ Muestra información detallada de la configuración
- ✅ Maneja mejor los errores
- ✅ Da sugerencias específicas si falla

---

**Creado**: 10 de Octubre, 2025

