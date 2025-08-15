# odoo_manager.py

import xmlrpc.client
import os

class OdooManager:
    # ... (el __init__ y authenticate_user no cambian) ...
    def __init__(self):
        self.url = os.getenv('ODOO_URL')
        self.db = os.getenv('ODOO_DB')
        self.user = os.getenv('ODOO_USER')
        self.password = os.getenv('ODOO_PASSWORD')
        self.uid = None
        self.models = None
        self.is_connected = False
        try:
            common_url = f'{self.url}/xmlrpc/2/common'
            models_url = f'{self.url}/xmlrpc/2/object'
            common = xmlrpc.client.ServerProxy(common_url)
            self.uid = common.authenticate(self.db, self.user, self.password, {})
            if self.uid:
                self.models = xmlrpc.client.ServerProxy(models_url)
                self.is_connected = True
                print("✅ Conexión principal a Odoo establecida con xmlrpc.client.")
            else:
                 print("❌ Error de autenticación en la conexión principal.")
        except Exception as e:
            print(f"❌ Error en la conexión principal a Odoo: {e}")

    def authenticate_user(self, username, password):
        if not self.is_connected: return False
        try:
            common_url = f'{self.url}/xmlrpc/2/common'
            common = xmlrpc.client.ServerProxy(common_url)
            user_uid = common.authenticate(self.db, username, password, {})
            return bool(user_uid)
        except Exception:
            return False

    def get_stock_inventory(self, search_term=None, product_id=None):
        if not self.is_connected:
            return []
        
        try:
            domain = [
                ('location_id.usage', '=', 'internal'),
                ('quantity', '>', 0),
                ('location_id', '=', 'ALMC/Stock/Comercial')
            ]
            
            if product_id:
                domain.append(('product_id', '=', product_id))
            elif search_term:
                search_domain = [
                    '|',
                        ('product_id.default_code', 'ilike', search_term),
                    '|',
                        ('product_id.name', 'ilike', search_term),
                        ('lot_id.name', 'ilike', search_term)
                ]
                domain.extend(search_domain)

            quant_fields = ['product_id', 'location_id', 'quantity', 'reserved_quantity', 'lot_id', 'product_uom_id']
            stock_quants = self.models.execute_kw(self.db, self.uid, self.password, 'stock.quant', 'search_read', [domain], {'fields': quant_fields, 'order': 'product_id'})
            
            if not stock_quants:
                return []

            product_ids = list(set(quant['product_id'][0] for quant in stock_quants))
            
            product_details = self.models.execute_kw(self.db, self.uid, self.password, 'product.product', 'read', [product_ids], {'fields': ['categ_id']})
            
            # **MEJORA**: El mapa ahora guarda ID y Nombre de la categoría
            product_category_map = {
                prod['id']: prod.get('categ_id', [0, 'Sin Categoría']) 
                for prod in product_details
            }

            inventory_list = []
            for quant in stock_quants:
                prod_id = quant['product_id'][0]
                category_info = product_category_map.get(prod_id, [0, 'Sin Categoría'])
                inventory_list.append({
                    'product_id': prod_id,
                    'category_id': category_info[0], # Devolvemos el ID de la categoría
                    'category_name': category_info[1], # Devolvemos el Nombre de la categoría
                    'product_name': quant.get('product_id', [0, 'N/A'])[1],
                    'location_name': quant.get('location_id', [0, 'N/A'])[1],
                    'quantity': quant.get('quantity', 0),
                    'reserved_quantity': quant.get('reserved_quantity', 0),
                    'lot_name': quant.get('lot_id', [0, 'N/A'])[1] if quant.get('lot_id') else 'N/A',
                    'uom_name': quant.get('product_uom_id', [0, 'N/A'])[1]
                })
            
            return inventory_list
        except Exception as e:
            print(f"Error al obtener el inventario de Odoo: {e}")
            return []

    # **MÉTODO ELIMINADO**: Ya no necesitamos get_all_categories
    # def get_all_categories(self): ...

    def get_dashboard_data(self, category_id=None):
        full_inventory = self.get_stock_inventory()
        if not full_inventory: return None

        inventory = full_inventory
        if category_id:
            # Filtramos por el ID de la categoría, que ahora está en los datos
            inventory = [item for item in full_inventory if item['category_id'] == category_id]

        if not inventory: 
            return {'kpi_total_products': 0, 'kpi_total_quantity': 0, 'chart_labels': [], 'chart_ids': [], 'chart_data': []}

        product_totals = {}
        for item in inventory:
            product_name = item['product_name']
            quantity = item['quantity']
            product_id = item['product_id']
            if product_name in product_totals:
                product_totals[product_name]['quantity'] += quantity
            else:
                product_totals[product_name] = {'quantity': quantity, 'id': product_id}
        
        total_products = len(product_totals)
        total_quantity = sum(item['quantity'] for item in product_totals.values())

        sorted_products = sorted(product_totals.items(), key=lambda x: x[1]['quantity'], reverse=True)
        top_5_products = sorted_products[:5]
        
        chart_labels = [item[0] for item in top_5_products]
        chart_data = [item[1]['quantity'] for item in top_5_products]
        chart_ids = [item[1]['id'] for item in top_5_products]

        return {
            'kpi_total_products': total_products,
            'kpi_total_quantity': int(total_quantity),
            'chart_labels': chart_labels,
            'chart_ids': chart_ids,
            'chart_data': chart_data
        }