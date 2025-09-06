# app.py - Dashboard de Ventas Farmacéuticas

from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from dotenv import load_dotenv
from odoo_manager import OdooManager
import os
import pandas as pd
import io
from datetime import datetime

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
data_manager = OdooManager()

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
        
        return render_template('sales.html', 
                             sales_data=sales_data,
                             filter_options=filter_options,
                             selected_filters=selected_filters)
    
    except Exception as e:
        flash(f'Error al obtener datos: {str(e)}', 'danger')
        return render_template('sales.html', 
                             sales_data=[],
                             filter_options={'lineas': [], 'clientes': []},
                             selected_filters={})

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
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
        
        # Obtener datos del dashboard
        dashboard_data = data_manager.get_sales_dashboard_data(
            date_from=selected_filters['date_from'],
            date_to=selected_filters['date_to'],
            partner_id=selected_filters['partner_id'],
            linea_id=selected_filters['linea_id']
        )
        
        return render_template('dashboard.html', 
                             dashboard_data=dashboard_data,
                             filter_options=filter_options,
                             selected_filters=selected_filters)
    
    except Exception as e:
        flash(f'Error al obtener datos del dashboard: {str(e)}', 'danger')
        return render_template('dashboard.html', 
                             dashboard_data={},
                             filter_options={'lineas': [], 'clientes': []},
                             selected_filters={})

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
        
        # Crear DataFrame
        df = pd.DataFrame(sales_data)
        
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

if __name__ == '__main__':
    print("🚀 Iniciando Dashboard de Ventas Farmacéuticas...")
    print("📊 Disponible en: http://127.0.0.1:5000")
    print("🔐 Usuario: configurado en .env")
    app.run(debug=True)
