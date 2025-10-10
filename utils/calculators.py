# -*- coding: utf-8 -*-
"""
Calculadoras financieras para cobranzas.

Contiene funciones para calcular métricas de cobranza:
- Interés moratorio
- DSO (Days Sales Outstanding)
- CEI (Collection Effectiveness Index)
- Días de vencimiento
- Clasificación de antigüedad de deuda
"""

from datetime import datetime, date


def calcular_mora(dias_retraso, tasa_anual, monto_adeudado):
    """
    Calcula el interés moratorio basado en días de retraso.
    
    La mora solo se calcula si el retraso excede 8 días (período de gracia).
    Tasa diaria = (1 + tasa_anual)^(1/360) - 1
    
    Args:
        dias_retraso (int): Días transcurridos desde el vencimiento
        tasa_anual (float): Tasa anual (ejemplo: 0.12 para 12%)
        monto_adeudado (float): Monto base para calcular interés
    
    Returns:
        float: Monto de interés moratorio calculado
    """
    if dias_retraso <= 8 or monto_adeudado <= 0:
        return 0.0
    
    # Calcular días efectivos (excluyendo período de gracia)
    dias_efectivos = dias_retraso - 8
    
    # Convertir tasa anual a tasa diaria: (1 + tasa_anual)^(1/360) - 1
    tasa_diaria = pow(1 + tasa_anual, 1/360) - 1
    
    # Calcular interés = dias_efectivos * tasa_diaria * monto_adeudado
    interes = dias_efectivos * tasa_diaria * monto_adeudado
    
    return round(interes, 2)


def calcular_dso(cuentas_por_cobrar, ventas_credito, dias_periodo):
    """
    Calcula Days Sales Outstanding (DSO).
    
    DSO = (Cuentas por Cobrar / Ventas a Crédito) * Días del Período
    Mide el tiempo promedio que toma cobrar las ventas a crédito.
    
    Args:
        cuentas_por_cobrar (float): Saldo de cuentas por cobrar
        ventas_credito (float): Total de ventas a crédito en el período
        dias_periodo (int): Número de días del período analizado
    
    Returns:
        float: DSO en días
    """
    if ventas_credito == 0:
        return 0.0
    
    dso = (cuentas_por_cobrar / ventas_credito) * dias_periodo
    return round(dso, 1)


def calcular_cei(cobrado_periodo, cobrable_periodo, saldo_inicial):
    """
    Calcula Collection Effectiveness Index (CEI).
    
    CEI = (Cobrado en el Período / (Saldo Inicial + Ventas del Período)) * 100
    Mide la efectividad del equipo de cobranza (0-100%).
    
    Args:
        cobrado_periodo (float): Monto cobrado en el período
        cobrable_periodo (float): Total cobrable (saldo inicial + ventas nuevas)
        saldo_inicial (float): Saldo de cuentas por cobrar al inicio
    
    Returns:
        float: CEI en porcentaje (0-100)
    """
    if cobrable_periodo == 0:
        return 0.0
    
    cei = (cobrado_periodo / cobrable_periodo) * 100
    return round(min(cei, 100.0), 1)  # No puede exceder 100%


def calcular_dias_vencido(fecha_vencimiento, fecha_actual=None):
    """
    Calcula los días de vencimiento (positivo) o vigencia (negativo).
    
    Args:
        fecha_vencimiento (str, date, datetime): Fecha de vencimiento
        fecha_actual (date, datetime, optional): Fecha de referencia. Por defecto hoy.
    
    Returns:
        int: Días vencidos (positivo) o días hasta vencer (negativo)
    """
    if fecha_actual is None:
        fecha_actual = date.today()
    
    # Convertir fecha_actual a date si es datetime
    if isinstance(fecha_actual, datetime):
        fecha_actual = fecha_actual.date()
    
    # Convertir fecha_vencimiento según su tipo
    if isinstance(fecha_vencimiento, str):
        try:
            fecha_venc = datetime.strptime(fecha_vencimiento, '%Y-%m-%d').date()
        except ValueError:
            return 0
    elif isinstance(fecha_vencimiento, datetime):
        fecha_venc = fecha_vencimiento.date()
    elif isinstance(fecha_vencimiento, date):
        fecha_venc = fecha_vencimiento
    else:
        return 0
    
    # Calcular diferencia: positivo = vencido, negativo = vigente
    dias_diferencia = (fecha_actual - fecha_venc).days
    
    return dias_diferencia


def clasificar_antiguedad(dias_vencido):
    """
    Clasifica la antigüedad de la deuda según días de vencimiento.
    
    Rangos:
    - Vigente: 0 días o menos (no vencido)
    - Atraso Corto: 1-30 días
    - Atraso Medio: 31-60 días
    - Atraso Prolongado: 61-90 días
    - Cobranza Judicial: +90 días
    
    Args:
        dias_vencido (int): Días de vencimiento (resultado de calcular_dias_vencido)
    
    Returns:
        str: Clasificación de antigüedad
    """
    dias = max(0, dias_vencido)  # Asegurar que sea no negativo
    
    if dias == 0:
        return "Vigente"
    elif dias <= 30:
        return "Atraso Corto (1-30)"
    elif dias <= 60:
        return "Atraso Medio (31-60)"
    elif dias <= 90:
        return "Atraso Prolongado (61-90)"
    else:
        return "Cobranza Judicial (+90)"


def get_aging_bucket_key(dias_vencido):
    """
    Obtiene la clave del bucket de aging para agrupación.
    
    Args:
        dias_vencido (int): Días de vencimiento
    
    Returns:
        str: Clave del bucket ('vigente', '1-30', '31-60', '61-90', '+90')
    """
    dias = max(0, dias_vencido)
    
    if dias == 0:
        return "vigente"
    elif dias <= 30:
        return "1-30"
    elif dias <= 60:
        return "31-60"
    elif dias <= 90:
        return "61-90"
    else:
        return "+90"

