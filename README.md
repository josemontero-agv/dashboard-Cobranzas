# Dashboard de Ventas Farmacéuticas - Versión Limpia

## Descripción
Sistema de dashboard para análisis de ventas farmacéuticas integrado con Odoo. 
Incluye solo funcionalidades esenciales: ventas y dashboard.

## Estructura del Proyecto
```
Dashboard-Ventas/
├── app.py                 # Aplicación Flask principal (solo rutas esenciales)
├── odoo_manager.py       # Gestión de datos Odoo (funciones limpias)
├── conectar_odoo.py      # Configuración de conexión Odoo
├── requirements.txt      # Dependencias del proyecto
├── .env                  # Variables de entorno (credenciales Odoo)
├── static/
│   ├── css/style.css    # Estilos Odoo
│   └── js/script.js     # JavaScript del frontend
└── templates/
    ├── base.html        # Template base
    ├── login.html       # Página de login
    ├── sales.html       # Tabla de ventas
    └── dashboard.html   # Dashboard con gráficos
```

## Funcionalidades
- **Login**: Autenticación con credenciales de Odoo
- **Sales**: Visualización de datos de ventas con filtros
- **Dashboard**: Gráficos de líneas comerciales y vendedores
- **Export**: Exportación de datos a Excel

## Configuración
1. Configurar credenciales en `.env`:
   ```
   ODOO_URL=tu_url_odoo
   ODOO_DB=tu_base_datos
   ODOO_USERNAME=usuario_odoo
   ODOO_PASSWORD=contraseña_odoo
   ```

2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Ejecutar aplicación:
   ```bash
   python app.py
   ```

## Rutas Disponibles
- `/` - Redirección al login
- `/login` - Página de autenticación
- `/sales` - Tabla de ventas con filtros
- `/dashboard` - Dashboard con gráficos
- `/export_excel` - Exportación de datos

## Características Técnicas
- **Framework**: Flask
- **Base de Datos**: Odoo (XML-RPC)
- **Frontend**: HTML, CSS, JavaScript, Chart.js
- **Estilo**: Diseño inspirado en Odoo
- **Autenticación**: Credenciales reales de Odoo
