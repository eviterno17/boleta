"""
Aplicación Flask para gestión de boletas de productos
"""

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from config import Config
from itertools import combinations_with_replacement
from decimal import Decimal

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)


# Modelo de Producto
class Producto(db.Model):
    __tablename__ = 'productos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    tiene_despacho_minimo = db.Column(db.Boolean, default=False)
    cantidad_minima_despacho = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'precio_unitario': float(self.precio_unitario),
            'stock': self.stock,
            'tiene_despacho_minimo': self.tiene_despacho_minimo,
            'cantidad_minima_despacho': self.cantidad_minima_despacho
        }


# Algoritmo de generación de boleta (problema de la mochila)
def generar_boleta_optimizada(monto_objetivo, tolerancia=5):
    """
    Genera una boleta óptima basada en el monto objetivo con tolerancia de ±5.
    Usa programación dinámica con restricciones de despacho mínimo.

    Args:
        monto_objetivo (float): Monto objetivo a alcanzar
        tolerancia (float): Tolerancia permitida (default: 5)

    Returns:
        dict: Boleta con productos seleccionados y total
    """
    productos = Producto.query.filter(Producto.stock > 0).all()

    if not productos:
        return {'productos': [], 'total': 0, 'error': 'No hay productos disponibles'}

    monto_min = monto_objetivo - tolerancia
    monto_max = monto_objetivo + tolerancia

    # Convertir a enteros para trabajar con centavos (evitar problemas de punto flotante)
    monto_min_cents = int(monto_min * 100)
    monto_max_cents = int(monto_max * 100)
    monto_objetivo_cents = int(monto_objetivo * 100)

    mejor_solucion = None
    mejor_diferencia = float('inf')

    # Intentar diferentes combinaciones usando backtracking optimizado
    def backtrack(index, combinacion_actual, total_actual):
        nonlocal mejor_solucion, mejor_diferencia

        # Si el total está dentro del rango, verificar si es mejor solución
        if monto_min_cents <= total_actual <= monto_max_cents:
            diferencia = abs(total_actual - monto_objetivo_cents)
            if diferencia < mejor_diferencia:
                mejor_diferencia = diferencia
                mejor_solucion = combinacion_actual.copy()

        # Si ya superamos el máximo, no seguir explorando
        if total_actual > monto_max_cents:
            return

        # Si ya revisamos todos los productos, retornar
        if index >= len(productos):
            return

        producto = productos[index]
        precio_cents = int(float(producto.precio_unitario) * 100)

        # Determinar cantidad mínima - DEBE respetar restricción de despacho
        if producto.tiene_despacho_minimo and producto.cantidad_minima_despacho:
            cantidad_min = producto.cantidad_minima_despacho
        else:
            cantidad_min = 1

        # Intentar diferentes cantidades de este producto
        max_cantidad = min(producto.stock, (monto_max_cents - total_actual) // precio_cents + 5)

        # Opción 1: No incluir este producto (solo si no hay restricción o si podemos seguir sin él)
        backtrack(index + 1, combinacion_actual, total_actual)

        # Opción 2: Incluir el producto respetando cantidad mínima de despacho
        # Si tiene despacho mínimo, DEBE incluirse con al menos la cantidad mínima
        for cantidad in range(cantidad_min, max_cantidad + 1):
            nuevo_total = total_actual + (precio_cents * cantidad)
            if nuevo_total <= monto_max_cents + (precio_cents * 2):  # Pequeño margen extra
                nueva_combinacion = combinacion_actual.copy()
                nueva_combinacion[producto.id] = {
                    'producto': producto,
                    'cantidad': cantidad
                }
                backtrack(index + 1, nueva_combinacion, nuevo_total)

    # Iniciar búsqueda
    backtrack(0, {}, 0)

    if mejor_solucion is None:
        return {
            'productos': [],
            'total': 0,
            'error': f'No se encontró combinación válida para el monto ${monto_objetivo} (±${tolerancia})'
        }

    # Construir respuesta
    productos_seleccionados = []
    total_real = 0

    for prod_id, datos in mejor_solucion.items():
        producto = datos['producto']
        cantidad = datos['cantidad']
        subtotal = float(producto.precio_unitario) * cantidad

        productos_seleccionados.append({
            'id': producto.id,
            'nombre': producto.nombre,
            'precio_unitario': float(producto.precio_unitario),
            'cantidad': cantidad,
            'subtotal': subtotal
        })
        total_real += subtotal

    return {
        'productos': productos_seleccionados,
        'total': round(total_real, 2),
        'monto_objetivo': monto_objetivo,
        'diferencia': round(abs(total_real - monto_objetivo), 2)
    }


# Rutas
@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')


@app.route('/api/productos', methods=['GET'])
def obtener_productos():
    """Obtener todos los productos"""
    productos = Producto.query.all()
    return jsonify([p.to_dict() for p in productos])


@app.route('/api/productos', methods=['POST'])
def crear_producto():
    """Crear un nuevo producto"""
    data = request.get_json()

    # Validaciones
    if not data.get('nombre') or not data.get('precio_unitario'):
        return jsonify({'error': 'Nombre y precio son requeridos'}), 400

    try:
        nuevo_producto = Producto(
            nombre=data['nombre'],
            precio_unitario=data['precio_unitario'],
            stock=data.get('stock', 0),
            tiene_despacho_minimo=data.get('tiene_despacho_minimo', False),
            cantidad_minima_despacho=data.get('cantidad_minima_despacho')
        )

        db.session.add(nuevo_producto)
        db.session.commit()

        return jsonify(nuevo_producto.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/productos/<int:producto_id>', methods=['PUT'])
def actualizar_producto(producto_id):
    """Actualizar un producto existente"""
    producto = Producto.query.get_or_404(producto_id)
    data = request.get_json()

    try:
        if 'nombre' in data:
            producto.nombre = data['nombre']
        if 'precio_unitario' in data:
            producto.precio_unitario = data['precio_unitario']
        if 'stock' in data:
            producto.stock = data['stock']
        if 'tiene_despacho_minimo' in data:
            producto.tiene_despacho_minimo = data['tiene_despacho_minimo']
        if 'cantidad_minima_despacho' in data:
            producto.cantidad_minima_despacho = data['cantidad_minima_despacho']

        db.session.commit()
        return jsonify(producto.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/productos/<int:producto_id>', methods=['DELETE'])
def eliminar_producto(producto_id):
    """Eliminar un producto"""
    producto = Producto.query.get_or_404(producto_id)

    try:
        db.session.delete(producto)
        db.session.commit()
        return jsonify({'message': 'Producto eliminado exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/generar-boleta', methods=['POST'])
def generar_boleta():
    """Generar boleta basada en monto objetivo"""
    data = request.get_json()

    if not data.get('monto_objetivo'):
        return jsonify({'error': 'Monto objetivo es requerido'}), 400

    # Validar campos requeridos
    if not data.get('nombre'):
        return jsonify({'error': 'El nombre es requerido'}), 400
    if not data.get('dni'):
        return jsonify({'error': 'El DNI es requerido'}), 400
    if not data.get('lugar'):
        return jsonify({'error': 'El lugar es requerido'}), 400

    try:
        monto_objetivo = float(data['monto_objetivo'])
        tolerancia = float(data.get('tolerancia', 5))

        if monto_objetivo <= 0:
            return jsonify({'error': 'El monto debe ser mayor a 0'}), 400

        resultado = generar_boleta_optimizada(monto_objetivo, tolerancia)

        # Agregar información del cliente a la boleta
        resultado['nombre'] = data['nombre']
        resultado['dni'] = data['dni']
        resultado['lugar'] = data['lugar']

        return jsonify(resultado)
    except ValueError:
        return jsonify({'error': 'Monto objetivo debe ser un número válido'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Crear tablas si no existen
    with app.app_context():
        db.create_all()

    app.run(debug=True, host='0.0.0.0', port=5000)
