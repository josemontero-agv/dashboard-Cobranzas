# -*- coding: utf-8 -*-
"""
Filtros de datos para separar cobranza Nacional e Internacional.

Funciones para filtrar líneas de venta y cobranza según canal de venta
y línea comercial.
"""


def filter_internacional(sales_lines):
    """
    Filtra líneas que corresponden a VENTA INTERNACIONAL.
    
    Incluye líneas donde:
    - La línea comercial contiene "VENTA INTERNACIONAL" o "INTERNACIONAL"
    - El canal de venta contiene "INTERNACIONAL"
    
    Args:
        sales_lines (list): Lista de líneas de venta/cobranza
    
    Returns:
        list: Líneas filtradas que son internacionales
    """
    internacional_lines = []
    
    for line in sales_lines:
        is_internacional = False
        
        # Verificar línea comercial
        linea_comercial = line.get('commercial_line_national_id')
        if linea_comercial and isinstance(linea_comercial, list) and len(linea_comercial) > 1:
            nombre_linea = str(linea_comercial[1]).upper()
            if 'VENTA INTERNACIONAL' in nombre_linea or 'INTERNACIONAL' in nombre_linea:
                is_internacional = True
        
        # Verificar canal de ventas
        canal_ventas = line.get('sales_channel_id')
        if canal_ventas and isinstance(canal_ventas, list) and len(canal_ventas) > 1:
            nombre_canal = str(canal_ventas[1]).upper()
            if 'VENTA INTERNACIONAL' in nombre_canal or 'INTERNACIONAL' in nombre_canal:
                is_internacional = True
        
        # Verificar país (si no es PE, es internacional)
        country_code = line.get('country_code') or line.get('patner_id/country_code')
        if country_code and country_code != 'PE':
            is_internacional = True
        
        if is_internacional:
            internacional_lines.append(line)
    
    return internacional_lines


def filter_nacional(sales_lines):
    """
    Filtra líneas que corresponden a VENTA NACIONAL (Perú).
    
    Excluye líneas donde:
    - La línea comercial contiene "VENTA INTERNACIONAL" o "INTERNACIONAL"
    - El canal de venta contiene "INTERNACIONAL"
    
    Args:
        sales_lines (list): Lista de líneas de venta/cobranza
    
    Returns:
        list: Líneas filtradas que son nacionales
    """
    nacional_lines = []
    
    for line in sales_lines:
        is_internacional = False
        
        # Verificar línea comercial
        linea_comercial = line.get('commercial_line_national_id')
        if linea_comercial and isinstance(linea_comercial, list) and len(linea_comercial) > 1:
            nombre_linea = str(linea_comercial[1]).upper()
            if 'VENTA INTERNACIONAL' in nombre_linea or 'INTERNACIONAL' in nombre_linea:
                is_internacional = True
        
        # Verificar canal de ventas
        canal_ventas = line.get('sales_channel_id')
        if canal_ventas and isinstance(canal_ventas, list) and len(canal_ventas) > 1:
            nombre_canal = str(canal_ventas[1]).upper()
            if 'VENTA INTERNACIONAL' in nombre_canal or 'INTERNACIONAL' in nombre_canal:
                is_internacional = True
        
        # Si no es internacional, es nacional
        if not is_internacional:
            nacional_lines.append(line)
    
    return nacional_lines


def is_internacional_line(line):
    """
    Verifica si una línea individual es internacional.
    
    Args:
        line (dict): Línea de venta/cobranza
    
    Returns:
        bool: True si es internacional, False si es nacional
    """
    # Verificar línea comercial
    linea_comercial = line.get('commercial_line_national_id')
    if linea_comercial and isinstance(linea_comercial, list) and len(linea_comercial) > 1:
        nombre_linea = str(linea_comercial[1]).upper()
        if 'VENTA INTERNACIONAL' in nombre_linea or 'INTERNACIONAL' in nombre_linea:
            return True
    
    # Verificar canal de ventas
    canal_ventas = line.get('sales_channel_id')
    if canal_ventas and isinstance(canal_ventas, list) and len(canal_ventas) > 1:
        nombre_canal = str(canal_ventas[1]).upper()
        if 'VENTA INTERNACIONAL' in nombre_canal or 'INTERNACIONAL' in nombre_canal:
            return True
    
    # Verificar país
    country_code = line.get('country_code') or line.get('patner_id/country_code')
    if country_code and country_code != 'PE':
        return True
    
    return False

