# Configuración para la Integración con Google Sheets

Sigue estos pasos para permitir que la aplicación lea y escriba datos en una hoja de cálculo de Google. Este proceso solo necesita hacerse una vez.

## Paso 1: Crear un Proyecto en Google Cloud y Habilitar APIs

1.  Ve a la [Consola de Google Cloud](https://console.cloud.google.com/).
2.  Crea un nuevo proyecto (o selecciona uno existente). Dale un nombre como "DashboardVentasApp".
3.  En el buscador de la consola, busca y habilita las siguientes dos APIs para tu proyecto:
    *   **Google Drive API**
    *   **Google Sheets API**

## Paso 2: Crear Credenciales de Cuenta de Servicio

1.  En el menú de navegación de la izquierda, ve a **"IAM y administración"** > **"Cuentas de servicio"**.
2.  Haz clic en **"+ CREAR CUENTA DE SERVICIO"**.
3.  Dale un nombre a la cuenta (ej: `dashboard-sheets-editor`) y una descripción. Haz clic en **"CREAR Y CONTINUAR"**.
4.  En el paso de "Conceder a esta cuenta de servicio acceso al proyecto", asígnale el rol de **"Editor"**. Haz clic en **"CONTINUAR"**.
5.  En el último paso, no es necesario conceder acceso a usuarios. Haz clic en **"LISTO"**.
6.  Busca la cuenta de servicio que acabas de crear en la lista. Haz clic en los tres puntos bajo "Acciones" y selecciona **"Administrar claves"**.
7.  Haz clic en **"AGREGAR CLAVE"** > **"Crear clave nueva"**.
8.  Selecciona el tipo de clave **JSON** y haz clic en **"CREAR"**. Se descargará un archivo JSON.

## Paso 3: Configurar el Archivo de Credenciales

1.  Renombra el archivo JSON que descargaste a `credentials.json`.
2.  Mueve este archivo `credentials.json` a la carpeta principal de tu proyecto (la misma donde está `app.py`).

## Paso 4: Crear y Compartir tu Google Sheet

1.  Crea una nueva hoja de cálculo en Google Sheets. Dale un nombre fácil de recordar (ej: "MetasDashboardVentas").
2.  Dentro de la hoja, crea dos pestañas en la parte inferior con los siguientes nombres exactos:
    *   `MetasPorLinea`
    *   `Equipos`
    *   `Metas`
3.  Abre tu archivo `credentials.json` con un editor de texto. Busca el valor del campo `"client_email"`. Será algo como `dashboard-sheets-editor@tu-proyecto.iam.gserviceaccount.com`.
4.  Vuelve a tu Google Sheet, haz clic en el botón **"Compartir"** (arriba a la derecha).
5.  Pega la dirección de correo (`client_email`) en el campo para compartir y asígnale el rol de **"Editor"**. Haz clic en **"Enviar"**.

## Paso 5: Actualizar el Archivo `.env`

1.  Abre el archivo `.env` de tu proyecto.
2.  Añade una nueva línea con el nombre exacto de tu hoja de cálculo:
    ```
    GOOGLE_SHEET_NAME="MetasDashboardVentas"
    ```

¡Listo! Ahora puedes instalar las nuevas librerías y ejecutar la aplicación.