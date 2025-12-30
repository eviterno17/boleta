"""
Configuración de la base de datos MySQL
"""

class Config:
    # Configuración de MySQL
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''  # Cambiar si tienes contraseña
    MYSQL_DB = 'boletas_db'

    # Configuración de SQLAlchemy
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuración de Flask
    SECRET_KEY = 'tu_clave_secreta_aqui'  # Cambiar en producción
