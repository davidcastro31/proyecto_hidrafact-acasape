import mysql.connector
from mysql.connector import Error

class crud:
    def __init__(self):
        print("Conectando a la base de datos...")
        try:
            self.conexion = mysql.connector.connect(
                host='localhost',
                user='root',
                password='',
                database='db_hidrofact'
            )
            if self.conexion.is_connected():
                print("Conexión exitosa a la base de datos db_hidrofact")
            else:
                print("Error: No se pudo conectar a la base de datos")
        except Error as e:
            print(f"Error de conexión: {e}")
            self.conexion = None
    
    def consultar(self, sql):
        """Ejecuta una consulta SELECT y devuelve resultados"""
        try:
            cursor = self.conexion.cursor(dictionary=True)
            cursor.execute(sql)
            resultado = cursor.fetchall()
            cursor.close()
            return resultado
        except Error as e:
            print(f"Error en consulta: {e}")
            return []
    
    def ejecutar(self, sql, datos):
        """Ejecuta INSERT, UPDATE o DELETE"""
        try:
            cursor = self.conexion.cursor()
            cursor.execute(sql, datos)
            self.conexion.commit()
            cursor.close()
            return "ok"
        except Error as e:
            print(f"Error al ejecutar: {e}")
            return str(e)
    
    def cerrar(self):
        """Cierra la conexión a la base de datos"""
        if self.conexion and self.conexion.is_connected():
            self.conexion.close()
            print("Conexión cerrada")