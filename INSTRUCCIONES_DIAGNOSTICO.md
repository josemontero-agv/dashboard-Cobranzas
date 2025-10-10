# 🔍 INSTRUCCIONES PARA DIAGNOSTICAR EL PROBLEMA

## ⚠️ Tu antivirus está bloqueando los comandos automáticos

Por favor, ejecuta estos comandos **MANUALMENTE** en PowerShell o CMD.

---

## PASO 1: Abrir PowerShell

1. Presiona `Windows + R`
2. Escribe `powershell`
3. Presiona Enter

---

## PASO 2: Navegar al proyecto

```powershell
cd "C:\Users\jmontero\Desktop\GitHub Proyectos_AGV\dashboard-Cobranzas"
```

---

## PASO 3: Verificar archivo .env

### Opción A: Ver contenido del .env

```powershell
Get-Content .env
```

**Debes ver algo como esto:**
```
ODOO_URL=https://tu-servidor.odoo.com
ODOO_DB=nombre_db
ODOO_USER=tu_usuario
ODOO_PASSWORD=tu_contraseña
SECRET_KEY=clave_secreta_123
```

### Opción B: Verificar variables con Python

```powershell
python verificar_env.py
```

---

## PASO 4: Probar conexión a Odoo

```powershell
python conectar_odoo.py
```

### **POSIBLES RESULTADOS:**

#### ✅ **SI FUNCIONA** (verás esto):
```
✅ ¡Conexión exitosa! Tu ID de usuario es: 123

Buscando los primeros 5 productos...
✅ Productos encontrados:
  - ID: 1, Código: ABC123, Nombre: Producto ejemplo
  ...
```

**Significa**: Las credenciales están correctas y Odoo funciona ✅

---

#### ❌ **SI FALLA** - Error 1: Variables no configuradas

```
❌ Error: Asegúrate de que las variables ODOO_URL, ODOO_DB, 
ODOO_USER y ODOO_PASSWORD estén definidas en tu archivo .env
```

**Solución**: 
1. Abre el archivo `.env` con un editor de texto
2. Verifica que tenga las 5 variables con valores reales
3. Guarda el archivo

---

#### ❌ **SI FALLA** - Error 2: URL incorrecta

```
❌ No se pudo conectar al servidor en la URL 'tu-servidor.com'. 
Error: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**Problema**: La ODOO_URL está mal escrita o el servidor no es accesible

**Soluciones**:
1. Verifica que ODOO_URL sea la correcta (debe ser https://...)
2. Prueba acceder a esa URL en el navegador
3. Verifica que tengas conexión a internet

**NOTA IMPORTANTE**: Si tu URL de Odoo NO tiene `https://`, entonces necesitas modificar el archivo `conectar_odoo.py`:

Línea 23, cambiar de:
```python
common = xmlrpc.client.ServerProxy(f'https://{url}/xmlrpc/2/common')
```

A:
```python
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
```

Y línea 37, cambiar de:
```python
models = xmlrpc.client.ServerProxy(f'https://{url}/xmlrpc/2/object')
```

A:
```python
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
```

**Y actualiza tu .env para incluir el protocolo en la URL**:
```
ODOO_URL=http://tu-servidor.odoo.com
```

---

#### ❌ **SI FALLA** - Error 3: Credenciales incorrectas

```
❌ Error de autenticación. Revisa las credenciales en tu archivo .env.
```

**Solución**:
1. Verifica que ODOO_USER y ODOO_PASSWORD sean correctos
2. Intenta iniciar sesión en Odoo con esas credenciales en el navegador
3. Verifica que ODOO_DB sea el nombre correcto de la base de datos

---

## PASO 5: Si la conexión funciona, ejecutar la aplicación

```powershell
python app.py
```

**Busca en la consola**:
- `[OK] Conexion a Odoo establecida exitosamente.` → ✅ **BIEN**
- `[ERROR] Error en la conexion a Odoo: ...` → ❌ **MAL**

---

## 🔧 PROBLEMAS COMUNES Y SOLUCIONES

### Problema 1: "No se encuentra el módulo dotenv"

```powershell
pip install python-dotenv
```

### Problema 2: "No se encuentra el archivo .env"

**Solución**: Crea el archivo manualmente

1. Crea un archivo nuevo llamado `.env` (con el punto al inicio)
2. Pega este contenido:

```env
ODOO_URL=https://TU-SERVIDOR-ODOO.com
ODOO_DB=TU_BASE_DATOS
ODOO_USER=TU_USUARIO
ODOO_PASSWORD=TU_CONTRASEÑA
SECRET_KEY=una_clave_secreta_aleatoria_123456789
```

3. Reemplaza los valores con tus credenciales reales
4. Guarda el archivo

### Problema 3: El archivo .env tiene la URL sin protocolo

**Ejemplo incorrecto**:
```
ODOO_URL=mi-servidor.odoo.com
```

**Debe ser** (CON protocolo):
```
ODOO_URL=https://mi-servidor.odoo.com
```

O si es HTTP (menos seguro):
```
ODOO_URL=http://mi-servidor.odoo.com
```

Y modifica `conectar_odoo.py` como se indicó arriba.

---

## 📋 CHECKLIST DE VERIFICACIÓN

Marca cada ítem cuando lo completes:

- [ ] Navegar a la carpeta del proyecto
- [ ] Verificar que existe archivo `.env`
- [ ] Verificar que `.env` tiene las 5 variables
- [ ] Verificar que los valores NO están vacíos
- [ ] Ejecutar `python verificar_env.py` → Todo en verde
- [ ] Ejecutar `python conectar_odoo.py` → Conexión exitosa
- [ ] Ejecutar `python app.py` → Servidor inicia sin errores
- [ ] Ir a http://127.0.0.1:5002/login
- [ ] Login funciona
- [ ] Dashboard muestra datos

---

## 🆘 SI TODO FALLA

**Envíame esta información**:

1. **Contenido del verificar_env.py** (lo que aparece al ejecutarlo)
2. **Error exacto de conectar_odoo.py** (copia todo el mensaje)
3. **Tipo de servidor Odoo** (cloud, on-premise, versión)

---

## 📞 COMANDOS ÚTILES

### Ver versión de Python
```powershell
python --version
```

### Ver paquetes instalados
```powershell
pip list
```

### Instalar dependencias del proyecto
```powershell
pip install -r requirements.txt
```

---

**Creado**: 10 de Octubre, 2025  
**Proyecto**: Dashboard Cobranzas

