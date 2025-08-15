# app.py

from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from dotenv import load_dotenv
from odoo_manager import OdooManager
import os
import pandas as pd
import io

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
data_manager = OdooManager()

# ... (tus rutas /login, /logout y /export/excel no cambian) ...
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
    search_term = request.args.get('search_term', '')
    product_id = request.args.get('product_id', type=int)
    inventory_data = data_manager.get_stock_inventory(search_term=search_term, product_id=product_id)
    if not inventory_data:
        flash('No hay datos para exportar.', 'warning')
        return redirect(url_for('inventory'))
    # Preparamos el DataFrame para exportar
    export_df_data = [{k: v for k, v in item.items() if k not in ['product_id', 'category_id']} for item in inventory_data]
    df = pd.DataFrame(export_df_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventario')
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='inventario_stock.xlsx')

# **RUTA MODIFICADA**
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    selected_category_id = request.form.get('category_id', type=int)
    dashboard_data = data_manager.get_dashboard_data(category_id=selected_category_id)
    
    # **MEJORA**: Obtenemos las categorías del inventario, no todas las de Odoo
    full_inventory = data_manager.get_stock_inventory()
    if full_inventory:
        # Creamos una lista de categorías únicas presentes en el inventario
        unique_categories_dict = {item['category_id']: item['category_name'] for item in full_inventory}
        available_categories = [{'id': id, 'display_name': name} for id, name in unique_categories_dict.items()]
        # Ordenamos alfabéticamente
        available_categories.sort(key=lambda x: x['display_name'])
    else:
        available_categories = []

    if not dashboard_data:
        flash('No hay datos de inventario para mostrar en el dashboard.', 'warning')
        return redirect(url_for('inventory'))
    
    return render_template('dashboard.html', data=dashboard_data, categories=available_categories, selected_id=selected_category_id)

@app.route('/', methods=['GET', 'POST'])
def inventory():
    # ... (esta ruta no cambia) ...
    if 'username' not in session: return redirect(url_for('login'))
    search_term = ""
    product_id = None
    if request.method == 'POST':
        search_term = request.form.get('search_term', '')
        stock_data = data_manager.get_stock_inventory(search_term=search_term)
    else: # GET
        product_id = request.args.get('product_id', type=int)
        stock_data = data_manager.get_stock_inventory(product_id=product_id)
    return render_template('inventory.html', inventory=stock_data, search_term=search_term)

if __name__ == '__main__':
    app.run(debug=True)