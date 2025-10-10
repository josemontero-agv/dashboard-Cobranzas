# -*- coding: utf-8 -*-
"""
Servicio de Cobranza Internacional.

Maneja KPIs y métricas de cobranza internacional.
"""

from datetime import datetime, date
from utils.calculators import calcular_dso, calcular_cei, calcular_dias_vencido, get_aging_bucket_key
from utils.filters import filter_internacional


class CobranzaService:
    """
    Servicio para métricas de cobranza internacional.
    """
    
    def __init__(self, connection):
        """
        Args:
            connection (OdooConnection): Conexión a Odoo
        """
        self.connection = connection
    
    def get_cobranza_kpis_internacional(self, date_from=None, date_to=None, payment_state=None, linea_id=None):
        """
        Obtener KPIs de cobranza internacional.
        
        Returns:
            dict: KPIs calculados
        """
        try:
            if not self.connection.is_connected():
                return self._get_empty_kpis()
            
            # Construir dominio
            domain = [('move_type', 'in', ['out_invoice', 'out_refund']), ('state', '=', 'posted')]
            
            if date_from:
                domain.append(('invoice_date', '>=', date_from))
            if date_to:
                domain.append(('invoice_date', '<=', date_to))
            if payment_state:
                domain.append(('payment_state', '=', payment_state))
            
            # Obtener facturas
            fields = [
                'id', 'name', 'partner_id', 'invoice_date', 'invoice_date_due',
                'amount_total', 'amount_residual', 'payment_state', 'currency_id',
                'team_id', 'invoice_user_id', 'country_code'
            ]
            
            invoices = self.connection.search_read('account.move', domain, fields, limit=10000)
            
            # Aplicar filtro internacional
            invoices_data = []
            for inv in invoices:
                temp_line = {
                    'country_code': inv.get('country_code'),
                    'sales_channel_id': inv.get('team_id'),
                }
                if filter_internacional([temp_line]):
                    invoices_data.append(inv)
            
            # Calcular KPIs
            today = date.today()
            total_facturas = len(invoices_data)
            monto_vencido = 0.0
            monto_vigente = 0.0
            total_overdue_days = 0
            overdue_count = 0
            
            # Aging buckets
            aging_buckets = {
                'vigente': 0.0,
                '1-30': 0.0,
                '31-60': 0.0,
                '61-90': 0.0,
                '+90': 0.0
            }
            
            # DSO por país
            dso_by_country = {}
            country_data = {}
            
            for inv in invoices_data:
                residual = float(inv.get('amount_residual') or 0.0)
                due_date = inv.get('invoice_date_due')
                amount_total = float(inv.get('amount_total') or 0.0)
                country_code = inv.get('country_code', 'N/A')
                
                # Acumular por país
                if country_code not in country_data:
                    country_data[country_code] = {'cxc': 0.0, 'ventas': 0.0}
                country_data[country_code]['cxc'] += residual
                country_data[country_code]['ventas'] += amount_total
                
                if residual <= 0:
                    continue
                
                # Calcular días vencido
                dias_vencido = calcular_dias_vencido(due_date, today) if due_date else 0
                
                if dias_vencido > 0:
                    monto_vencido += residual
                    total_overdue_days += dias_vencido
                    overdue_count += 1
                else:
                    monto_vigente += residual
                
                # Aging bucket
                bucket_key = get_aging_bucket_key(dias_vencido)
                aging_buckets[bucket_key] += residual
            
            # Calcular DSO promedio y por país
            dias_periodo = (datetime.strptime(date_to, '%Y-%m-%d') - datetime.strptime(date_from, '%Y-%m-%d')).days if date_from and date_to else 30
            
            total_cxc = sum(d['cxc'] for d in country_data.values())
            total_ventas = sum(d['ventas'] for d in country_data.values())
            dso_promedio = calcular_dso(total_cxc, total_ventas, dias_periodo)
            
            for country, data in country_data.items():
                dso_by_country[country] = calcular_dso(data['cxc'], data['ventas'], dias_periodo)
            
            promedio_dias_morosidad = (total_overdue_days / overdue_count) if overdue_count > 0 else 0.0
            
            # CEI simplificado (necesitaría más datos para cálculo completo)
            cei = 80.0  # Placeholder
            
            porcentaje_vencido = (monto_vencido / (monto_vencido + monto_vigente) * 100) if (monto_vencido + monto_vigente) > 0 else 0.0
            
            return {
                'dso_promedio': dso_promedio,
                'dso_by_country': dso_by_country,
                'cei': cei,
                'porcentaje_vencido': round(porcentaje_vencido, 1),
                'monto_vencido': round(monto_vencido, 2),
                'monto_vigente': round(monto_vigente, 2),
                'total_facturas': total_facturas,
                'promedio_dias_morosidad': round(promedio_dias_morosidad, 1),
                'aging_buckets': aging_buckets,
                'tasa_recuperacion': 75.0,  # Placeholder
                'plazo_promedio_cobranza': 45.0,  # Placeholder
            }
            
        except Exception as e:
            print(f"[ERROR] Error calculando KPIs internacionales: {e}")
            import traceback
            traceback.print_exc()
            return self._get_empty_kpis()
    
    def _get_empty_kpis(self):
        """KPIs vacíos."""
        return {
            'dso_promedio': 0.0,
            'dso_by_country': {},
            'cei': 0.0,
            'porcentaje_vencido': 0.0,
            'monto_vencido': 0.0,
            'monto_vigente': 0.0,
            'total_facturas': 0,
            'promedio_dias_morosidad': 0.0,
            'aging_buckets': {'vigente': 0.0, '1-30': 0.0, '31-60': 0.0, '61-90': 0.0, '+90': 0.0},
            'tasa_recuperacion': 0.0,
            'plazo_promedio_cobranza': 0.0,
        }
    
    def get_top15_deudores_internacional(self, date_from=None, date_to=None):
        """
        Obtener top 15 clientes con mayor deuda vencida internacional.
        
        Returns:
            dict: {'clientes': [], 'montos': [], 'detalles': []}
        """
        try:
            if not self.connection.is_connected():
                return {'clientes': [], 'montos': [], 'detalles': []}
            
            domain = [
                ('move_type', 'in', ['out_invoice', 'out_refund']),
                ('state', '=', 'posted'),
                ('amount_residual', '>', 0)
            ]
            
            if date_from:
                domain.append(('invoice_date', '>=', date_from))
            if date_to:
                domain.append(('invoice_date', '<=', date_to))
            
            fields = [
                'partner_id', 'amount_residual', 'invoice_date_due', 'country_code'
            ]
            
            invoices = self.connection.search_read('account.move', domain, fields, limit=5000)
            
            # Filtrar internacional
            internacional_inv = []
            for inv in invoices:
                temp = {'country_code': inv.get('country_code')}
                if filter_internacional([temp]):
                    internacional_inv.append(inv)
            
            # Agrupar por cliente
            by_partner = {}
            for inv in internacional_inv:
                partner = inv.get('partner_id')
                if not partner:
                    continue
                
                partner_name = partner[1] if isinstance(partner, list) and len(partner) >= 2 else str(partner)
                residual = float(inv.get('amount_residual') or 0.0)
                
                if partner_name not in by_partner:
                    by_partner[partner_name] = 0.0
                by_partner[partner_name] += residual
            
            # Top 15
            sorted_items = sorted(by_partner.items(), key=lambda x: x[1], reverse=True)[:15]
            clientes = [name for name, _ in sorted_items]
            montos = [round(amount, 2) for _, amount in sorted_items]
            
            return {
                'clientes': clientes,
                'montos': montos,
                'detalles': []
            }
            
        except Exception as e:
            print(f"[ERROR] Error obteniendo top15: {e}")
            return {'clientes': [], 'montos': [], 'detalles': []}

