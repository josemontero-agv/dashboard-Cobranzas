# -*- coding: utf-8 -*-
"""
Servicios de la aplicación Dashboard Cobranzas.

Este paquete contiene los servicios para interactuar con Odoo:
- odoo_connection: Conexión base XML-RPC
- sales_service: Lógica de ventas
- cobranza_service: Lógica de cobranza internacional
- report_service: Generación de reportes CxC
"""

from .odoo_connection import OdooConnection
from .sales_service import SalesService
from .cobranza_service import CobranzaService
from .report_service import ReportService

__all__ = ['OdooConnection', 'SalesService', 'CobranzaService', 'ReportService']

