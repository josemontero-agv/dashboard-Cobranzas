# -*- coding: utf-8 -*-
"""
Servicio de conexión a Odoo.

Maneja la conexión XML-RPC y autenticación con Odoo.
"""

import xmlrpc.client
import os


class OdooConnection:
    """
    Conexión base a Odoo usando XML-RPC.
    
    Lee credenciales del archivo .env y establece conexión.
    """
    
    def __init__(self):
        """Inicializa la conexión a Odoo."""
        try:
            # Leer credenciales del archivo .env
            self.url = os.getenv('ODOO_URL')
            self.db = os.getenv('ODOO_DB')
            self.username = os.getenv('ODOO_USER')
            self.password = os.getenv('ODOO_PASSWORD')
            
            # Validar que todas las credenciales estén configuradas
            if not all([self.url, self.db, self.username, self.password]):
                raise ValueError("Faltan credenciales de Odoo en el archivo .env")
            
            # Establecer conexión
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.uid = common.authenticate(self.db, self.username, self.password, {})
            
            if self.uid:
                self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
                print("[OK] Conexion a Odoo establecida exitosamente.")
            else:
                print("[ERROR] No se pudo autenticar. Continuando en modo offline.")
                self.uid = None
                self.models = None
                
        except Exception as e:
            print(f"[ERROR] Error en la conexion a Odoo: {e}")
            print("[INFO] Continuando en modo offline.")
            self.uid = None
            self.models = None
    
    def authenticate_user(self, username, password):
        """
        Autentica un usuario contra Odoo.
        
        Args:
            username (str): Nombre de usuario
            password (str): Contraseña
        
        Returns:
            bool: True si la autenticación fue exitosa
        """
        try:
            # Crear conexión temporal para autenticación
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            
            # Intentar autenticar con las credenciales proporcionadas
            uid = common.authenticate(self.db, username, password, {})
            
            if uid:
                print(f"[OK] Autenticacion exitosa para usuario: {username}")
                return True
            else:
                print(f"[ERROR] Credenciales incorrectas para usuario: {username}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error en autenticacion contra Odoo: {e}")
            
            # Fallback: verificar si las credenciales coinciden con las del .env
            try:
                if username == self.username and password == self.password:
                    print(f"[OK] Autenticacion exitosa usando credenciales del .env")
                    return True
                else:
                    print(f"[ERROR] Credenciales no coinciden con las configuradas")
                    return False
            except Exception as fallback_error:
                print(f"[ERROR] Error en fallback de autenticacion: {fallback_error}")
                return False
    
    def execute_kw(self, model, method, args, kwargs=None):
        """
        Wrapper genérico para llamadas execute_kw a Odoo.
        
        Args:
            model (str): Modelo de Odoo (ej: 'account.move')
            method (str): Método a ejecutar (ej: 'search_read')
            args (list): Argumentos posicionales
            kwargs (dict, optional): Argumentos con nombre
        
        Returns:
            Result from Odoo or None if connection failed
        """
        if not self.uid or not self.models:
            print("[WARN] No hay conexion a Odoo disponible")
            return None
        
        if kwargs is None:
            kwargs = {}
        
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, method, args, kwargs
            )
        except Exception as e:
            print(f"[ERROR] Error ejecutando {model}.{method}: {e}")
            return None
    
    def search_read(self, model, domain, fields, limit=None, offset=None, order=None):
        """
        Método conveniente para search_read.
        
        Args:
            model (str): Modelo de Odoo
            domain (list): Dominio de búsqueda
            fields (list): Campos a obtener
            limit (int, optional): Límite de registros
            offset (int, optional): Offset para paginación
            order (str, optional): Campo de ordenamiento
        
        Returns:
            list: Registros encontrados
        """
        options = {'fields': fields}
        if limit:
            options['limit'] = limit
        if offset:
            options['offset'] = offset
        if order:
            options['order'] = order
        
        return self.execute_kw(model, 'search_read', [domain], options) or []
    
    def read(self, model, ids, fields):
        """
        Método conveniente para read.
        
        Args:
            model (str): Modelo de Odoo
            ids (list): IDs de registros a leer
            fields (list): Campos a obtener
        
        Returns:
            list: Registros leídos
        """
        return self.execute_kw(model, 'read', [ids], {'fields': fields}) or []
    
    def is_connected(self):
        """
        Verifica si hay conexión activa a Odoo.
        
        Returns:
            bool: True si está conectado
        """
        return bool(self.uid and self.models)

