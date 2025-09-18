# Bitácora de Cambios del Proyecto - Dashboard de Ventas

Este documento registra los cambios y funcionalidades más importantes implementadas a lo largo del desarrollo del proyecto.

---

### Versión 1.0: Funcionalidad Inicial

- **Conexión con Odoo:** Establecimiento de la conexión con la base de datos de Odoo para la extracción de datos de ventas.
- **Dashboard General:** Creación del dashboard principal con:
  - KPIs de rendimiento (Meta, Venta, Avance, etc.).
  - Tabla de avance por línea comercial.
  - Gráficos de "Venta por Tipo de Producto", "Top 7 Productos" y "Venta por Línea Comercial".
- **Gestión de Metas por Línea:** Interfaz para establecer las metas mensuales para cada línea comercial.
- **Vista de Líneas de Venta:** Tabla detallada con todas las líneas de venta y filtros por fecha, cliente y línea.

---

### Versión 2.0: Gestión de Equipos y Metas Individuales

- **Dashboard por Vendedor:** Creación de un dashboard detallado por línea comercial, mostrando el rendimiento de cada vendedor.
- **Gestión de Equipos y Metas:** Implementación de una nueva interfaz unificada para:
  - Asignar vendedores a equipos de venta.
  - Establecer metas individuales (Total e IPN) para cada vendedor en una vista de tabla dinámica anual.
- **Mejoras de UI:**
  - Formateo de números con separadores de miles en los campos de metas.
  - Optimización del diseño de las tablas para una mejor visualización.

---

### Versión 3.0: Integración con Google Sheets y Mejoras de UI

- **Integración con Google Sheets:** Migración completa de la gestión de metas (por línea y por vendedor) y equipos desde archivos locales (`.json`) a una única hoja de cálculo de Google Sheets, centralizando la fuente de datos.
- **Mejoras en Dashboard de Vendedor:**
  - Se añadió la columna **"Vencimiento < 6 Meses"** para un análisis más completo.
  - Se incorporó un nuevo **gráfico de barras "Meta vs. Venta por Vendedor"**.
  - Se estandarizó el formato de números en las ventanas emergentes (tooltips) de todos los gráficos para no mostrar decimales.
- **Preparación para Despliegue:** Se añadió `gunicorn` y se limpió el archivo `requirements.txt` para asegurar la compatibilidad con servicios de despliegue como Render.com.

---

### Versión 3.1: Mejoras de Flujo y Usabilidad

- **Flujo de Usuario Optimizado:**
  - La página de inicio después del login es ahora el **Dashboard Principal**.
  - La página de "Ventas" ya no carga datos por defecto, mejorando la velocidad de carga inicial. Los datos se obtienen al presionar "Buscar".
- **Interfaz de Ventas Simplificada:**
  - Se eliminó el filtro por "Cliente".
  - El botón "Buscar" ahora carga los datos de los últimos 30 días si no se especifican fechas.
- **Personalización de UI:** Se muestra el nombre del usuario que ha iniciado sesión debajo del título principal en los dashboards.
- **Corrección de Errores:** Solucionado un error que impedía la carga de los filtros en la página de "Ventas".