# app.py - Versión Completa y Actualizada

from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from dotenv import load_dotenv
from odoo_manager import OdooManager
import os
import pandas as pd
import io

# Cargar variables de entorno
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
data_manager = OdooManager()

# ... (tus rutas /login y /logout no cambian) ...
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

# **NUEVA RUTA DE EXPORTACIÓN**
@app.route('/export/excel')
def export_excel():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Obtiene el mismo término de búsqueda que la tabla de inventario
    search_term = request.args.get('search_term', '')
    inventory_data = data_manager.get_stock_inventory(search_term)

    if not inventory_data:
        flash('No hay datos para exportar.', 'warning')
        return redirect(url_for('inventory'))

    # Convierte los datos a un DataFrame de Pandas
    df = pd.DataFrame(inventory_data)
    
    # Crea un buffer en memoria para guardar el archivo Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventario')
    output.seek(0)

    # Envía el archivo al usuario para su descarga
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='inventario_stock.xlsx'
    )

# ... (tus rutas /dashboard y / (inventory) no cambian) ...
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session: return redirect(url_for('login'))
    selected_category_id = request.form.get('category_id', type=int)
    dashboard_data = data_manager.get_dashboard_data(category_id=selected_category_id)
    all_categories = data_manager.get_all_categories()
    if not dashboard_data:
        flash('No hay datos de inventario para mostrar en el dashboard.', 'warning')
        return redirect(url_for('inventory'))
    return render_template('dashboard.html', data=dashboard_data, categories=all_categories, selected_id=selected_category_id)

@app.route('/', methods=['GET', 'POST'])
def inventory():
    if 'username' not in session: return redirect(url_for('login'))
    search_term = ""
    if request.method == 'POST':
        search_term = request.form.get('search_term', '')
    else:
        search_term = request.args.get('search_term', '')
    stock_data = data_manager.get_stock_inventory(search_term)
    return render_template('inventory.html', inventory=stock_data, search_term=search_term)

# ... (if __name__ == '__main__' no cambia) ...
if __name__ == '__main__':
    app.run(debug=True)