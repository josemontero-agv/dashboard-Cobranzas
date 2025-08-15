# odoo_manager.py

import xmlrpc.client
import os

class OdooManager:
    def __init__(self):
        """
        Inicializa la conexión a Odoo usando la librería estándar xmlrpc.client.
        """
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
        """
        Verifica si un usuario y contraseña son válidos en Odoo.
        """
        if not self.is_connected:
            return False
        try:
            common_url = f'{self.url}/xmlrpc/2/common'
            common = xmlrpc.client.ServerProxy(common_url)
            user_uid = common.authenticate(self.db, username, password, {})
            return bool(user_uid)
        except Exception:
            return False

    def get_stock_inventory(self, search_term=None):
        """
        Obtiene el inventario, filtrado por la ubicación final, y añade la categoría del producto.
        """
        if not self.is_connected:
            return []
        
        try:
            domain = [
                ('location_id.usage', '=', 'internal'),
                ('quantity', '>', 0),
                ('location_id', '=', 'ALMC/Stock/Comercial')
            ]
            
            if search_term:
                domain.append(('product_id.name', 'ilike', search_term))
            
            quant_fields = ['product_id', 'location_id', 'quantity', 'reserved_quantity', 'lot_id', 'product_uom_id']
            stock_quants = self.models.execute_kw(
                self.db, self.uid, self.password,
                'stock.quant', 'search_read',
                [domain],
                {'fields': quant_fields, 'order': 'product_id'}
            )
            
            if not stock_quants:
                return []

            product_ids = list(set(quant['product_id'][0] for quant in stock_quants))
            
            product_details = self.models.execute_kw(
                self.db, self.uid, self.password,
                'product.product', 'read',
                [product_ids],
                {'fields': ['categ_id']}
            )
            
            product_category_map = {
                prod['id']: prod.get('categ_id', [0, 'Sin Categoría'])[1] 
                for prod in product_details
            }

            inventory_list = []
            for quant in stock_quants:
                product_id = quant['product_id'][0]
                inventory_list.append({
                    'category_name': product_category_map.get(product_id, 'Sin Categoría'),
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

    def get_all_categories(self):
        """
        Obtiene una lista de todas las categorías de productos.
        """
        if not self.is_connected:
            return []
        try:
            categories = self.models.execute_kw(
                self.db, self.uid, self.password,
                'product.category', 'search_read',
                [[]],
                {'fields': ['id', 'display_name'], 'order': 'display_name'}
            )
            return categories
        except Exception as e:
            print(f"Error al obtener las categorías: {e}")
            return []

    def get_dashboard_data(self, category_id=None):
        """
        Calcula los datos para el dashboard, agrupando las cantidades por producto.
        """
        full_inventory = self.get_stock_inventory()

        if not full_inventory:
            return None

        inventory = full_inventory
        if category_id:
            category_info = self.models.execute_kw(
                self.db, self.uid, self.password,
                'product.category', 'read', [category_id], {'fields': ['display_name']}
            )
            if category_info:
                category_name = category_info[0]['display_name']
                inventory = [item for item in full_inventory if item['category_name'] == category_name]

        if not inventory:
            return {'kpi_total_products': 0, 'kpi_total_quantity': 0, 'chart_labels': [], 'chart_data': []}

        product_totals = {}
        for item in inventory:
            product_name = item['product_name']
            quantity = item['quantity']
            if product_name in product_totals:
                product_totals[product_name] += quantity
            else:
                product_totals[product_name] = quantity
        
        total_products = len(product_totals)
        total_quantity = sum(product_totals.values())

        sorted_products = sorted(product_totals.items(), key=lambda x: x[1], reverse=True)
        top_5_products = sorted_products[:5]
        
        chart_labels = [item[0] for item in top_5_products]
        chart_data = [item[1] for item in top_5_products]

        return {
            'kpi_total_products': total_products,
            'kpi_total_quantity': int(total_quantity),
            'chart_labels': chart_labels,
            'chart_data': chart_data
        }