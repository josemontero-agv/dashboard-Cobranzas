#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from odoo_manager import OdooManager

def test_data():
    print("🧪 Probando obtención de datos...")
    
    om = OdooManager()
    
    if not om.uid:
        print("❌ No hay conexión a Odoo")
        return
    
    print(f"✅ Conectado con UID: {om.uid}")
    
    # Test obtener opciones de filtro
    try:
        filter_options = om.get_filter_options()
        print(f"📋 Filtros disponibles:")
        print(f"  - Líneas comerciales: {len(filter_options.get('lineas', []))}")
        print(f"  - Clientes: {len(filter_options.get('clientes', []))}")
    except Exception as e:
        print(f"❌ Error obteniendo filtros: {e}")
    
    # Test obtener líneas de venta
    try:
        sales_data = om.get_sales_lines(limit=10)
        print(f"📊 Líneas de venta: {len(sales_data)} obtenidas")
        
        if sales_data:
            first = sales_data[0]
            print(f"  - Primera línea:")
            print(f"    Cliente: {first.get('partner_name', 'N/A')}")
            print(f"    Producto: {first.get('name', 'N/A')}")
            print(f"    Monto: S/ {abs(first.get('balance', 0)):,.2f}")
            
    except Exception as e:
        print(f"❌ Error obteniendo ventas: {e}")
        import traceback
        traceback.print_exc()
    
    # Test dashboard data
    try:
        dashboard_data = om.get_sales_dashboard_data()
        print(f"📈 Dashboard:")
        print(f"  - Total ventas: S/ {dashboard_data.get('kpi_total_sales', 0):,.2f}")
        print(f"  - Total facturas: {dashboard_data.get('kpi_total_invoices', 0)}")
        
    except Exception as e:
        print(f"❌ Error obteniendo dashboard: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_data()
