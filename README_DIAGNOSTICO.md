# 🔍 DIAGNÓSTICO COMPLETO - Dashboard Cobranzas

## 🎯 RESUMEN EJECUTIVO

**PROBLEMA**: La aplicación NO extrae datos de Odoo

**CAUSA PRINCIPAL**: Archivo `.env` no configurado o credenciales incorrectas

**SOLUCIÓN**: Seguir las instrucciones en este documento

---

## 📚 DOCUMENTACIÓN CREADA

He creado 6 archivos para ayudarte:

| Archivo | Propósito |
|---------|-----------|
| **EXPLICACION_PROYECTO.md** | Documentación técnica completa (300+ líneas) |
| **SOLUCION_RAPIDA.md** | Guía rápida para solucionar el problema |
| **INSTRUCCIONES_DIAGNOSTICO.md** | Pasos manuales detallados |
| **CORREGIR_CONECTAR_ODOO.md** | Corrección del bug en conectar_odoo.py |
| **verificar_env.py** | Script para verificar variables de entorno |
| **conectar_odoo_CORREGIDO.py** | Versión mejorada del script de prueba |

---

## ⚡ PASOS RÁPIDOS (EJECUTA ESTO)

### 1️⃣ Abrir PowerShell

```powershell
# Presiona Windows + R, escribe "powershell", Enter
```

### 2️⃣ Navegar al proyecto

```powershell
cd "C:\Users\jmontero\Desktop\GitHub Proyectos_AGV\dashboard-Cobranzas"
```

### 3️⃣ Verificar variables de entorno

```powershell
python verificar_env.py
```

**Esperado**: ✅ Todo en verde

**Si falla**: Abre `.env` y verifica que tenga estas 5 variables:
```env
ODOO_URL=https://tu-servidor.odoo.com
ODOO_DB=tu_base_datos
ODOO_USER=tu_usuario
ODOO_PASSWORD=tu_contraseña
SECRET_KEY=clave_secreta_123
```

### 4️⃣ Probar conexión a Odoo

```powershell
python conectar_odoo_CORREGIDO.py
```

**Esperado**: 
```
✅ ¡Conexión exitosa! Tu ID de usuario es: 123
✅ Se encontraron 5 productos:
   - ID: 1, Código: ABC, Nombre: Producto 1
   ...
```

### 5️⃣ Ejecutar la aplicación

```powershell
python app.py
```

**Esperado**: 
```
[OK] Conexion a Odoo establecida exitosamente.
[INFO] Iniciando Dashboard de Cobranzas...
 * Running on http://127.0.0.1:5002
```

### 6️⃣ Acceder a la aplicación

Abre el navegador y ve a: **http://127.0.0.1:5002/login**

---

## 🐛 PROBLEMA IDENTIFICADO EN conectar_odoo.py

### Bug encontrado:

**Línea 23**:
```python
common = xmlrpc.client.ServerProxy(f'https://{url}/xmlrpc/2/common')
#                                    ^^^^^^^^ Agrega https:// siempre
```

### Problema:
- Si tu `.env` tiene `ODOO_URL=https://servidor.com` → Resultado: `https://https://servidor.com` ❌
- Si tu `.env` tiene `ODOO_URL=servidor.com` → Resultado: `https://servidor.com` ✅

### Solución aplicada en `conectar_odoo_CORREGIDO.py`:

```python
# Detectar si la URL ya incluye el protocolo
if not url.startswith('http://') and not url.startswith('https://'):
    url_completa = f'https://{url}'
else:
    url_completa = url

common = xmlrpc.client.ServerProxy(f'{url_completa}/xmlrpc/2/common')
```

---

## 🔧 ERRORES COMUNES Y SOLUCIONES

### Error 1: Variables no configuradas

**Síntoma**:
```
❌ Error: Faltan variables en el archivo .env
```

**Solución**:
1. Verifica que existe `.env` en la carpeta del proyecto
2. Abre `.env` con un editor de texto
3. Asegúrate de tener las 5 variables con valores

---

### Error 2: URL incorrecta

**Síntoma**:
```
❌ No se pudo conectar al servidor en la URL 'xxx'
Error: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**Soluciones**:

**A) Si tu Odoo usa HTTPS**:
```env
ODOO_URL=https://tu-servidor.odoo.com
```

**B) Si tu Odoo usa HTTP** (menos común):
```env
ODOO_URL=http://tu-servidor.odoo.com
```

**C) Si tu Odoo está en localhost**:
```env
ODOO_URL=http://localhost:8069
```

---

### Error 3: Credenciales incorrectas

**Síntoma**:
```
❌ Error de autenticación. Credenciales incorrectas.
```

**Solución**:
1. Intenta iniciar sesión en Odoo desde el navegador
2. Si funciona en el navegador, copia exactamente esas credenciales al `.env`
3. Verifica que `ODOO_DB` sea el nombre correcto de la base de datos

---

### Error 4: Base de datos incorrecta

**Síntoma**:
```
❌ Error: Database 'xxx' does not exist
```

**Solución**:
1. Inicia sesión en Odoo desde el navegador
2. La URL después de login suele mostrar el nombre de la DB
3. Ejemplo: `https://servidor.odoo.com/web?db=mi_empresa`
4. Actualiza `.env` con el nombre correcto:
```env
ODOO_DB=mi_empresa
```

---

## 📊 ESTRUCTURA DEL PROYECTO (Simplificada)

```
dashboard-Cobranzas/
│
├── .env                          ⚠️ CRÍTICO - Credenciales
│
├── app.py                        🚀 Aplicación principal Flask
│
├── odoo_manager.py               📦 Wrapper de servicios
│
├── services/
│   ├── odoo_connection.py        🔌 Conexión a Odoo
│   ├── report_service.py         📊 Reportes CxC
│   └── cobranza_service.py       💰 KPIs cobranza
│
├── templates/                    🎨 HTML (Jinja2)
│   ├── login.html
│   ├── dashboard_clean.html
│   └── ...
│
├── static/                       🎨 CSS, JS, imágenes
│
└── utils/                        🛠️ Utilidades
    ├── calculators.py
    └── filters.py
```

---

## 🗑️ CÓDIGO DEPRECADO

### Archivos a eliminar:

1. **`INSTRUCCIONES_GOOGLE_SHEETS.md`** → Ya no se usa Google Sheets
2. **`conectar_odoo.py`** (después de probar) → Reemplazar por versión corregida
3. Carpeta `/test` (opcional) → Revisar si los tests son útiles

---

## ✅ CHECKLIST COMPLETO

### Configuración:
- [ ] Existe archivo `.env` en la carpeta del proyecto
- [ ] `.env` contiene las 5 variables con valores reales
- [ ] Ejecutar `python verificar_env.py` → Todo ✅

### Conexión:
- [ ] Ejecutar `python conectar_odoo_CORREGIDO.py` → Conexión exitosa
- [ ] Se obtienen productos de Odoo

### Aplicación:
- [ ] Ejecutar `python app.py` → Sin errores
- [ ] Ver mensaje `[OK] Conexion a Odoo establecida`
- [ ] Ir a http://127.0.0.1:5002/login
- [ ] Iniciar sesión con credenciales
- [ ] Dashboard muestra datos (tablas, gráficos)

---

## 💡 FLUJO DE DATOS

```
1. Usuario abre navegador
   ↓
2. Va a http://127.0.0.1:5002/login
   ↓
3. Flask (app.py) inicia
   ↓
4. Lee .env y conecta a Odoo (odoo_connection.py)
   ↓
5. Si conexión OK → Autentica usuario
   ↓
6. Usuario accede a /dashboard
   ↓
7. Flask llama data_manager.get_sales_lines()
   ↓
8. OdooManager → ReportService → OdooConnection
   ↓
9. XML-RPC → Odoo (consulta datos)
   ↓
10. Odoo responde con JSON
   ↓
11. Procesa datos (agrupa, calcula KPIs)
   ↓
12. Almacena en LOCAL_STORAGE (memoria)
   ↓
13. Renderiza template HTML
   ↓
14. Usuario ve dashboard con datos
```

**Si falla en paso 4 → No hay datos en ninguna página**

---

## 🆘 SI NECESITAS AYUDA

### Información que necesito si persiste el problema:

1. **Resultado de `python verificar_env.py`** (copia completa)
2. **Resultado de `python conectar_odoo_CORREGIDO.py`** (copia completa)
3. **Tipo de Odoo**:
   - Odoo Cloud (odoo.com)
   - Odoo On-Premise
   - Odoo.sh
   - Versión (11, 12, 13, 14, 15, 16, 17)
4. **¿Puedes acceder a Odoo desde el navegador?** (Sí/No)

---

## 📞 COMANDOS ÚTILES

```powershell
# Ver versión de Python
python --version

# Ver paquetes instalados
pip list

# Instalar dependencias
pip install -r requirements.txt

# Verificar .env
Get-Content .env

# Ejecutar app
python app.py
```

---

## 🎯 OBJETIVO FINAL

Al completar todos los pasos, deberías poder:

✅ Iniciar sesión en la aplicación
✅ Ver dashboard con gráficos de ventas
✅ Ver reportes de CxC
✅ Ver dashboard de cobranza internacional
✅ Gestionar metas por línea
✅ Gestionar metas por vendedor
✅ Exportar datos a Excel

---

**Fecha**: 10 de Octubre, 2025  
**Proyecto**: Dashboard Cobranzas - AGV Agrovet Market  
**Versión**: 4.1.0  
**Autor**: Claude Sonnet 4.5

