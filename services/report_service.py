# -*- coding: utf-8 -*-
"""
Servicio de Reportes CxC (Cuentas por Cobrar).

Genera reportes de cuentas por cobrar nacional e internacional.
"""

from datetime import datetime
from utils.calculators import calcular_mora, calcular_dias_vencido, clasificar_antiguedad
from utils.filters import filter_internacional


class ReportService:
    """
    Servicio para generar reportes de cuentas por cobrar.
    """
    
    def __init__(self, connection):
        """
        Inicializa el servicio de reportes.
        
        Args:
            connection (OdooConnection): Instancia de conexión a Odoo
        """
        self.connection = connection
    
    def get_report_lines(self, start_date=None, end_date=None, customer=None, limit=0, account_codes=None, search_term=None):
        """
        Obtener líneas de reporte de CxC siguiendo la cadena de relaciones.
        
        Args:
            start_date (str): Fecha inicial
            end_date (str): Fecha final
            customer (str): Nombre de cliente a filtrar
            limit (int): Límite de registros
            account_codes (str): Códigos de cuenta separados por coma
            search_term (str): Término de búsqueda general
        
        Returns:
            list: Líneas de reporte CxC
        """
        try:
            print("[INFO] Obteniendo lineas de reporte CxC...")
            
            if not self.connection.is_connected():
                print("[ERROR] No hay conexion a Odoo disponible")
                return []
            
            # Códigos de cuenta a buscar
            if account_codes:
                codes = [c.strip() for c in account_codes.split(',') if c.strip()]
            else:
                codes = ['12']  # Cuenta 12 por defecto
            
            # Construir dominio base
            line_domain = [
                ('parent_state', '=', 'posted'),
                ('reconciled', '=', True),
            ]
            
            # Construir OR para códigos de cuenta
            if len(codes) > 1:
                or_operators = ['|'] * (len(codes) - 1)
                code_conditions = []
                for code in codes:
                    code_conditions.append(('account_id.code', '=like', f'{code}%'))
                line_domain = or_operators + code_conditions + line_domain
            else:
                line_domain.insert(0, ('account_id.code', '=like', f'{codes[0]}%'))
            
            # Filtros adicionales
            if start_date:
                line_domain.append(('date', '>=', start_date))
            if end_date:
                line_domain.append(('date', '<=', end_date))
            if customer:
                line_domain.append(('partner_id.name', 'ilike', customer))
            if search_term:
                # Búsqueda general en múltiples campos
                line_domain.append('|')
                line_domain.append('|')
                line_domain.append(('name', 'ilike', search_term))
                line_domain.append(('partner_id.name', 'ilike', search_term))
                line_domain.append(('move_id.name', 'ilike', search_term))
            
            # Campos a extraer
            line_fields = [
                'id', 'move_id', 'partner_id', 'account_id', 'name', 'date',
                'date_maturity', 'amount_currency', 'amount_residual', 'currency_id',
            ]
            
            lines = self.connection.search_read(
                'account.move.line', line_domain, line_fields,
                limit=limit if limit > 0 else 10000
            )
            
            print(f"[OK] Obtenidas {len(lines)} lineas de asiento contable")
            
            if not lines:
                return []
            
            # Extraer IDs únicos
            move_ids = list(set([l['move_id'][0] for l in lines if l.get('move_id')]))
            partner_ids = list(set([l['partner_id'][0] for l in lines if l.get('partner_id')]))
            account_ids = list(set([l['account_id'][0] for l in lines if l.get('account_id')]))
            
            # Obtener datos de facturas
            move_map = {}
            if move_ids:
                move_fields = [
                    'id', 'name', 'payment_state', 'invoice_date', 'invoice_date_due',
                    'invoice_origin', 'l10n_latam_document_type_id', 'amount_total',
                    'amount_residual', 'currency_id', 'ref', 'invoice_payment_term_id',
                    'invoice_user_id', 'sales_channel_id', 'sale_type_id',
                ]
                moves = self.connection.read('account.move', move_ids, move_fields)
                move_map = {m['id']: m for m in moves}
            
            # Obtener datos de clientes
            partner_map = {}
            if partner_ids:
                partner_fields = [
                    'id', 'name', 'vat', 'state_id', 'l10n_pe_district',
                    'country_code', 'country_id',
                ]
                partners = self.connection.read('res.partner', partner_ids, partner_fields)
                partner_map = {p['id']: p for p in partners}
            
            # Obtener datos de cuentas
            account_map = {}
            if account_ids:
                accounts = self.connection.read('account.account', account_ids, ['id', 'code', 'name'])
                account_map = {a['id']: a for a in accounts}
            
            # Obtener información de crédito
            credit_map = {}
            if partner_ids:
                try:
                    credit_customers = self.connection.search_read(
                        'agr.credit.customer',
                        [('partner_id', 'in', partner_ids)],
                        ['partner_id', 'sub_channel_id']
                    )
                    credit_map = {cc['partner_id'][0]: cc for cc in credit_customers}
                except Exception as e:
                    print(f"[WARN] No se pudo obtener agr.credit.customer: {e}")
            
            # Combinar datos
            rows = []
            def m2o_name(val):
                if isinstance(val, list) and len(val) >= 2:
                    return val[1]
                return ''
            
            for line in lines:
                move_id = line['move_id'][0] if line.get('move_id') else None
                partner_id = line['partner_id'][0] if line.get('partner_id') else None
                account_id = line['account_id'][0] if line.get('account_id') else None
                
                move = move_map.get(move_id, {})
                partner = partner_map.get(partner_id, {})
                account = account_map.get(account_id, {})
                credit = credit_map.get(partner_id, {})
                
                # Determinar Sub Canal
                sub_channel_raw = m2o_name(credit.get('sub_channel_id'))
                country_code = partner.get('country_code', '')
                
                if not sub_channel_raw or sub_channel_raw == 'N/A' or sub_channel_raw.strip() == '':
                    if country_code == 'PE':
                        sub_channel_final = 'NACIONAL'
                    elif country_code and country_code != '':
                        sub_channel_final = 'INTERNACIONAL'
                    else:
                        sub_channel_final = 'N/A'
                else:
                    sub_channel_final = sub_channel_raw
                
                row = {
                    'payment_state': move.get('payment_state', ''),
                    'invoice_date': move.get('invoice_date', ''),
                    'I10nn_latam_document_type_id': m2o_name(move.get('l10n_latam_document_type_id')),
                    'move_name': move.get('name', ''),
                    'invoice_origin': move.get('invoice_origin', ''),
                    'account_id/code': account.get('code', ''),
                    'account_id/name': account.get('name', ''),
                    'patner_id/vat': partner.get('vat', ''),
                    'patner_id': partner.get('name', ''),
                    'patner_id/state_id': m2o_name(partner.get('state_id')),
                    'patner_id/l10n_pe_district': partner.get('l10n_pe_district', ''),
                    'patner_id/country_code': country_code,
                    'patner_id/country_id': m2o_name(partner.get('country_id')),
                    'currency_id': m2o_name(line.get('currency_id') or move.get('currency_id')),
                    'amount_total': move.get('amount_total', 0.0),
                    'amount_residual': move.get('amount_residual', 0.0),
                    'amount_currency': line.get('amount_currency', 0.0),
                    'amount_residual_currency': line.get('amount_residual', 0.0),
                    'date': line.get('date', ''),
                    'date_maturity': line.get('date_maturity', ''),
                    'invoice_date_due': move.get('invoice_date_due', ''),
                    'ref': move.get('ref', ''),
                    'invoice_payment_term_id': m2o_name(move.get('invoice_payment_term_id')),
                    'name': line.get('name', ''),
                    'move_id/invoice_user_id': m2o_name(move.get('invoice_user_id')),
                    'move_id/sales_channel_id': m2o_name(move.get('sales_channel_id')),
                    'move_id/sales_type_id': m2o_name(move.get('sale_type_id')),
                    'move_id/payment_state': move.get('payment_state', ''),
                    'sub_channel_id': sub_channel_final,
                }
                
                rows.append(row)
            
            print(f"[OK] Procesadas {len(rows)} lineas de CxC con TODOS los campos")
            return rows
            
        except Exception as e:
            print(f"[ERROR] Error al obtener las lineas de reporte CxC: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_report_internacional(self, start_date=None, end_date=None, customer=None, payment_state=None, limit=0):
        """
        Obtener reporte de facturas internacionales no pagadas con campos calculados.
        
        Args:
            start_date (str): Fecha inicial
            end_date (str): Fecha final
            customer (str): Nombre de cliente
            payment_state (str): Estado de pago
            limit (int): Límite de registros
        
        Returns:
            list: Líneas de reporte internacional con campos calculados
        """
        try:
            print("[INFO] Obteniendo reporte internacional...")
            
            if not self.connection.is_connected():
                print("[ERROR] No hay conexion a Odoo disponible")
                return []
            
            # Construir dominio
            line_domain = [
                ('parent_state', '=', 'posted'),
                ('reconciled', '=', False),  # Solo no pagadas
                ('account_id.code', '=like', '12%'),
            ]
            
            if start_date:
                line_domain.append(('date', '>=', start_date))
            if end_date:
                line_domain.append(('date', '<=', end_date))
            if customer:
                line_domain.append(('partner_id.name', 'ilike', customer))
            
            # Campos a extraer (incluir amount_residual_with_retention)
            line_fields = [
                'id', 'move_id', 'partner_id', 'account_id', 'name', 'date',
                'date_maturity', 'amount_currency', 'amount_residual', 'currency_id',
            ]
            
            lines = self.connection.search_read(
                'account.move.line', line_domain, line_fields,
                limit=limit if limit > 0 else 10000
            )
            
            if not lines:
                return []
            
            # Extraer IDs únicos
            move_ids = list(set([l['move_id'][0] for l in lines if l.get('move_id')]))
            partner_ids = list(set([l['partner_id'][0] for l in lines if l.get('partner_id')]))
            
            # Obtener facturas
            move_map = {}
            if move_ids:
                move_fields = [
                    'id', 'name', 'payment_state', 'invoice_date', 'invoice_date_due',
                    'invoice_origin', 'l10n_latam_document_type_id', 'amount_total',
                    'amount_residual', 'currency_id', 'invoice_payment_term_id',
                    'invoice_user_id', 'amount_total_signed',
                ]
                moves = self.connection.read('account.move', move_ids, move_fields)
                move_map = {m['id']: m for m in moves}
                
                # Filtrar por payment_state si se especificó
                if payment_state:
                    move_map = {k: v for k, v in move_map.items() if v.get('payment_state') == payment_state}
            
            # Obtener clientes
            partner_map = {}
            if partner_ids:
                partner_fields = ['id', 'name', 'vat', 'country_code', 'country_id']
                partners = self.connection.read('res.partner', partner_ids, partner_fields)
                partner_map = {p['id']: p for p in partners}
            
            # Procesar y calcular campos
            rows = []
            today = datetime.today().date()
            
            def m2o_name(val):
                if isinstance(val, list) and len(val) >= 2:
                    return val[1]
                return ''
            
            for line in lines:
                move_id = line['move_id'][0] if line.get('move_id') else None
                partner_id = line['partner_id'][0] if line.get('partner_id') else None
                
                move = move_map.get(move_id, {})
                partner = partner_map.get(partner_id, {})
                
                # Crear estructura de línea temporal para filtro
                temp_line = {
                    'country_code': partner.get('country_code'),
                    'patner_id/country_code': partner.get('country_code'),
                }
                
                # Filtrar solo internacional
                internacional_lines = filter_internacional([temp_line])
                if not internacional_lines:
                    continue
                
                # Calcular campos
                invoice_date_due = move.get('invoice_date_due', '')
                amount_residual = move.get('amount_residual', 0.0)
                
                # Días de vencido
                dias_vencido = calcular_dias_vencido(invoice_date_due, today) if invoice_date_due else 0
                
                # Monto de interés (12% anual, gracia 8 días)
                monto_interes = calcular_mora(dias_vencido, 0.12, amount_residual)
                
                # Estado de deuda
                estado_deuda = 'VENCIDO' if dias_vencido > 0 else 'VIGENTE'
                
                # Antigüedad
                antiguedad = clasificar_antiguedad(max(0, dias_vencido))
                
                row = {
                    'payment_state': move.get('payment_state', ''),
                    'vat': partner.get('vat', ''),
                    'patner_id': partner.get('name', ''),
                    'I10nn_latam_document_type_id': m2o_name(move.get('l10n_latam_document_type_id')),
                    'name': move.get('name', ''),
                    'invoice_origin': move.get('invoice_origin', ''),
                    'invoice_payment_term_id': m2o_name(move.get('invoice_payment_term_id')),
                    'invoice_date': move.get('invoice_date', ''),
                    'invoice_date_due': invoice_date_due,
                    'currency_id': m2o_name(move.get('currency_id')),
                    'amount_total_currency_signed': move.get('amount_total_signed', move.get('amount_total', 0.0)),
                    'amount_residual_with_retention': amount_residual,
                    'monto_interes': monto_interes,
                    'dias_vencido': dias_vencido,
                    'estado_deuda': estado_deuda,
                    'antiguedad': antiguedad,
                    'invoice_user_id': m2o_name(move.get('invoice_user_id')),
                    'country_code': partner.get('country_code', ''),
                    'country_id': m2o_name(partner.get('country_id')),
                }
                
                rows.append(row)
            
            print(f"[OK] Procesadas {len(rows)} lineas internacionales")
            return rows
            
        except Exception as e:
            print(f"[ERROR] Error al obtener reporte internacional: {e}")
            import traceback
            traceback.print_exc()
            return []

