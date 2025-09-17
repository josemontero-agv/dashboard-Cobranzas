# app.py - Dashboard de Ventas Farmacéuticas

from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from dotenv import load_dotenv
from odoo_manager import OdooManager
from google_sheets_manager import GoogleSheetsManager
import os
import pandas as pd
import json
import io
import calendar
from datetime import datetime, timedelta

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Configuración para deshabilitar cache de templates
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# --- Inicialización de Managers ---
data_manager = OdooManager()
gs_manager = GoogleSheetsManager(
    credentials_file='credentials.json',
    sheet_name=os.getenv('GOOGLE_SHEET_NAME')
)

# --- Funciones Auxiliares ---

def get_meses_del_año(año):
    """Genera una lista de meses para un año específico."""
    meses_nombres = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]
    meses_disponibles = []
    for i in range(1, 13):
        mes_key = f"{año}-{i:02d}"
        mes_nombre = f"{meses_nombres[i-1]} {año}"
        meses_disponibles.append({'key': mes_key, 'nombre': mes_nombre})
    return meses_disponibles

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if data_manager.authenticate_user(username, password):
            session['username'] = username
            flash('¡Inicio de sesión exitoso!', 'success')
            return redirect(url_for('sales'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@app.route('/sales', methods=['GET', 'POST'])
def sales():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    try:
        # Obtener opciones de filtro
        filter_options = data_manager.get_filter_options()
        
        # Obtener filtros de la request
        selected_filters = {
            'date_from': request.form.get('date_from') or request.args.get('date_from'),
            'date_to': request.form.get('date_to') or request.args.get('date_to'),
            'linea_id': request.form.get('linea_id') or request.args.get('linea_id'),
            'partner_id': request.form.get('partner_id') or request.args.get('partner_id')
        }
        
        # Convertir strings vacíos a None
        for key, value in selected_filters.items():
            if value == '':
                selected_filters[key] = None
            elif key in ['linea_id', 'partner_id'] and value is not None:
                try:
                    selected_filters[key] = int(value)
                except (ValueError, TypeError):
                    selected_filters[key] = None
        
        # Obtener datos
        sales_data = data_manager.get_sales_lines(
            date_from=selected_filters['date_from'],
            date_to=selected_filters['date_to'],
            partner_id=selected_filters['partner_id'],
            linea_id=selected_filters['linea_id'],
            limit=1000
        )
        
        # Filtrar VENTA INTERNACIONAL (exportaciones)
        sales_data_filtered = []
        for sale in sales_data:
            linea_comercial = sale.get('commercial_line_national_id')
            if linea_comercial and isinstance(linea_comercial, list) and len(linea_comercial) > 1:
                nombre_linea = linea_comercial[1].upper()
                if 'VENTA INTERNACIONAL' in nombre_linea:
                    continue
            
            # También filtrar por canal de ventas
            canal_ventas = sale.get('sales_channel_id')
            if canal_ventas and isinstance(canal_ventas, list) and len(canal_ventas) > 1:
                nombre_canal = canal_ventas[1].upper()
                if 'VENTA INTERNACIONAL' in nombre_canal or 'INTERNACIONAL' in nombre_canal:
                    continue
            
            sales_data_filtered.append(sale)
        
        return render_template('sales.html', 
                             sales_data=sales_data_filtered,
                             filter_options=filter_options,
                             selected_filters=selected_filters,
                             fecha_actual=datetime.now())
    
    except Exception as e:
        flash(f'Error al obtener datos: {str(e)}', 'danger')
        return render_template('sales.html', 
                             sales_data=[],
                             filter_options={'lineas': [], 'clientes': []},
                             selected_filters={},
                             fecha_actual=datetime.now())

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    try:
        # Obtener año actual y mes seleccionado
        fecha_actual = datetime.now()
        año_actual = fecha_actual.year
        mes_seleccionado = request.args.get('mes', fecha_actual.strftime('%Y-%m'))
        
        # Crear todos los meses del año actual
        meses_disponibles = get_meses_del_año(año_actual)
        
        # Obtener nombre del mes seleccionado
        mes_obj = next((m for m in meses_disponibles if m['key'] == mes_seleccionado), None)
        mes_nombre = mes_obj['nombre'] if mes_obj else "Mes Desconocido"
        
        # Obtener día correcto según el mes seleccionado
        if mes_seleccionado == fecha_actual.strftime('%Y-%m'):
            # Mes actual: usar día actual
            dia_actual = fecha_actual.day
        else:
            # Mes pasado: usar último día del mes para mostrar el total del mes completo
            año_sel, mes_sel = mes_seleccionado.split('-')
            ultimo_dia = calendar.monthrange(int(año_sel), int(mes_sel))[1]
            dia_actual = ultimo_dia
        
        # Obtener metas del mes seleccionado desde la sesión
        metas_historicas = gs_manager.read_metas_por_linea()
        metas_del_mes = metas_historicas.get(mes_seleccionado, {}).get('metas', {})
        metas_ipn_del_mes = metas_historicas.get(mes_seleccionado, {}).get('metas_ipn', {})
        
        # Líneas comerciales estáticas
        lineas_comerciales_estaticas = [
            {'nombre': 'PETMEDICA', 'id': 'petmedica'},
            {'nombre': 'AGROVET', 'id': 'agrovet'},
            {'nombre': 'PET NUTRISCIENCE', 'id': 'pet_nutriscience'},
            {'nombre': 'AVIVET', 'id': 'avivet'},
            {'nombre': 'ECOMMERCE', 'id': 'ecommerce'},
            {'nombre': 'OTROS', 'id': 'otros'},
            {'nombre': 'GENVET', 'id': 'genvet'},
            {'nombre': 'LICITACIÓN', 'id': 'licitacion'},
            {'nombre': 'Ninguno', 'id': 'ninguno'},
        ]
        
        # Obtener datos reales de ventas desde Odoo
        try:
            # Calcular fechas para el mes seleccionado
            año_sel, mes_sel = mes_seleccionado.split('-')
            fecha_inicio = f"{año_sel}-{mes_sel}-01"
            
            # Último día del mes
            ultimo_dia = calendar.monthrange(int(año_sel), int(mes_sel))[1]
            fecha_fin = f"{año_sel}-{mes_sel}-{ultimo_dia}"
            
            # Obtener datos de ventas reales desde Odoo
            sales_data = data_manager.get_sales_lines(
                date_from=fecha_inicio,
                date_to=fecha_fin,
                limit=5000
            )
            
            print(f"📊 Obtenidas {len(sales_data)} líneas de ventas para el dashboard")
            
        except Exception as e:
            print(f"⚠️ Error obteniendo datos de Odoo: {e}")
            sales_data = []
        
        # Procesar datos de ventas por línea comercial
        datos_lineas = []
        total_meta = 0
        total_venta = 0
        total_meta_pn = 0
        total_venta_pn = 0
        total_vencimiento = 0
        
        # Mapeo de líneas comerciales de Odoo a IDs locales
        mapeo_lineas = {
            'PETMEDICA': 'petmedica',
            'AGROVET': 'agrovet', 
            'PET NUTRISCIENCE': 'pet_nutriscience',
            'AVIVET': 'avivet',
            'ECOMMERCE': 'ecommerce',
            'OTROS': 'otros',
            'GENVET': 'genvet',
            'LICITACIÓN': 'licitacion'
        }
        
        # Calcular ventas reales por línea comercial
        ventas_por_linea = {}
        ventas_por_ruta = {}
        ventas_ipn_por_linea = {} # Nueva variable para ventas de productos nuevos
        ventas_por_producto = {}
        ciclo_vida_por_producto = {}
        ventas_por_ciclo_vida = {}
        ventas_por_forma = {}
        for sale in sales_data:
            # Excluir VENTA INTERNACIONAL (exportaciones)
            linea_comercial = sale.get('commercial_line_national_id')
            nombre_linea_actual = None
            if linea_comercial and isinstance(linea_comercial, list) and len(linea_comercial) > 1:
                nombre_linea_actual = linea_comercial[1].upper()
                if 'VENTA INTERNACIONAL' in nombre_linea_actual:
                    continue
            
            # También filtrar por canal de ventas
            canal_ventas = sale.get('sales_channel_id')
            if canal_ventas and isinstance(canal_ventas, list) and len(canal_ventas) > 1:
                nombre_canal = canal_ventas[1].upper()
                if 'VENTA INTERNACIONAL' in nombre_canal or 'INTERNACIONAL' in nombre_canal:
                    continue
            
            # Procesar el balance de la venta
            balance_float = float(sale.get('balance', 0))
            if balance_float != 0:
                
                # Sumar a ventas totales por línea
                if nombre_linea_actual:
                    ventas_por_linea[nombre_linea_actual] = ventas_por_linea.get(nombre_linea_actual, 0) + balance_float
                
                # LÓGICA FINAL: Sumar si la RUTA (route_id) coincide con los valores especificados
                ruta = sale.get('route_id')
                # Se cambia la comparación al ID de la ruta (ruta[0]) para evitar problemas con traducciones.
                if isinstance(ruta, list) and len(ruta) > 0 and ruta[0] in [18, 19]:
                    if nombre_linea_actual:
                        ventas_por_ruta[nombre_linea_actual] = ventas_por_ruta.get(nombre_linea_actual, 0) + balance_float
                
                # Sumar a ventas de productos nuevos (IPN) - Lógica restaurada
                ciclo_vida = sale.get('product_life_cycle')
                if ciclo_vida and ciclo_vida == 'nuevo':
                    if nombre_linea_actual:
                        ventas_ipn_por_linea[nombre_linea_actual] = ventas_ipn_por_linea.get(nombre_linea_actual, 0) + balance_float
                
                # Agrupar por producto para Top 7
                producto_nombre = sale.get('name', '').strip()
                if producto_nombre:
                    ventas_por_producto[producto_nombre] = ventas_por_producto.get(producto_nombre, 0) + balance_float
                    if producto_nombre not in ciclo_vida_por_producto:
                        ciclo_vida_por_producto[producto_nombre] = ciclo_vida
                
                # Agrupar por ciclo de vida para el gráfico de dona
                ciclo_vida_grafico = ciclo_vida if ciclo_vida else 'No definido'
                ventas_por_ciclo_vida[ciclo_vida_grafico] = ventas_por_ciclo_vida.get(ciclo_vida_grafico, 0) + balance_float

                # Agrupar por forma farmacéutica para el gráfico de ECharts
                forma_farmaceutica = sale.get('pharmaceutical_forms_id')
                nombre_forma = forma_farmaceutica[1] if forma_farmaceutica and isinstance(forma_farmaceutica, list) and len(forma_farmaceutica) > 1 else 'Instrumental'
                ventas_por_forma[nombre_forma] = ventas_por_forma.get(nombre_forma, 0) + balance_float

        print(f"💰 Ventas por línea comercial: {ventas_por_linea}")
        print(f"📦 Ventas por Vencimiento (Ciclo de Vida): {ventas_por_ruta}")
        print(f"✨ Ventas IPN (Productos Nuevos): {ventas_ipn_por_linea}")

        # --- Procesamiento de datos para gráficos (después del bucle) ---

        # 1. Procesar datos para la tabla principal
        for linea in lineas_comerciales_estaticas:
            meta = metas_del_mes.get(linea['id'], 0)
            nombre_linea = linea['nombre'].upper()
            
            # Usar ventas reales de Odoo
            venta = ventas_por_linea.get(nombre_linea, 0)
            
            # Usar la meta IPN registrada por el usuario
            meta_pn = metas_ipn_del_mes.get(linea['id'], 0)
            venta_pn = ventas_ipn_por_linea.get(nombre_linea, 0) # Usar el cálculo real de ventas de productos nuevos
            vencimiento = ventas_por_ruta.get(nombre_linea, 0) # Usamos el nuevo cálculo
            
            porcentaje_total = (venta / meta * 100) if meta > 0 else 0
            porcentaje_pn = (venta_pn / meta_pn * 100) if meta_pn > 0 else 0

            datos_lineas.append({
                'nombre': linea['nombre'],
                'meta': meta,
                'venta': venta, # Ahora es positivo
                'porcentaje_total': (venta / meta * 100) if meta > 0 else 0,
                'meta_pn': meta_pn,
                'venta_pn': venta_pn,
                'porcentaje_pn': porcentaje_pn,
                'vencimiento_6_meses': vencimiento
            })
            
            total_meta += meta
            total_venta += venta
            total_meta_pn += meta_pn
            total_venta_pn += venta_pn
            total_vencimiento += vencimiento
        
        # 2. Calcular KPIs
        # Calcular KPIs
        kpis = {
            'meta_total': total_meta, # Meta siempre es positiva
            'venta_total': total_venta, # Ya es positivo
            'porcentaje_avance': (total_venta / total_meta * 100) if total_meta > 0 else 0,
            'meta_ipn': total_meta_pn, # Meta IPN siempre es positiva
            'venta_ipn': total_venta_pn, # Ya es positivo
            'porcentaje_avance_ipn': (total_venta_pn / total_meta_pn * 100) if total_meta_pn > 0 else 0,
            'vencimiento_6_meses': total_vencimiento,
            'avance_diario_total': ((total_venta / total_meta * 100) / dia_actual) if total_meta > 0 and dia_actual > 0 else 0,
            'avance_diario_ipn': ((total_venta_pn / total_meta_pn * 100) / dia_actual) if total_meta_pn > 0 and dia_actual > 0 else 0
        }
        
        # 3. Ordenar productos para el gráfico Top 7
        # Ordenar productos por ventas y tomar los top 7
        productos_ordenados = sorted(ventas_por_producto.items(), key=lambda x: x[1], reverse=True)[:7]
        
        datos_productos = []
        for nombre_producto, venta in productos_ordenados:
            datos_productos.append({
                'nombre': nombre_producto,
                'venta': venta,
                'ciclo_vida': ciclo_vida_por_producto.get(nombre_producto, 'No definido')
            })
        
        print(f"🏆 Top 7 productos por ventas: {[p['nombre'] for p in datos_productos]}")
        
        # 4. Ordenar datos para el gráfico de Ciclo de Vida
        # Convertir a lista ordenada por ventas
        datos_ciclo_vida = []
        for ciclo, venta in sorted(ventas_por_ciclo_vida.items(), key=lambda x: x[1], reverse=True):
            datos_ciclo_vida.append({
                'ciclo': ciclo,
                'venta': venta
            })
        
        print(f"📈 Ventas por Ciclo de Vida: {datos_ciclo_vida}")
        
        # 5. Ordenar datos para el gráfico de Forma Farmacéutica
        # Convertir a lista ordenada por ventas
        datos_forma_farmaceutica = []
        for forma, venta in sorted(ventas_por_forma.items(), key=lambda x: x[1], reverse=True):
            datos_forma_farmaceutica.append({
                'forma': forma,
                'venta': venta
            })
        
        return render_template('dashboard_clean.html',
                             meses_disponibles=meses_disponibles,
                             mes_seleccionado=mes_seleccionado,
                             mes_nombre=mes_nombre,
                             dia_actual=dia_actual,
                             kpis=kpis,
                             datos_lineas=datos_lineas, # Usar para gráficos
                             datos_lineas_tabla=datos_lineas, # Usar para la tabla
                             datos_productos=datos_productos,
                             datos_ciclo_vida=datos_ciclo_vida if 'datos_ciclo_vida' in locals() else [],
                             datos_forma_farmaceutica=datos_forma_farmaceutica)
    
    except Exception as e:
        flash(f'Error al obtener datos del dashboard: {str(e)}', 'danger')
        
        # Crear datos por defecto para evitar errores
        fecha_actual = datetime.now()
        kpis_default = {
            'meta_total': 0,
            'venta_total': 0,
            'porcentaje_avance': 0,
            'meta_ipn': 0,
            'venta_ipn': 0,
            'porcentaje_avance_ipn': 0,
            'vencimiento_6_meses': 0,
            'avance_diario_total': 0,
            'avance_diario_ipn': 0
        }
        
        return render_template('dashboard_clean.html',
                             meses_disponibles=[{
                                 'key': fecha_actual.strftime('%Y-%m'),
                                 'nombre': f"{fecha_actual.strftime('%B')} {fecha_actual.year}"
                             }],
                             mes_seleccionado=fecha_actual.strftime('%Y-%m'),
                             mes_nombre=f"{fecha_actual.strftime('%B').upper()} {fecha_actual.year}",
                             dia_actual=fecha_actual.day,
                             kpis=kpis_default,
                             datos_lineas=[], # Se mantiene vacío en caso de error
                             datos_lineas_tabla=[],
                             datos_productos=[],
                             datos_ciclo_vida=[],
                             datos_forma_farmaceutica=[])


@app.route('/dashboard_linea')
def dashboard_linea():
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        # --- 1. OBTENER FILTROS ---
        fecha_actual = datetime.now()
        mes_seleccionado = request.args.get('mes', fecha_actual.strftime('%Y-%m'))
        año_actual = fecha_actual.year
        meses_disponibles = get_meses_del_año(año_actual)

        linea_seleccionada_nombre = request.args.get('linea_nombre', 'PETMEDICA') # Default a PETMEDICA si no se especifica

        # Obtener día correcto según el mes seleccionado (lógica del dashboard principal)
        if mes_seleccionado == fecha_actual.strftime('%Y-%m'):
            # Mes actual: usar día actual
            dia_actual = fecha_actual.day
        else:
            # Mes pasado: usar último día del mes
            año_sel_dia, mes_sel_dia = mes_seleccionado.split('-')
            ultimo_dia_mes = calendar.monthrange(int(año_sel_dia), int(mes_sel_dia))[1]
            dia_actual = ultimo_dia_mes

        # Mapeo de nombre de línea a ID para cargar metas
        mapeo_nombre_a_id = {
            'PETMEDICA': 'petmedica', 'AGROVET': 'agrovet', 'PET NUTRISCIENCE': 'pet_nutriscience',
            'AVIVET': 'avivet', 'ECOMMERCE': 'ecommerce', 'OTROS': 'otros',
            'GENVET': 'genvet', 'LICITACIÓN': 'licitacion', 'Ninguno': 'ninguno'
        }
        linea_seleccionada_id = mapeo_nombre_a_id.get(linea_seleccionada_nombre.upper(), 'petmedica')

        # --- 2. OBTENER DATOS ---
        año_sel, mes_sel = mes_seleccionado.split('-')
        fecha_inicio = f"{año_sel}-{mes_sel}-01"
        ultimo_dia = calendar.monthrange(int(año_sel), int(mes_sel))[1]
        fecha_fin = f"{año_sel}-{mes_sel}-{ultimo_dia}"

        # Cargar metas de vendedores para el mes y línea seleccionados
        # La estructura es metas[equipo_id][vendedor_id][mes_key]
        metas_vendedores_historicas = gs_manager.read_metas()
        # 1. Obtener todas las metas del equipo/línea
        metas_del_equipo = metas_vendedores_historicas.get(linea_seleccionada_id, {})

        # Obtener todos los vendedores de Odoo
        todos_los_vendedores = {str(v['id']): v['name'] for v in data_manager.get_all_sellers()}

        # Obtener ventas del mes
        sales_data = data_manager.get_sales_lines(
            date_from=fecha_inicio,
            date_to=fecha_fin,
            limit=10000
        )

        # --- 3. PROCESAR Y AGREGAR DATOS POR VENDEDOR ---
        ventas_por_vendedor = {}
        ventas_ipn_por_vendedor = {}
        ventas_vencimiento_por_vendedor = {}
        ventas_por_producto = {}
        ventas_por_ciclo_vida = {}
        ventas_por_forma = {}

        for sale in sales_data:
            linea_comercial = sale.get('commercial_line_national_id')
            if linea_comercial and isinstance(linea_comercial, list) and len(linea_comercial) > 1:
                nombre_linea_actual = linea_comercial[1].upper()

                # Filtrar por la línea comercial seleccionada
                if nombre_linea_actual == linea_seleccionada_nombre.upper():
                    user_info = sale.get('invoice_user_id')
                    if user_info and isinstance(user_info, list) and len(user_info) > 1:
                        vendedor_id = str(user_info[0])
                        balance = float(sale.get('balance', 0))

                        # Agrupar ventas totales
                        ventas_por_vendedor[vendedor_id] = ventas_por_vendedor.get(vendedor_id, 0) + balance

                        # Agrupar ventas IPN
                        if sale.get('product_life_cycle') == 'nuevo':
                            ventas_ipn_por_vendedor[vendedor_id] = ventas_ipn_por_vendedor.get(vendedor_id, 0) + balance

                        # Agrupar ventas por vencimiento < 6 meses
                        ruta = sale.get('route_id')
                        if isinstance(ruta, list) and len(ruta) > 0 and ruta[0] in [18, 19]:
                            ventas_vencimiento_por_vendedor[vendedor_id] = ventas_vencimiento_por_vendedor.get(vendedor_id, 0) + balance

                        # Agrupar para gráficos (Top Productos, Ciclo Vida, Forma Farmacéutica)
                        producto_nombre = sale.get('name', '').strip()
                        if producto_nombre:
                            ventas_por_producto[producto_nombre] = ventas_por_producto.get(producto_nombre, 0) + balance

                        ciclo_vida = sale.get('product_life_cycle', 'No definido')
                        ventas_por_ciclo_vida[ciclo_vida] = ventas_por_ciclo_vida.get(ciclo_vida, 0) + balance

                        forma_farma = sale.get('pharmaceutical_forms_id')
                        nombre_forma = forma_farma[1] if forma_farma and len(forma_farma) > 1 else 'Instrumental'
                        ventas_por_forma[nombre_forma] = ventas_por_forma.get(nombre_forma, 0) + balance

        # --- 4. CONSTRUIR ESTRUCTURA DE DATOS PARA LA PLANTILLA ---
        datos_vendedores = []
        total_meta = 0
        total_venta = 0
        total_meta_ipn = 0
        total_venta_ipn = 0
        total_vencimiento = 0

        # Iterar sobre todos los vendedores para incluirlos aunque no tengan ventas
        for vendedor_id, vendedor_nombre in todos_los_vendedores.items():
            # 2. Obtener la meta para este vendedor y este mes específico
            meta_guardada = metas_del_equipo.get(vendedor_id, {}).get(mes_seleccionado, {})
            
            meta = float(meta_guardada.get('meta', 0))
            meta_ipn = float(meta_guardada.get('meta_ipn', 0))
            venta = ventas_por_vendedor.get(vendedor_id, 0)
            venta_ipn = ventas_ipn_por_vendedor.get(vendedor_id, 0)
            vencimiento = ventas_vencimiento_por_vendedor.get(vendedor_id, 0)

            # Incluir solo si el vendedor tiene ventas en el mes seleccionado
            if venta > 0:
                datos_vendedores.append({
                    'id': vendedor_id,
                    'nombre': vendedor_nombre,
                    'meta': meta,
                    'venta': venta,
                    'porcentaje_avance': (venta / meta * 100) if meta > 0 else 0,
                    'meta_ipn': meta_ipn,
                    'venta_ipn': venta_ipn,
                    'porcentaje_avance_ipn': (venta_ipn / meta_ipn * 100) if meta_ipn > 0 else 0,
                    'vencimiento_6_meses': vencimiento
                })
                total_meta += meta
                total_venta += venta
                total_meta_ipn += meta_ipn
                total_venta_ipn += venta_ipn
                total_vencimiento += vencimiento

        # Ordenar por venta descendente
        datos_vendedores = sorted(datos_vendedores, key=lambda x: x['venta'], reverse=True)

        # KPIs generales para la línea
        kpis = {
            'meta_total': total_meta,
            'venta_total': total_venta,
            'porcentaje_avance': (total_venta / total_meta * 100) if total_meta > 0 else 0,
            'meta_ipn': total_meta_ipn,
            'venta_ipn': total_venta_ipn,
            'porcentaje_avance_ipn': (total_venta_ipn / total_meta_ipn * 100) if total_meta_ipn > 0 else 0,
            'vencimiento_6_meses': total_vencimiento,
            'avance_diario_total': ((total_venta / total_meta * 100) / dia_actual) if total_meta > 0 and dia_actual > 0 else 0,
            'avance_diario_ipn': ((total_venta_ipn / total_meta_ipn * 100) / dia_actual) if total_meta_ipn > 0 and dia_actual > 0 else 0
        }

        # Datos para gráficos
        productos_ordenados = sorted(ventas_por_producto.items(), key=lambda x: x[1], reverse=True)[:7]
        datos_productos = [{'nombre': n, 'venta': v} for n, v in productos_ordenados]

        datos_ciclo_vida = [{'ciclo': c, 'venta': v} for c, v in ventas_por_ciclo_vida.items()]
        datos_forma_farmaceutica = [{'forma': f, 'venta': v} for f, v in ventas_por_forma.items()]

        # Lista de todas las líneas para el selector
        lineas_comerciales_disponibles = [
            'PETMEDICA', 'AGROVET', 'PET NUTRISCIENCE', 'AVIVET', 'ECOMMERCE', 'OTROS', 'GENVET', 'LICITACIÓN'
        ]

        return render_template('dashboard_linea.html',
                               linea_nombre=linea_seleccionada_nombre,
                               mes_seleccionado=mes_seleccionado,
                               meses_disponibles=meses_disponibles,
                               kpis=kpis,
                               datos_vendedores=datos_vendedores,
                               datos_productos=datos_productos,
                               datos_ciclo_vida=datos_ciclo_vida,
                               datos_forma_farmaceutica=datos_forma_farmaceutica,
                               lineas_disponibles=lineas_comerciales_disponibles)

    except Exception as e:
        flash(f'Error al generar el dashboard para la línea: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/meta', methods=['GET', 'POST'])
def meta():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    try:
        # Líneas comerciales estáticas de la empresa
        lineas_comerciales_estaticas = [
            {'nombre': 'PETMEDICA', 'id': 'petmedica'},
            {'nombre': 'AGROVET', 'id': 'agrovet'},
            {'nombre': 'PET NUTRISCIENCE', 'id': 'pet_nutriscience'},
            {'nombre': 'AVIVET', 'id': 'avivet'},
            {'nombre': 'ECOMMERCE', 'id': 'ecommerce'},
            {'nombre': 'OTROS', 'id': 'otros'},
            {'nombre': 'GENVET', 'id': 'genvet'},
            {'nombre': 'LICITACIÓN', 'id': 'licitacion'},
            {'nombre': 'Ninguno', 'id': 'ninguno'},
        ]
        
        # Obtener año actual y mes seleccionado
        fecha_actual = datetime.now()
        año_actual = fecha_actual.year
        mes_seleccionado = request.args.get('mes', fecha_actual.strftime('%Y-%m'))
        
        # Crear todos los meses del año actual
        meses_año = [{'es_actual': m['key'] == fecha_actual.strftime('%Y-%m'), **m} for m in get_meses_del_año(año_actual)]
        
        if request.method == 'POST':
            # Obtener el mes del formulario
            mes_formulario = request.form.get('mes_seleccionado', mes_seleccionado)
            
            # Procesar metas enviadas
            metas_data = {}
            metas_ipn_data = {}
            total_meta = 0
            total_meta_ipn = 0
            
            for linea in lineas_comerciales_estaticas:
                # Procesar Meta Total
                meta_value = request.form.get(f"meta_{linea['id']}", '0')
                try:
                    clean_value = str(meta_value).replace(',', '') if meta_value else '0'
                    valor = float(clean_value) if clean_value else 0.0
                    metas_data[linea['id']] = valor
                    total_meta += valor
                except (ValueError, TypeError):
                    metas_data[linea['id']] = 0.0
                
                # Procesar Meta IPN
                meta_ipn_value = request.form.get(f"meta_ipn_{linea['id']}", '0')
                try:
                    clean_value_ipn = str(meta_ipn_value).replace(',', '') if meta_ipn_value else '0'
                    valor_ipn = float(clean_value_ipn) if clean_value_ipn else 0.0
                    metas_ipn_data[linea['id']] = valor_ipn
                    total_meta_ipn += valor_ipn
                except (ValueError, TypeError):
                    metas_ipn_data[linea['id']] = 0.0
            
            # Encontrar el nombre del mes
            mes_obj = next((m for m in meses_año if m['key'] == mes_formulario), None)
            mes_nombre_formulario = mes_obj['nombre'] if mes_obj else ""
            
            metas_historicas = gs_manager.read_metas_por_linea()
            metas_historicas[mes_formulario] = {
                'metas': metas_data,
                'metas_ipn': metas_ipn_data,
                'total': total_meta,
                'total_ipn': total_meta_ipn,
                'mes_nombre': mes_nombre_formulario
            }
            gs_manager.write_metas_por_linea(metas_historicas)
            
            flash(f'Metas guardadas exitosamente para {mes_nombre_formulario}. Total: S/ {total_meta:,.0f}', 'success')
            
            # Actualizar mes seleccionado después de guardar
            mes_seleccionado = mes_formulario
        
        # Obtener todas las metas históricas
        metas_historicas = gs_manager.read_metas_por_linea()
        
        # Obtener metas y total del mes seleccionado
        metas_actuales = metas_historicas.get(mes_seleccionado, {}).get('metas', {})
        metas_ipn_actuales = metas_historicas.get(mes_seleccionado, {}).get('metas_ipn', {})
        total_actual = sum(metas_actuales.values()) if metas_actuales else 0
        total_ipn_actual = sum(metas_ipn_actuales.values()) if metas_ipn_actuales else 0
        
        # Encontrar el nombre del mes seleccionado
        mes_obj_seleccionado = next((m for m in meses_año if m['key'] == mes_seleccionado), meses_año[fecha_actual.month - 1])
        
        return render_template('meta.html',
                             lineas_comerciales=lineas_comerciales_estaticas,
                             metas_actuales=metas_actuales,
                             metas_ipn_actuales=metas_ipn_actuales,
                             metas_historicas=metas_historicas,
                             meses_año=meses_año,
                             mes_seleccionado=mes_seleccionado,
                             mes_nombre=mes_obj_seleccionado['nombre'],
                             total_actual=total_actual,
                             total_ipn_actual=total_ipn_actual,
                             fecha_actual=fecha_actual)
    
    except Exception as e:
        flash(f'Error al procesar metas: {str(e)}', 'danger')
        return render_template('meta.html',
                             lineas_comerciales=[],
                             metas_actuales={},
                             metas_ipn_actuales={},
                             metas_historicas={},
                             meses_año=[],
                             mes_seleccionado="",
                             mes_nombre="",
                             total_actual=0,
                             total_ipn_actual=0,
                             fecha_actual=datetime.now())

@app.route('/export/excel/sales')
def export_excel_sales():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    try:
        # Obtener filtros de la URL
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        linea_id = request.args.get('linea_id')
        partner_id = request.args.get('partner_id')
        
        # Convertir a tipos apropiados
        if linea_id:
            try:
                linea_id = int(linea_id)
            except (ValueError, TypeError):
                linea_id = None
        
        if partner_id:
            try:
                partner_id = int(partner_id)
            except (ValueError, TypeError):
                partner_id = None
        
        # Obtener datos
        sales_data = data_manager.get_sales_lines(
            date_from=date_from,
            date_to=date_to,
            partner_id=partner_id,
            linea_id=linea_id,
            limit=10000  # Más datos para export
        )
        
        # Filtrar VENTA INTERNACIONAL (exportaciones)
        sales_data_filtered = []
        for sale in sales_data:
            linea_comercial = sale.get('commercial_line_national_id')
            if linea_comercial and isinstance(linea_comercial, list) and len(linea_comercial) > 1:
                nombre_linea = linea_comercial[1].upper()
                if 'VENTA INTERNACIONAL' in nombre_linea:
                    continue
            
            # También filtrar por canal de ventas
            canal_ventas = sale.get('sales_channel_id')
            if canal_ventas and isinstance(canal_ventas, list) and len(canal_ventas) > 1:
                nombre_canal = canal_ventas[1].upper()
                if 'VENTA INTERNACIONAL' in nombre_canal or 'INTERNACIONAL' in nombre_canal:
                    continue
            
            sales_data_filtered.append(sale)
        
        # Crear DataFrame
        df = pd.DataFrame(sales_data_filtered)
        
        # Crear archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Ventas', index=False)
        
        output.seek(0)
        
        # Generar nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'ventas_farmaceuticas_{timestamp}.xlsx'
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        flash(f'Error al exportar datos: {str(e)}', 'danger')
        return redirect(url_for('sales'))

@app.route('/metas_vendedor', methods=['GET', 'POST'])
def metas_vendedor():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Obtener meses y líneas comerciales para los filtros
    fecha_actual = datetime.now()
    año_actual = fecha_actual.year
    meses_disponibles = get_meses_del_año(año_actual)
    lineas_comerciales_estaticas = [
        {'nombre': 'PETMEDICA', 'id': 'petmedica'},
        {'nombre': 'AGROVET', 'id': 'agrovet'},
        {'nombre': 'PET NUTRISCIENCE', 'id': 'pet_nutriscience'},
        {'nombre': 'AVIVET', 'id': 'avivet'},
        {'nombre': 'ECOMMERCE', 'id': 'ecommerce'},
        {'nombre': 'OTROS', 'id': 'otros'},
        {'nombre': 'GENVET', 'id': 'genvet'},
        {'nombre': 'LICITACIÓN', 'id': 'licitacion'},
        {'nombre': 'Ninguno', 'id': 'ninguno'},
    ]
    equipos_definidos = [
        {'id': 'petmedica', 'nombre': 'PETMEDICA'},
        {'id': 'agrovet', 'nombre': 'AGROVET'},
        {'id': 'pet_nutriscience', 'nombre': 'PET NUTRISCIENCE'},
        {'id': 'avivet', 'nombre': 'AVIVET'},
        {'id': 'ecommerce', 'nombre': 'ECOMMERCE'},
        {'id': 'otros', 'nombre': 'OTROS'},
    ]

    # Determinar mes y línea seleccionados (desde form o por defecto)
    mes_seleccionado = request.form.get('mes_seleccionado', fecha_actual.strftime('%Y-%m'))
    linea_seleccionada = request.form.get('linea_seleccionada', lineas_comerciales_estaticas[0]['id'])

    if request.method == 'POST':
        # --- 1. GUARDAR ASIGNACIONES DE EQUIPOS ---
        equipo_actualizado_id = request.form.get('guardar_equipo') # Para el mensaje flash
        todos_los_vendedores_para_guardar = data_manager.get_all_sellers()
        equipos_guardados = gs_manager.read_equipos()

        for equipo in equipos_definidos:
            campo_vendedores = f'vendedores_{equipo["id"]}'
            if campo_vendedores in request.form:
                vendedores_str = request.form.get(campo_vendedores, '')
                if vendedores_str:
                    vendedores_ids = [int(vid) for vid in vendedores_str.split(',') if vid.isdigit()]
                    equipos_guardados[equipo['id']] = vendedores_ids
                else:
                    equipos_guardados[equipo['id']] = []
        gs_manager.write_equipos(equipos_guardados, todos_los_vendedores_para_guardar)

        # --- 2. GUARDAR TODAS LAS METAS (ESTRUCTURA PIVOT) ---
        metas_vendedores_historicas = gs_manager.read_metas()
        
        for equipo in equipos_definidos:
            equipo_id = equipo['id']
            if equipo_id not in metas_vendedores_historicas:
                metas_vendedores_historicas[equipo_id] = {}

            vendedores_ids_en_equipo = equipos_guardados.get(equipo_id, [])
            for vendedor_id in vendedores_ids_en_equipo:
                vendedor_id_str = str(vendedor_id)
                if vendedor_id_str not in metas_vendedores_historicas[equipo_id]:
                    metas_vendedores_historicas[equipo_id][vendedor_id_str] = {}

                for mes in meses_disponibles:
                    mes_key = mes['key']
                    # No es necesario crear la clave del mes aquí, se crea si hay datos

                    meta_valor_str = request.form.get(f'meta_{equipo_id}_{vendedor_id_str}_{mes_key}')
                    meta_ipn_valor_str = request.form.get(f'meta_ipn_{equipo_id}_{vendedor_id_str}_{mes_key}')

                    # Convertir a float, manejar valores vacíos como None para no guardar ceros innecesarios
                    meta = float(meta_valor_str) if meta_valor_str else None
                    meta_ipn = float(meta_ipn_valor_str) if meta_ipn_valor_str else None

                    if meta is not None or meta_ipn is not None:
                        # Si la clave del mes no existe, créala
                        if mes_key not in metas_vendedores_historicas[equipo_id][vendedor_id_str]:
                             metas_vendedores_historicas[equipo_id][vendedor_id_str][mes_key] = {}
                        metas_vendedores_historicas[equipo_id][vendedor_id_str][mes_key] = {
                            'meta': meta or 0.0,
                            'meta_ipn': meta_ipn or 0.0
                        }
                    # Si ambos son None y la clave existe, se elimina para limpiar el JSON
                    elif mes_key in metas_vendedores_historicas[equipo_id][vendedor_id_str]:
                        del metas_vendedores_historicas[equipo_id][vendedor_id_str][mes_key]

        gs_manager.write_metas(metas_vendedores_historicas)
        
        if equipo_actualizado_id:
            flash(f'Miembros del equipo actualizados. Ahora puedes asignar sus metas.', 'info')
        else:
            flash('Equipos y metas guardados correctamente.', 'success')

        # Redirigir con los parámetros para recargar la página con los filtros correctos
        return redirect(url_for('metas_vendedor'))

    # GET o después de POST
    todos_los_vendedores = data_manager.get_all_sellers()
    vendedores_por_id = {v['id']: v for v in todos_los_vendedores}
    equipos_guardados = gs_manager.read_equipos()

    # Construir la estructura de datos para la plantilla
    equipos_con_vendedores = []
    for equipo_def in equipos_definidos:
        equipo_id = equipo_def['id']
        vendedores_ids = equipos_guardados.get(equipo_id, [])
        vendedores_de_equipo = [vendedores_por_id[vid] for vid in vendedores_ids if vid in vendedores_por_id]
        
        equipos_con_vendedores.append({
            'id': equipo_id,
            'nombre': equipo_def['nombre'],
            'vendedores_ids': [str(vid) for vid in vendedores_ids], # Para Tom-Select
            'vendedores': sorted(vendedores_de_equipo, key=lambda v: v['name']) # Para la tabla
        })

    # Para la vista, pasamos todas las metas cargadas
    metas_guardadas = gs_manager.read_metas()

    return render_template('metas_vendedor.html',
                           meses_disponibles=meses_disponibles,
                           lineas_comerciales=lineas_comerciales_estaticas,
                           equipos_con_vendedores=equipos_con_vendedores,
                           todos_los_vendedores=todos_los_vendedores,
                           metas_guardadas=metas_guardadas)

@app.route('/export/dashboard/details')
def export_dashboard_details():
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        # Obtener el mes seleccionado de los parámetros de la URL
        mes_seleccionado = request.args.get('mes')
        if not mes_seleccionado:
            flash('No se especificó un mes para la exportación.', 'danger')
            return redirect(url_for('dashboard'))

        # Calcular fechas para el mes seleccionado
        año_sel, mes_sel = mes_seleccionado.split('-')
        fecha_inicio = f"{año_sel}-{mes_sel}-01"
        ultimo_dia = calendar.monthrange(int(año_sel), int(mes_sel))[1]
        fecha_fin = f"{año_sel}-{mes_sel}-{ultimo_dia}"

        # Obtener datos de ventas reales desde Odoo para ese mes
        sales_data = data_manager.get_sales_lines(
            date_from=fecha_inicio,
            date_to=fecha_fin,
            limit=10000  # Límite alto para exportación
        )

        # Filtrar VENTA INTERNACIONAL (exportaciones), igual que en el dashboard
        sales_data_filtered = []
        for sale in sales_data:
            linea_comercial = sale.get('commercial_line_national_id')
            if linea_comercial and isinstance(linea_comercial, list) and len(linea_comercial) > 1:
                if 'VENTA INTERNACIONAL' in linea_comercial[1].upper():
                    continue
            
            canal_ventas = sale.get('sales_channel_id')
            if canal_ventas and isinstance(canal_ventas, list) and len(canal_ventas) > 1:
                nombre_canal = canal_ventas[1].upper()
                if 'VENTA INTERNACIONAL' in nombre_canal or 'INTERNACIONAL' in nombre_canal:
                    continue
            
            sales_data_filtered.append(sale)

        # Convertir el balance a positivo para que coincida con el dashboard
        for sale in sales_data_filtered:
            if 'balance' in sale and sale['balance'] is not None:
                sale['balance'] = float(sale['balance']) # Ya viene con el signo correcto desde OdooManager

        # Crear DataFrame de Pandas con los datos filtrados
        df = pd.DataFrame(sales_data_filtered)

        # Crear archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=f'Detalle Ventas {mes_seleccionado}', index=False)
        output.seek(0)

        # Generar nombre de archivo
        filename = f'detalle_ventas_{mes_seleccionado}.xlsx'

        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        flash(f'Error al exportar los detalles del dashboard: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))


if __name__ == '__main__':
    print("🚀 Iniciando Dashboard de Ventas Farmacéuticas...")
    print("📊 Disponible en: http://127.0.0.1:5000")
    print("🔐 Usuario: configurado en .env")
    app.run(debug=True)
