# Sistema de Gestión de Boletas

Aplicación web simple con Flask y JavaScript para gestionar boletas de productos con selección automática basada en monto objetivo.

## Características

- Gestión de productos (CRUD completo)
- Generación automática de boletas basada en monto objetivo
- Algoritmo de optimización tipo "problema de la mochila"
- Respeto de restricciones de despacho mínimo
- Tolerancia configurable de ±5 en el monto
- Interfaz web limpia y funcional

## Requisitos Previos

- Python 3.8 o superior
- MySQL Server 5.7 o superior
- pip (gestor de paquetes de Python)

## Estructura del Proyecto

```
boleta/
├── app.py                      # Backend Flask con API REST
├── config.py                   # Configuración de base de datos
├── schema.sql                  # Script SQL para crear base de datos
├── requirements.txt            # Dependencias Python
├── templates/
│   └── index.html             # Interfaz web única
├── static/
│   ├── css/
│   │   └── styles.css         # Estilos CSS
│   └── js/
│       └── main.js            # Lógica frontend JavaScript
└── README.md                   # Este archivo
```

## Instalación y Configuración

### 1. Clonar o descargar el proyecto

```bash
cd boleta
```

### 2. Crear entorno virtual (recomendado)

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Linux/Mac:
source venv/bin/activate
# En Windows:
venv\Scripts\activate
```

### 3. Instalar dependencias Python

```bash
pip install -r requirements.txt
```

### 4. Configurar MySQL

#### Instalar MySQL (si no está instalado)

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
```

**macOS (con Homebrew):**
```bash
brew install mysql
brew services start mysql
```

**Windows:**
- Descargar e instalar desde [mysql.com](https://dev.mysql.com/downloads/installer/)

#### Crear la base de datos

```bash
# Acceder a MySQL
mysql -u root -p

# Si no tienes contraseña (entorno local):
mysql -u root
```

Dentro de MySQL, ejecutar:
```sql
source schema.sql;
exit;
```

O alternativamente:
```bash
mysql -u root < schema.sql
```

### 5. Configurar credenciales de base de datos

Editar el archivo `config.py` y ajustar las credenciales según tu configuración:

```python
class Config:
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''  # Cambiar si tienes contraseña
    MYSQL_DB = 'boletas_db'
```

### 6. Ejecutar la aplicación

```bash
python app.py
```

La aplicación estará disponible en: **http://localhost:5000**

## Uso

### 1. Agregar Productos

- Completar el formulario con:
  - Nombre del producto (requerido)
  - Precio unitario (requerido)
  - Stock disponible
  - Si tiene despacho mínimo (checkbox)
  - Cantidad mínima de despacho (si aplica)

### 2. Ver Lista de Productos

- Los productos se muestran automáticamente en la tabla
- Se puede eliminar productos desde la columna "Acciones"

### 3. Generar Boleta

- Ingresar el monto objetivo deseado
- Opcionalmente ajustar la tolerancia (default: ±5)
- Hacer clic en "Generar Boleta"
- El sistema seleccionará automáticamente la mejor combinación de productos

## Algoritmo de Selección

El sistema utiliza un algoritmo de backtracking optimizado (variante del problema de la mochila) que:

1. Busca combinaciones de productos que se ajusten al monto objetivo ±tolerancia
2. Respeta las restricciones de stock disponible
3. Cumple con las cantidades mínimas de despacho
4. Prioriza la combinación más cercana al monto exacto
5. Retorna la mejor solución encontrada

### Restricciones consideradas:

- **Stock disponible**: No se pueden seleccionar más unidades de las disponibles
- **Despacho mínimo**: Si un producto tiene despacho mínimo, se debe incluir al menos la cantidad mínima especificada
- **Tolerancia de precio**: El total debe estar dentro del rango [monto_objetivo - tolerancia, monto_objetivo + tolerancia]

## API Endpoints

### Productos

- `GET /api/productos` - Obtener todos los productos
- `POST /api/productos` - Crear nuevo producto
- `PUT /api/productos/<id>` - Actualizar producto
- `DELETE /api/productos/<id>` - Eliminar producto

### Boleta

- `POST /api/generar-boleta` - Generar boleta
  ```json
  {
    "monto_objetivo": 10000,
    "tolerancia": 5
  }
  ```

## Solución de Problemas

### Error de conexión a MySQL

**Problema:** `Can't connect to MySQL server`

**Solución:**
```bash
# Verificar que MySQL esté corriendo
sudo systemctl status mysql  # Linux
brew services list          # macOS

# Iniciar MySQL si está detenido
sudo systemctl start mysql  # Linux
brew services start mysql   # macOS
```

### Error: "Access denied for user 'root'"

**Solución:** Verificar credenciales en `config.py` o resetear contraseña de MySQL

### Error: "No module named 'flask'"

**Solución:**
```bash
# Asegurarse de que el entorno virtual esté activado
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstalar dependencias
pip install -r requirements.txt
```

### La base de datos no se crea

**Solución:**
```bash
# Crear manualmente
mysql -u root -p
CREATE DATABASE boletas_db;
USE boletas_db;
source schema.sql;
```

## Tecnologías Utilizadas

- **Backend:** Flask 3.0.0, Flask-SQLAlchemy 3.1.1
- **Base de datos:** MySQL con PyMySQL
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **Algoritmos:** Backtracking optimizado para problema de la mochila

## Características Técnicas

- API RESTful con JSON
- Validaciones en backend y frontend
- Programación dinámica para optimización
- Responsive design
- Manejo de errores robusto
- Transacciones de base de datos seguras

## Mejoras Futuras

- Autenticación de usuarios
- Historial de boletas generadas
- Exportación de boletas a PDF
- Gráficos y estadísticas
- Búsqueda y filtros de productos
- Edición de productos inline

## Licencia

Proyecto de código abierto para uso educativo y comercial.

## Soporte

Para reportar problemas o sugerencias, crear un issue en el repositorio del proyecto.
