from odoo_manager import OdooManager

# Crear instancia del manager
om = OdooManager()

print("🔍 Probando obtención de líneas comerciales...")

# Probar get_sales_filter_options
filter_options = om.get_sales_filter_options()
print(f"📊 Filter options: {filter_options}")

# Mostrar líneas comerciales
lineas = filter_options.get('lineas', [])
print(f"📋 Número de líneas comerciales encontradas: {len(lineas)}")

for i, linea in enumerate(lineas[:10]):  # Mostrar solo las primeras 10
    print(f"  {i+1}. ID: {linea.get('id')}, Nombre: {linea.get('display_name')}")

print("\n🔍 Probando método alternativo...")
# Probar get_filter_options (el método original)
filter_options_old = om.get_filter_options()
lineas_old = filter_options_old.get('lineas', [])
print(f"📋 Método antiguo - Líneas encontradas: {len(lineas_old)}")
