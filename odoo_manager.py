# -*- coding: utf-8 -*-
# odoo_manager.py - Wrapper para servicios

import xmlrpc.client
import os
import pandas as pd
from datetime import datetime, timedelta
from services.odoo_connection import OdooConnection
from services.report_service import ReportService
from services.cobranza_service import CobranzaService

class OdooManager:
    def __init__(self):
        # Inicializar servicios
        self.connection = OdooConnection()
        self.reports = ReportService(self.connection)
        self.cobranza = CobranzaService(self.connection)
        
        # Mantener atributos para retrocompatibilidad
        self.url = self.connection.url
        self.db = self.connection.db
        self.username = self.connection.username
        self.password = self.connection.password
        self.uid = self.connection.uid
        self.models = self.connection.models

    def authenticate_user(self, username, password):
        """Delegar autenticación al servicio de conexión."""
        return self.connection.authenticate_user(username, password)

    def get_sales_filter_options(self):
        """Obtener opciones para filtros de ventas"""
        try:
            # Usar el método existente que obtiene líneas comerciales del inventario
            # Esto garantiza que usamos las mismas líneas que en el resto del sistema
            existing_options = self._get_filter_options_internal()
            
            # Obtener líneas comerciales
            lineas = existing_options.get('lineas', [])
            
            # Si no hay líneas en el inventario, intentar obtenerlas directamente de productos
            if not lineas:
                try:
                    # Consulta directa a productos para obtener líneas comerciales
                    products = self.models.execute_kw(
                        self.db, self.uid, self.password, 'product.product', 'search_read',
                        [[('commercial_line_national_id', '!=', False)]],
                        {'fields': ['commercial_line_national_id'], 'limit': 1000}
                    )
                    
                    # Extraer líneas únicas
                    unique_lines = {}
                    for product in products:
                        if product.get('commercial_line_national_id'):
                            line_id, line_name = product['commercial_line_national_id']
                            unique_lines[line_id] = line_name
                    
                    # Formatear líneas
                    lineas = [
                        {'id': line_id, 'display_name': line_name}
                        for line_id, line_name in unique_lines.items()
                    ]
                    lineas.sort(key=lambda x: x['display_name'])
                    
                except Exception as product_error:
                    print(f"Error obteniendo líneas de productos: {product_error}")
            
            # Para compatibilidad con diferentes templates
            commercial_lines = lineas
            
            # Obtener clientes
            partners = self.models.execute_kw(
                self.db, self.uid, self.password, 'res.partner', 'search_read',
                [[('customer_rank', '>', 0)]],
                {'fields': ['id', 'name'], 'limit': 100}
            )
            
            # Formatear clientes
            clientes = [
                {'id': p['id'], 'display_name': p['name']}
                for p in partners
            ]
            
            return {
                'commercial_lines': commercial_lines,
                'lineas': lineas,  # Para compatibilidad con meta.html
                'partners': partners,
                'clientes': clientes  # Para compatibilidad
            }
            
        except Exception as e:
            print(f"Error al obtener opciones de filtro de ventas: {e}")
            return {'commercial_lines': [], 'lineas': [], 'partners': [], 'clientes': []}

    def get_filter_options(self):
        """Alias para get_sales_filter_options para compatibilidad"""
        return self.get_sales_filter_options()

    def get_all_sellers(self):
        """Obtiene una lista única de todos los vendedores (invoice_user_id)."""
        try:
            if not self.uid or not self.models:
                return []
            
            # Usamos read_group para obtener vendedores únicos de forma eficiente
            seller_groups = self.models.execute_kw(
                self.db, self.uid, self.password, 'account.move', 'read_group',
                [[('invoice_user_id', '!=', False)]],
                {'fields': ['invoice_user_id'], 'groupby': ['invoice_user_id']}
            )
            
            # Formatear la lista para el frontend
            sellers = []
            for group in seller_groups:
                if group.get('invoice_user_id'):
                    seller_id, seller_name = group['invoice_user_id']
                    sellers.append({'id': seller_id, 'name': seller_name})
            
            return sorted(sellers, key=lambda x: x['name'])
        except Exception as e:
            print(f"Error obteniendo la lista de vendedores: {e}")
            return []

    def get_sales_lines(self, page=None, per_page=None, filters=None, date_from=None, date_to=None, partner_id=None, linea_id=None, search=None, limit=5000):
        """Obtener líneas de venta completas con todas las 27 columnas"""
        try:
            print(f"🔍 Obteniendo líneas de venta completas...")
            
            # Verificar conexión
            if not self.uid or not self.models:
                print("❌ No hay conexión a Odoo disponible")
                if page is not None and per_page is not None:
                    return [], {'page': page, 'per_page': per_page, 'total': 0, 'pages': 0}
                return []
            
            # Manejar parámetros de ambos formatos de llamada
            if filters:
                date_from = filters.get('date_from')
                date_to = filters.get('date_to')
                partner_id = filters.get('partner_id')
                linea_id = filters.get('linea_id')
                search = filters.get('search')
            
            # Construir dominio de filtro
            domain = [
                ('move_id.move_type', 'in', ['out_invoice', 'out_refund']),
                ('move_id.state', '=', 'posted'),
                ('product_id.default_code', '!=', False)  # Solo productos con código
            ]
            
            # Filtros de exclusión de categorías específicas
            excluded_categories = [315, 333, 304, 314, 318, 339]
            domain.append(('product_id.categ_id', 'not in', excluded_categories))
            
            # Filtros de fecha
            if date_from:
                domain.append(('move_id.invoice_date', '>=', date_from))
            if date_to:
                domain.append(('move_id.invoice_date', '<=', date_to))
            
            # Filtro de cliente
            if partner_id:
                domain.append(('partner_id', '=', partner_id))
            
            # Filtro de línea comercial
            if linea_id:
                domain.append(('product_id.commercial_line_national_id', '=', linea_id))
            
            # Obtener líneas base con todos los campos necesarios
            query_options = {
                'fields': [
                    'move_id', 'partner_id', 'product_id', 'balance', 'move_name',
                    'quantity', 'price_unit', 'tax_ids'
                ],
                'context': {'lang': 'es_PE'}
            }
            
            # Solo agregar limit si no es None (XML-RPC no maneja None)
            if limit is not None:
                query_options['limit'] = limit
            
            sales_lines_base = self.models.execute_kw(
                self.db, self.uid, self.password, 'account.move.line', 'search_read',
                [domain],
                query_options
            )
            
            print(f"📊 Base obtenida: {len(sales_lines_base)} líneas")
            
            if not sales_lines_base:
                return []
            
            # Obtener IDs únicos para consultas relacionadas
            move_ids = list(set([line['move_id'][0] for line in sales_lines_base if line.get('move_id')]))
            product_ids = list(set([line['product_id'][0] for line in sales_lines_base if line.get('product_id')]))
            partner_ids = list(set([line['partner_id'][0] for line in sales_lines_base if line.get('partner_id')]))
            
            print(f"📊 IDs únicos: {len(move_ids)} facturas, {len(product_ids)} productos, {len(partner_ids)} clientes")
            
            # Obtener datos de facturas (account.move) - Asientos contables
            move_data = {}
            if move_ids:
                moves = self.models.execute_kw(
                    self.db, self.uid, self.password, 'account.move', 'search_read',
                    [[('id', 'in', move_ids)]],
                    {
                        'fields': [
                            'payment_state', 'team_id', 'invoice_user_id', 'invoice_origin',
                            'invoice_date', 'l10n_latam_document_type_id', 'origin_number',
                            'order_id', 'name', 'ref', 'journal_id', 'amount_total', 'state'
                        ],
                        'context': {'lang': 'es_PE'}
                    }
                )
                move_data = {m['id']: m for m in moves}
                print(f"✅ Asientos contables (account.move): {len(move_data)} registros")
            
            # Obtener datos de productos con todos los campos farmacéuticos
            product_data = {}
            if product_ids:
                products = self.models.execute_kw(
                    self.db, self.uid, self.password, 'product.product', 'search_read',
                    [[('id', 'in', product_ids)]],
                    {
                        'fields': [
                            'name', 'default_code', 'categ_id', 'commercial_line_national_id',
                            'pharmacological_classification_id', 'pharmaceutical_forms_id',
                            'administration_way_id', 'production_line_id', 'product_life_cycle',
                        ],
                        'context': {'lang': 'es_PE'}
                    }
                )
                product_data = {p['id']: p for p in products}
                # --- DEBUG: Imprimir los campos del primer producto para verificar el nombre del campo ---
                if products:
                    print("🔍 DEBUG: Campos del primer producto obtenido:")
                    print(products[0])
                # --- FIN DEBUG ---
                print(f"✅ Productos: {len(product_data)} registros")
            
            # Obtener datos de clientes
            partner_data = {}
            if partner_ids:
                partners = self.models.execute_kw(
                    self.db, self.uid, self.password, 'res.partner', 'search_read',
                    [[('id', 'in', partner_ids)]],
                    {'fields': ['vat', 'name'], 'context': {'lang': 'es_PE'}}
                )
                partner_data = {p['id']: p for p in partners}
                print(f"✅ Clientes: {len(partner_data)} registros")
            
            # Obtener datos de órdenes de venta con más campos
            order_ids = [move['order_id'][0] for move in move_data.values() if move.get('order_id')]
            order_data = {}
            if order_ids:
                orders = self.models.execute_kw(
                    self.db, self.uid, self.password, 'sale.order', 'search_read',
                    [[('id', 'in', list(set(order_ids)))]],
                    {
                        'fields': [
                            'name', 'delivery_observations', 'partner_supplying_agency_id', 
                            'partner_shipping_id', 'date_order', 'state', 'amount_total',
                            'user_id', 'team_id', 'warehouse_id', 'commitment_date',
                            'client_order_ref', 'origin',
                        ]
                    }
                )
                order_data = {o['id']: o for o in orders}
                print(f"✅ Órdenes de venta (sale.order): {len(order_data)} registros con observaciones de entrega")
            
            # Obtener datos de líneas de orden de venta con más campos
            sale_line_data = {}
            if order_ids and product_ids:
                try:
                    sale_lines = self.models.execute_kw(
                        self.db, self.uid, self.password, 'sale.order.line', 'search_read',
                        [[('order_id', 'in', list(set(order_ids))), ('product_id', 'in', product_ids)]],
                        {
                            'fields': [
                                'order_id', 'product_id', 'route_id', 'name', 'product_uom_qty',
                                'price_unit', 'price_subtotal', 'discount', 'product_uom',
                                'analytic_distribution', 'display_type'
                            ],
                            'context': {'lang': 'es_PE'}
                        }
                    )
                    for sl in sale_lines:
                        if sl.get('order_id') and sl.get('product_id'):
                            key = (sl['order_id'][0], sl['product_id'][0])
                            sale_line_data[key] = sl
                    print(f"✅ Líneas de orden de venta (sale.order.line): {len(sale_line_data)} registros con rutas")
                except Exception as e:
                    print(f"⚠️ Error obteniendo líneas de orden: {e}")
            
            # Obtener todos los tax_ids únicos de las líneas contables
            all_tax_ids = set()
            for line in sales_lines_base:
                if line.get('tax_ids'):
                    all_tax_ids.update(line['tax_ids'])
            tax_names = {}
            if all_tax_ids:
                taxes = self.models.execute_kw(
                    self.db, self.uid, self.password, 'account.tax', 'search_read',
                    [[('id', 'in', list(all_tax_ids))]],
                    {'fields': ['id', 'name'], 'context': {'lang': 'es_PE'}}
                )
                tax_names = {t['id']: t['name'] for t in taxes}
            
            # Procesar y combinar todos los datos para las 27 columnas
            sales_lines = []
            print(f"🚀 Procesando {len(sales_lines_base)} líneas con 27 columnas...")
            
            for line in sales_lines_base:
                move_id = line.get('move_id')
                product_id = line.get('product_id')
                partner_id = line.get('partner_id')
                
                # Obtener datos relacionados
                move = move_data.get(move_id[0]) if move_id else {}
                product = product_data.get(product_id[0]) if product_id else {}
                partner = partner_data.get(partner_id[0]) if partner_id else {}
                
                # Obtener datos de orden de venta
                order_id = move.get('order_id')
                order = order_data.get(order_id[0]) if order_id else {}
                
                # Obtener datos de línea de orden
                sale_line_key = (order_id[0], product_id[0]) if order_id and product_id else None
                sale_line = sale_line_data.get(sale_line_key, {}) if sale_line_key else {}
                # Obtener nombres de impuestos
                imp_list = []
                for tid in line.get('tax_ids', []):
                    if tid in tax_names:
                        imp_list.append(tax_names[tid])
                imp_str = ', '.join(imp_list) if imp_list else ''
                # Filtrar por impuestos IGV o IGV_INC
                if 'IGV' in imp_list or 'IGV_INC' in imp_list:
                    # Obtener línea comercial sin modificaciones ECOMMERCE
                    commercial_line_id = product.get('commercial_line_national_id')

                    # Crear registro completo con las 27 columnas
                    sales_lines.append({
                        # 1. Estado de Pago
                        'payment_state': move.get('payment_state'),
                        
                        # 2. Canal de Venta
                        'sales_channel_id': move.get('team_id'),
                        
                        # 3. Línea Comercial Local
                        'commercial_line_national_id': commercial_line_id,
                        
                        # 4. Vendedor
                        'invoice_user_id': move.get('invoice_user_id'),
                        
                        # 5. Socio
                        'partner_name': partner.get('name'),
                        
                        # 6. NIF
                        'vat': partner.get('vat'),
                        
                        # 7. Origen
                        'invoice_origin': move.get('invoice_origin'),
                        
                        # 7.1. Asiento Contable (move_id)
                        'move_name': move.get('name'),  # Número del asiento contable
                        'move_ref': move.get('ref'),    # Referencia del asiento
                        'move_state': move.get('state'), # Estado del asiento
                        
                        # 7.2. Orden de Venta (order_id) 
                        'order_name': order.get('name'),  # Número de la orden de venta
                        'order_origin': order.get('origin'), # Origen de la orden
                        'client_order_ref': order.get('client_order_ref'), # Referencia del cliente
                        
                        # 8. Producto
                        'name': product.get('name', ''),
                        
                        # 9. Referencia Interna
                        'default_code': product.get('default_code', ''),
                        
                        # 10. ID Producto
                        'product_id': line.get('product_id'),
                        
                        # 11. Fecha Factura
                        'invoice_date': move.get('invoice_date'),
                        
                        # 12. Tipo Documento
                        'l10n_latam_document_type_id': move.get('l10n_latam_document_type_id'),
                        
                        # 13. Número
                        'move_name': line.get('move_name'),
                        
                        # 14. Ref. Doc. Rectificado
                        'origin_number': move.get('origin_number'),
                        
                        # 15. Saldo
                        'balance': -line.get('balance', 0) if line.get('balance') is not None else 0,
                        
                        # 16. Clasificación Farmacológica
                        'pharmacological_classification_id': product.get('pharmacological_classification_id'),
                        
                        # 17. Observaciones Entrega (delivery_observations)
                        'delivery_observations': order.get('delivery_observations'),
                        
                        # 17.1. Información adicional de la orden
                        'order_date': order.get('date_order'),  # Fecha de la orden
                        'order_state': order.get('state'),      # Estado de la orden
                        'commitment_date': order.get('commitment_date'),  # Fecha compromiso
                        'order_user_id': order.get('user_id'),  # Vendedor de la orden
                        
                        # 18. Agencia
                        'partner_supplying_agency_id': order.get('partner_supplying_agency_id'),
                        
                        # 19. Formas Farmacéuticas
                        'pharmaceutical_forms_id': product.get('pharmaceutical_forms_id'),
                        
                        # 20. Vía Administración
                        'administration_way_id': product.get('administration_way_id'),
                        
                        # 21. Categoría Producto
                        'categ_id': product.get('categ_id'),
                        
                        # 22. Línea Producción
                        'production_line_id': product.get('production_line_id'),
                        
                        # 23. Cantidad
                        'quantity': line.get('quantity'),
                        
                        # 24. Precio Unitario
                        'price_unit': line.get('price_unit'),
                        
                        # 25. Dirección Entrega
                        'partner_shipping_id': order.get('partner_shipping_id'),
                        
                        # 26. Ruta
                        'route_id': sale_line.get('route_id'),
                        
                        # 27. Ciclo de Vida
                        'product_life_cycle': product.get('product_life_cycle'),
                        
                        # 28. IMP (Impuesto)
                        'tax_id': imp_str,
                        
                        # Campos adicionales para compatibilidad
                        'move_id': line.get('move_id'),
                        'partner_id': line.get('partner_id')
                    })
            
            print(f"✅ Procesadas {len(sales_lines)} líneas con 27 columnas completas")
            
            # Si se solicita paginación, devolver tupla (datos, paginación)
            if page is not None and per_page is not None:
                # Calcular paginación
                total_items = len(sales_lines)
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                paginated_data = sales_lines[start_idx:end_idx]
                
                pagination = {
                    'page': page,
                    'per_page': per_page,
                    'total': total_items,
                    'pages': (total_items + per_page - 1) // per_page
                }
                
                return paginated_data, pagination
            
            # Si no se solicita paginación, devolver solo los datos
            return sales_lines
            
        except Exception as e:
            print(f"Error al obtener las líneas de venta de Odoo: {e}")
            # Devolver formato apropiado según si se solicitó paginación
            if page is not None and per_page is not None:
                return [], {'page': page, 'per_page': per_page, 'total': 0, 'pages': 0}
            return []

    def get_sales_dashboard_data(self, date_from=None, date_to=None, linea_id=None, partner_id=None):
        """Obtener datos para el dashboard de ventas"""
        try:
            # Obtener líneas de venta
            sales_lines = self.get_sales_lines(
                date_from=date_from,
                date_to=date_to,
                partner_id=partner_id,
                linea_id=linea_id,
                limit=5000
            )
            
            # Filtrar VENTA INTERNACIONAL (exportaciones)
            sales_lines_filtered = []
            for line in sales_lines:
                # Filtrar por línea comercial
                linea_comercial = line.get('commercial_line_national_id')
                if linea_comercial and isinstance(linea_comercial, list) and len(linea_comercial) > 1:
                    nombre_linea = linea_comercial[1].upper()
                    if 'VENTA INTERNACIONAL' in nombre_linea:
                        continue
                
                # Filtrar por canal de ventas
                canal_ventas = line.get('sales_channel_id')
                if canal_ventas and isinstance(canal_ventas, list) and len(canal_ventas) > 1:
                    nombre_canal = canal_ventas[1].upper()
                    if 'VENTA INTERNACIONAL' in nombre_canal or 'INTERNACIONAL' in nombre_canal:
                        continue
                
                sales_lines_filtered.append(line)
            
            sales_lines = sales_lines_filtered  # Usar los datos filtrados
            
            if not sales_lines:
                return self._get_empty_dashboard_data()
            
            # Calcular métricas básicas
            total_sales = sum([abs(line.get('balance', 0)) for line in sales_lines])
            total_quantity = sum([line.get('quantity', 0) for line in sales_lines])
            total_lines = len(sales_lines)
            
            # Métricas por cliente
            clients_data = {}
            for line in sales_lines:
                client_name = line.get('partner_name', 'Sin Cliente')
                if client_name not in clients_data:
                    clients_data[client_name] = {'sales': 0, 'quantity': 0}
                clients_data[client_name]['sales'] += abs(line.get('balance', 0))
                clients_data[client_name]['quantity'] += line.get('quantity', 0)
            
            # Top clientes
            top_clients = sorted(clients_data.items(), key=lambda x: x[1]['sales'], reverse=True)[:10]
            
            # Métricas por producto
            products_data = {}
            for line in sales_lines:
                product_name = line.get('name', 'Sin Producto')
                if product_name not in products_data:
                    products_data[product_name] = {'sales': 0, 'quantity': 0}
                products_data[product_name]['sales'] += abs(line.get('balance', 0))
                products_data[product_name]['quantity'] += line.get('quantity', 0)
            
            # Top productos
            top_products = sorted(products_data.items(), key=lambda x: x[1]['sales'], reverse=True)[:10]
            
            # Métricas por canal
            channels_data = {}
            for line in sales_lines:
                channel = line.get('sales_channel_id')
                channel_name = channel[1] if channel and len(channel) > 1 else 'Sin Canal'
                if channel_name not in channels_data:
                    channels_data[channel_name] = {'sales': 0, 'quantity': 0}
                channels_data[channel_name]['sales'] += abs(line.get('balance', 0))
                channels_data[channel_name]['quantity'] += line.get('quantity', 0)
            
            sales_by_channel = list(channels_data.items())
            
            # Métricas por línea comercial (NUEVO)
            commercial_lines_data = {}
            for line in sales_lines:
                commercial_line = line.get('commercial_line_national_id')
                if commercial_line:
                    line_name = commercial_line[1] if commercial_line and len(commercial_line) > 1 else 'Sin Línea'
                else:
                    line_name = 'Sin Línea Comercial'
                
                if line_name not in commercial_lines_data:
                    commercial_lines_data[line_name] = {'sales': 0, 'quantity': 0}
                commercial_lines_data[line_name]['sales'] += abs(line.get('balance', 0))
                commercial_lines_data[line_name]['quantity'] += line.get('quantity', 0)
            
            # Preparar datos de líneas comerciales para el gráfico
            commercial_lines_sorted = sorted(commercial_lines_data.items(), key=lambda x: x[1]['sales'], reverse=True)
            commercial_lines = [
                {
                    'name': line_name,
                    'amount': data['sales'],
                    'quantity': data['quantity']
                } 
                for line_name, data in commercial_lines_sorted
            ]
            
            # Estadísticas de líneas comerciales
            commercial_lines_stats = {
                'total_lines': len(commercial_lines),
                'top_line_name': commercial_lines[0]['name'] if commercial_lines else 'N/A',
                'top_line_amount': commercial_lines[0]['amount'] if commercial_lines else 0
            }
            
            # Métricas por vendedor (NUEVO)
            sellers_data = {}
            for line in sales_lines:
                seller = line.get('invoice_user_id')
                if seller:
                    seller_name = seller[1] if seller and len(seller) > 1 else 'Sin Vendedor'
                else:
                    seller_name = 'Sin Vendedor Asignado'
                
                if seller_name not in sellers_data:
                    sellers_data[seller_name] = {'sales': 0, 'quantity': 0}
                sellers_data[seller_name]['sales'] += abs(line.get('balance', 0))
                sellers_data[seller_name]['quantity'] += line.get('quantity', 0)
            
            # Preparar datos de vendedores para el gráfico (Top 8 vendedores)
            sellers_sorted = sorted(sellers_data.items(), key=lambda x: x[1]['sales'], reverse=True)[:8]
            sellers = [
                {
                    'name': seller_name,
                    'amount': data['sales'],
                    'quantity': data['quantity']
                } 
                for seller_name, data in sellers_sorted
            ]
            
            # Estadísticas de vendedores
            sellers_stats = {
                'total_sellers': len(sellers_data),
                'top_seller_name': sellers[0]['name'] if sellers else 'N/A',
                'top_seller_amount': sellers[0]['amount'] if sellers else 0
            }
            
            return {
                'total_sales': total_sales,
                'total_quantity': total_quantity,
                'total_lines': total_lines,
                'top_clients': top_clients,
                'top_products': top_products,
                'sales_by_month': [],  # Puede implementarse después
                'sales_by_channel': sales_by_channel,
                # Datos específicos para líneas comerciales
                'commercial_lines': commercial_lines,
                'commercial_lines_stats': commercial_lines_stats,
                # Datos específicos para vendedores
                'sellers': sellers,
                'sellers_stats': sellers_stats,
                # Campos KPI para el template
                'kpi_total_sales': total_sales,
                'kpi_total_invoices': total_lines,
                'kpi_total_quantity': total_quantity
            }
            
        except Exception as e:
            print(f"Error obteniendo datos del dashboard: {e}")
            return self._get_empty_dashboard_data()

    def _get_empty_dashboard_data(self):
        """Datos vacíos para el dashboard"""
        return {
            'total_sales': 0,
            'total_quantity': 0,
            'total_lines': 0,
            'top_clients': [],
            'top_products': [],
            'sales_by_month': [],
            'sales_by_channel': [],
            # Datos vacíos para líneas comerciales
            'commercial_lines': [],
            'commercial_lines_stats': {
                'total_lines': 0,
                'top_line_name': 'N/A',
                'top_line_amount': 0
            },
            # Datos vacíos para vendedores
            'sellers': [],
            'sellers_stats': {
                'total_sellers': 0,
                'top_seller_name': 'N/A',
                'top_seller_amount': 0
            },
            # Campos KPI para el template
            'kpi_total_sales': 0,
            'kpi_total_invoices': 0,
            'kpi_total_quantity': 0
        }

    def get_report_lines(self, start_date=None, end_date=None, customer=None, limit=0, account_codes=None, search_term=None):
        """Delegar al servicio de reportes."""
        return self.reports.get_report_lines(start_date, end_date, customer, limit, account_codes, search_term)
    
    def get_report_internacional(self, start_date=None, end_date=None, customer=None, payment_state=None, limit=0):
        """Obtener reporte internacional con campos calculados."""
        return self.reports.get_report_internacional(start_date, end_date, customer, payment_state, limit)
    

    def get_cobranza_kpis(self, date_from=None, date_to=None, payment_state=None):
        """Obtener KPIs de cobranza para el dashboard internacional"""
        try:
            # Construir dominio
            domain = [('move_type', 'in', ['out_invoice', 'out_refund'])]
            
            if date_from:
                domain.append(('invoice_date', '>=', date_from))
            if date_to:
                domain.append(('invoice_date', '<=', date_to))
            if payment_state:
                domain.append(('payment_state', '=', payment_state))
            
            # Obtener facturas
            invoices = self.odoo_client.search_read(
                'account.move',
                domain,
                ['payment_state', 'amount_total', 'amount_residual', 'invoice_date_due'],
                limit=10000
            )
            
            # Calcular KPIs
            from datetime import date
            today = date.today()
            
            total_facturas = len(invoices)
            monto_vencido = 0.0
            monto_vigente = 0.0
            total_overdue_days = 0
            overdue_count = 0
            
            # Contadores de estados de pago
            estados_pago = {}
            
            for inv in invoices:
                residual = float(inv.get('amount_residual') or 0.0)
                due_date = inv.get('invoice_date_due')
                estado = inv.get('payment_state', 'not_paid')
                
                # Contar estados de pago
                if estado not in estados_pago:
                    estados_pago[estado] = 0
                estados_pago[estado] += 1
                
                if residual <= 0:
                    continue
                    
                if due_date:
                    try:
                        due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                        if due_date_obj < today:
                            monto_vencido += residual
                            overdue_days = (today - due_date_obj).days
                            if overdue_days > 0:
                                total_overdue_days += overdue_days
                                overdue_count += 1
                        else:
                            monto_vigente += residual
                    except:
                        monto_vigente += residual
                else:
                    monto_vigente += residual
            
            promedio_dias_morosidad = (total_overdue_days / overdue_count) if overdue_count else 0.0
            
            # Formatear estados de pago
            estados_pago_data = []
            estado_names = {
                'not_paid': 'No Pagado',
                'in_payment': 'En Pago',
                'paid': 'Pagado',
                'partial': 'Parcial',
                'reversed': 'Reversado'
            }
            
            for estado, count in estados_pago.items():
                estados_pago_data.append({
                    'name': estado_names.get(estado, estado),
                    'value': count
                })
            
            return {
                'total_facturas': total_facturas,
                'monto_vencido': round(monto_vencido, 2),
                'monto_vigente': round(monto_vigente, 2),
                'promedio_dias_morosidad': round(promedio_dias_morosidad, 2),
                'estados_pago': estados_pago_data,
                'cobranza_por_linea': {
                    'labels': ['Línea A', 'Línea B', 'Línea C', 'Línea D'],
                    'values': [15000, 22000, 18000, 12000]  # Datos de ejemplo
                },
                'morosidad_series': {
                    'labels': ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
                    'values': [15, 18, 22, 19, 25, 28]  # Datos de ejemplo
                }
            }
            
        except Exception as e:
            print(f"Error obteniendo KPIs de cobranza: {e}")
            return {
                'total_facturas': 0,
                'monto_vencido': 0,
                'monto_vigente': 0,
                'promedio_dias_morosidad': 0,
                'estados_pago': [],
                'morosidad_series': {'labels': [], 'values': []}
            }

    def get_top15_cobranza(self, date_from=None, date_to=None, payment_state=None):
        """Obtener top 15 clientes con mayor deuda"""
        try:
            # Construir dominio
            domain = [('move_type', 'in', ['out_invoice', 'out_refund'])]
            
            if date_from:
                domain.append(('invoice_date', '>=', date_from))
            if date_to:
                domain.append(('invoice_date', '<=', date_to))
            if payment_state:
                domain.append(('payment_state', '=', payment_state))
            
            # Obtener facturas
            invoices = self.odoo_client.search_read(
                'account.move',
                domain,
                ['partner_id', 'amount_residual'],
                limit=10000
            )
            
            # Agrupar por cliente
            by_partner = {}
            for inv in invoices:
                residual = float(inv.get('amount_residual') or 0.0)
                if residual <= 0:
                    continue
                    
                partner = inv.get('partner_id')
                partner_name = None
                if isinstance(partner, list) and len(partner) >= 2:
                    partner_name = str(partner[1])
                elif isinstance(partner, str):
                    partner_name = partner
                else:
                    partner_name = "(Sin nombre)"
                    
                by_partner[partner_name] = by_partner.get(partner_name, 0.0) + residual
            
            # Ordenar y tomar top 15
            sorted_items = sorted(by_partner.items(), key=lambda x: x[1], reverse=True)[:15]
            clientes = [name for name, _ in sorted_items]
            montos = [round(amount, 2) for _, amount in sorted_items]
            
            return {
                'clientes': clientes,
                'montos': montos
            }
            
        except Exception as e:
            print(f"Error obteniendo top 15 cobranza: {e}")
            return {'clientes': [], 'montos': []}

    def get_top15_cobranza_details(self, date_from=None, date_to=None, payment_state=None):
        """Obtener detalles del top 15 clientes"""
        try:
            # Construir dominio
            domain = [('move_type', 'in', ['out_invoice', 'out_refund'])]
            
            if date_from:
                domain.append(('invoice_date', '>=', date_from))
            if date_to:
                domain.append(('invoice_date', '<=', date_to))
            if payment_state:
                domain.append(('payment_state', '=', payment_state))
            
            # Obtener facturas con más detalles
            invoices = self.odoo_client.search_read(
                'account.move',
                domain,
                ['partner_id', 'name', 'invoice_date', 'invoice_date_due', 
                 'amount_total', 'amount_residual', 'payment_state', 'invoice_origin'],
                limit=1000
            )
            
            # Formatear datos para la tabla
            rows = []
            for inv in invoices:
                residual = float(inv.get('amount_residual') or 0.0)
                if residual <= 0:
                    continue
                    
                partner = inv.get('partner_id')
                partner_name = None
                if isinstance(partner, list) and len(partner) >= 2:
                    partner_name = str(partner[1])
                elif isinstance(partner, str):
                    partner_name = partner
                else:
                    partner_name = "(Sin nombre)"
                
                rows.append({
                    'cliente': partner_name,
                    'documento': inv.get('name', ''),
                    'fecha': inv.get('invoice_date', ''),
                    'vence': inv.get('invoice_date_due', ''),
                    'monto': float(inv.get('amount_total') or 0.0),
                    'saldo': residual,
                    'estado': inv.get('payment_state', 'not_paid'),
                    'origen': inv.get('invoice_origin', '')
                })
            
            # Ordenar por saldo descendente y tomar top 15
            rows.sort(key=lambda x: x['saldo'], reverse=True)
            rows = rows[:15]
            
            return {'rows': rows}
            
        except Exception as e:
            print(f"Error obteniendo detalles top 15: {e}")
            return {'rows': []}

    def get_cobranza_por_linea(self, date_from=None, date_to=None, payment_state=None, linea_id=None):
        """Obtener cobranza agrupada por línea comercial"""
        try:
            # Construir dominio
            domain = [('move_type', 'in', ['out_invoice', 'out_refund'])]
            
            if date_from:
                domain.append(('invoice_date', '>=', date_from))
            if date_to:
                domain.append(('invoice_date', '<=', date_to))
            if payment_state:
                domain.append(('payment_state', '=', payment_state))
            if linea_id:
                domain.append(('commercial_line_id', '=', int(linea_id)))
            
            # Obtener facturas con línea comercial
            invoices = self.odoo_client.search_read(
                'account.move',
                domain,
                ['commercial_line_id', 'amount_total', 'amount_residual', 'invoice_date_due'],
                limit=10000
            )
            
            # Agrupar por línea comercial
            by_linea = {}
            for inv in invoices:
                residual = float(inv.get('amount_residual') or 0.0)
                if residual <= 0:
                    continue
                    
                linea = inv.get('commercial_line_id')
                linea_name = None
                if isinstance(linea, list) and len(linea) >= 2:
                    linea_name = str(linea[1])
                elif isinstance(linea, str):
                    linea_name = linea
                else:
                    linea_name = "Sin Línea"
                
                if linea_name not in by_linea:
                    by_linea[linea_name] = {
                        'facturas_total': 0,
                        'monto_vigente': 0.0,
                        'monto_vencido': 0.0,
                        'total_por_cobrar': 0.0
                    }
                
                by_linea[linea_name]['facturas_total'] += 1
                by_linea[linea_name]['total_por_cobrar'] += residual
                
                # Clasificar como vigente o vencido
                due_date = inv.get('invoice_date_due')
                if due_date:
                    try:
                        from datetime import date
                        today = date.today()
                        due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                        if due_date_obj < today:
                            by_linea[linea_name]['monto_vencido'] += residual
                        else:
                            by_linea[linea_name]['monto_vigente'] += residual
                    except:
                        by_linea[linea_name]['monto_vigente'] += residual
                else:
                    by_linea[linea_name]['monto_vigente'] += residual
            
            # Convertir a lista para la tabla
            rows = []
            for linea_name, data in by_linea.items():
                rows.append({
                    'linea_comercial': linea_name,
                    'facturas_total': data['facturas_total'],
                    'monto_vigente': round(data['monto_vigente'], 2),
                    'monto_vencido': round(data['monto_vencido'], 2),
                    'total_por_cobrar': round(data['total_por_cobrar'], 2)
                })
            
            # Ordenar por total por cobrar descendente
            rows.sort(key=lambda x: x['total_por_cobrar'], reverse=True)
            
            return {'rows': rows}
            
        except Exception as e:
            print(f"Error obteniendo cobranza por línea: {e}")
            return {'rows': []}