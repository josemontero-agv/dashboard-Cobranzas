# odoo_manager.py

import xmlrpc.client
import os
import pandas as pd
from datetime import datetime, timedelta

class OdooManager:
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

    def get_stock_inventory(self, search_term=None, product_id=None, grupo_id=None, linea_id=None, lugar_id=None):
        if not self.is_connected:
            return []
        try:
            domain = [('location_id.usage', '=', 'internal'), ('available_quantity', '>', 0)]
            
            if lugar_id:
                # Si el usuario selecciona un lugar específico del filtro, lo usamos.
                domain.append(('location_id', '=', lugar_id))
            else:
                # **MEJORA**: Si no hay filtro, por defecto buscamos en la lista de 6 ubicaciones.
                default_locations = [
                    'ALMC/Stock/Corto Vencimiento/VCTO1A3M',
                    'ALMC/Stock/Corto Vencimiento/VCTO3A6M',
                    'ALMC/Stock/Corto Vencimiento/VCTO6A9M',
                    'ALMC/Stock/Corto Vencimiento/VCTO9A12M',
                    'ALMC/Stock/Comercial',
                    'ALMC/Stock/PCP/Exportacion'
                ]
                domain.append(('location_id', 'in', default_locations))

            if grupo_id:
                domain.append(('product_id.categ_id', '=', grupo_id))
            
            if linea_id:
                domain.append(('product_id.commercial_line_national_id', '=', linea_id))

            if product_id:
                domain.append(('product_id', '=', product_id))
            elif search_term:
                search_domain = ['|', ('product_id.default_code', 'ilike', search_term), '|', ('product_id.name', 'ilike', search_term), ('lot_id.name', 'ilike', search_term)]
                domain.extend(search_domain)
            
            quant_fields = ['product_id', 'location_id', 'available_quantity', 'lot_id', 'product_uom_id']
            stock_quants = self.models.execute_kw(self.db, self.uid, self.password, 'stock.quant', 'search_read', [domain], {'fields': quant_fields})
            
            if not stock_quants: return []

            product_ids = list(set(quant['product_id'][0] for quant in stock_quants))
            lot_ids = list(set(quant['lot_id'][0] for quant in stock_quants if quant.get('lot_id')))

            product_fields = ['display_name', 'default_code', 'categ_id', 'commercial_line_national_id']
            product_details = self.models.execute_kw(self.db, self.uid, self.password, 'product.product', 'read', [product_ids], {'fields': product_fields})
            product_map = {prod['id']: prod for prod in product_details}

            lot_map = {}
            if lot_ids:
                lot_details = self.models.execute_kw(self.db, self.uid, self.password, 'stock.lot', 'read', [lot_ids], {'fields': ['expiration_date']})
                lot_map = {lot['id']: lot for lot in lot_details}

            inventory_list = []
            for quant in stock_quants:
                prod_id = quant['product_id'][0]
                product_data = product_map.get(prod_id, {})
                lot_data = lot_map.get(quant.get('lot_id', [0])[0]) if quant.get('lot_id') else {}
                
                def get_related_name(data):
                    return data[1] if isinstance(data, list) and len(data) > 1 else ''

                exp_date_str = lot_data.get('expiration_date', '')
                formatted_exp_date = ''
                if exp_date_str:
                    try:
                        date_part = exp_date_str.split(' ')[0]
                        dt_obj = datetime.strptime(date_part, '%Y-%m-%d')
                        formatted_exp_date = dt_obj.strftime('%d-%m-%Y')
                    except ValueError:
                        formatted_exp_date = exp_date_str
                
                months_to_expire = None
                if formatted_exp_date:
                    try:
                        exp_date_obj = datetime.strptime(formatted_exp_date, '%d-%m-%Y')
                        today = datetime.now()
                        months_to_expire = (exp_date_obj.year - today.year) * 12 + (exp_date_obj.month - today.month)
                    except ValueError:
                        months_to_expire = None

                inventory_list.append({
                    'product_id': prod_id,
                    'grupo_articulo_id': product_data.get('categ_id', [0, ''])[0],
                    'grupo_articulo': get_related_name(product_data.get('categ_id')),
                    'linea_comercial': get_related_name(product_data.get('commercial_line_national_id')),
                    'cod_articulo': product_data.get('default_code', ''),
                    'producto': product_data.get('display_name', ''),
                    'um': get_related_name(quant.get('product_uom_id')),
                    'lugar': get_related_name(quant.get('location_id')),
                    'lote': get_related_name(quant.get('lot_id')),
                    'fecha_expira': formatted_exp_date,
                    'cantidad_disponible': f"{quant.get('available_quantity', 0):.3f}",
                    'meses_expira': months_to_expire
                })
            
            inventory_list.sort(key=lambda item: item['meses_expira'] if item['meses_expira'] is not None else float('inf'))
            return inventory_list
        except Exception as e:
            print(f"Error al obtener el inventario de Odoo: {e}")
            return []

    def get_filter_options(self):
        if not self.is_connected:
            return {}
        try:
            grupos = self.models.execute_kw(self.db, self.uid, self.password, 'product.category', 'search_read', [[]], {'fields': ['id', 'display_name'], 'order': 'display_name'})
            lineas = self.models.execute_kw(self.db, self.uid, self.password, 'agr.sales.comercial.division', 'search_read', [[]], {'fields': ['id', 'display_name'], 'order': 'display_name'})
            quants_with_location = self.models.execute_kw(
                self.db, self.uid, self.password, 'stock.quant', 'search_read',
                [[('quantity', '>', 0), ('location_id.usage', '=', 'internal')]],
                {'fields': ['location_id']}
            )
            unique_locations = {quant['location_id'][0]: quant['location_id'][1] for quant in quants_with_location if quant['location_id']}
            lugares = [{'id': id, 'display_name': name} for id, name in unique_locations.items()]
            lugares.sort(key=lambda x: x['display_name'])
            return {'grupos': grupos, 'lineas': lineas, 'lugares': lugares}
        except Exception as e:
            print(f"Error al obtener opciones de filtro: {e}")
            return {'grupos': [], 'lineas': [], 'lugares': []}

    def get_dashboard_data(self, category_id=None):
        full_inventory = self.get_stock_inventory()
        if not full_inventory: return None
        inventory = full_inventory
        if category_id:
            inventory = [item for item in full_inventory if item['grupo_articulo_id'] == category_id]
        if not inventory: return {'kpi_total_products': 0, 'kpi_total_quantity': 0, 'chart_labels': [], 'chart_ids': [], 'chart_data': []}
        product_totals = {}
        for item in inventory:
            product_name = item['producto']
            quantity = float(item['cantidad_disponible'].replace(',', ''))
            if product_name in product_totals:
                product_totals[product_name]['quantity'] += quantity
            else:
                product_totals[product_name] = {'quantity': quantity, 'id': item.get('product_id', 0)}
        total_products = len(product_totals)
        total_quantity = sum(item['quantity'] for item in product_totals.values())
        sorted_products = sorted(product_totals.items(), key=lambda x: x[1]['quantity'], reverse=True)
        top_5_products = sorted_products[:5]
        chart_labels = [item[0] for item in top_5_products]
        chart_data = [item[1]['quantity'] for item in top_5_products]
        chart_ids = [item[1]['id'] for item in top_5_products]
        return {'kpi_total_products': total_products, 'kpi_total_quantity': int(total_quantity), 'chart_labels': chart_labels, 'chart_ids': chart_ids, 'chart_data': chart_data}