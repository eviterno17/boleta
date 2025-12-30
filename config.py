"""
Configuración de la base de datos MySQL
"""

class Config:
    # Configuración de MySQL
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = '#Celular0523'  # Cambiar si tienes contraseña
    MYSQL_DB = 'boletas_db'

    # Configuración de SQLAlchemy (construida después de definir las variables)
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuración de Flask
    SECRET_KEY = 'clave-local-desarrollo-123'  # Para uso local está bien cualquier string

# Construir la URI después de definir la clase
Config.SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{Config.MYSQL_USER}:{Config.MYSQL_PASSWORD}@{Config.MYSQL_HOST}/{Config.MYSQL_DB}'
