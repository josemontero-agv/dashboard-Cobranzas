# -*- coding: utf-8 -*-
"""
Utilidades de la aplicación Dashboard Cobranzas.

Este paquete contiene funciones auxiliares:
- calculators: Cálculos financieros (mora, DSO, CEI, aging)
- filters: Filtros de datos (Nacional/Internacional)
"""

from .calculators import (
    calcular_mora,
    calcular_dso,
    calcular_cei,
    calcular_dias_vencido,
    clasificar_antiguedad
)
from .filters import filter_internacional, filter_nacional

__all__ = [
    'calcular_mora',
    'calcular_dso',
    'calcular_cei',
    'calcular_dias_vencido',
    'clasificar_antiguedad',
    'filter_internacional',
    'filter_nacional'
]

