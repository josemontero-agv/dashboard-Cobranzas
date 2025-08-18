# app.py

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
            return redirect(url_for('inventory'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Has cerrado la sesión.', 'info')
    return redirect(url_for('login'))

@app.route('/export/excel')
def export_excel():
    if 'username' not in session: return redirect(url_for('login'))
    
    # Pasamos todos los filtros posibles a la función de exportación
    selected_filters = {
        'search_term': request.args.get('search_term'),
        'product_id': request.args.get('product_id', type=int),
        'grupo_id': request.args.get('grupo_id', type=int),
        'linea_id': request.args.get('linea_id', type=int),
        'lugar_id': request.args.get('lugar_id', type=int)
    }
    
    inventory_data = data_manager.get_stock_inventory(**selected_filters)
    
    if not inventory_data:
        flash('No hay datos para exportar.', 'warning')
        return redirect(url_for('inventory'))
    
    export_df_data = [{k: v for k, v in item.items() if k not in ['product_id', 'grupo_articulo_id']} for item in inventory_data]
    df = pd.DataFrame(export_df_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventario')
    output.seek(0)
    
    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
    filename = f"inventario_stock_{timestamp}.xlsx"
    
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=filename)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session: return redirect(url_for('login'))
    
    selected_category_id = request.form.get('category_id', type=int)
    dashboard_data = data_manager.get_dashboard_data(category_id=selected_category_id)
    
    full_inventory = data_manager.get_stock_inventory()
    if full_inventory:
        unique_categories_dict = {
            item.get('grupo_articulo_id'): item.get('grupo_articulo') 
            for item in full_inventory if item.get('grupo_articulo_id')
        }
        available_categories = [{'id': id, 'display_name': name} for id, name in unique_categories_dict.items()]
        available_categories.sort(key=lambda x: x['display_name'])
    else:
        available_categories = []

    if not dashboard_data:
        flash('No hay datos de inventario para mostrar en el dashboard.', 'warning')
        return redirect(url_for('inventory'))
    
    return render_template('dashboard.html', data=dashboard_data, categories=available_categories, selected_id=selected_category_id)

# **RUTA DE INVENTARIO MODIFICADA**
@app.route('/', methods=['GET', 'POST'])
def inventory():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    filter_options = data_manager.get_filter_options()
    
    # Usamos request.values que combina los datos del formulario (POST) y de la URL (GET)
    selected_filters = {
        'search_term': request.values.get('search_term'),
        'product_id': request.values.get('product_id', type=int), # <-- Leemos el product_id
        'grupo_id': request.values.get('grupo_id', type=int),
        'linea_id': request.values.get('linea_id', type=int),
        'lugar_id': request.values.get('lugar_id', type=int)
    }

    # Pasamos todos los filtros a la función de búsqueda
    stock_data = data_manager.get_stock_inventory(**selected_filters)
    
    return render_template(
        'inventory.html', 
        inventory=stock_data, 
        filter_options=filter_options,
        selected_filters=selected_filters
    )

if __name__ == '__main__':
    app.run(debug=True)