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


# Modelo de Boleta
class Boleta(db.Model):
    __tablename__ = 'boletas'

    id = db.Column(db.Integer, primary_key=True)
    nombre_cliente = db.Column(db.String(255), nullable=False)
    dni_cliente = db.Column(db.String(50), nullable=False)
    lugar_cliente = db.Column(db.String(255), nullable=False)
    monto_objetivo = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    diferencia = db.Column(db.Numeric(10, 2), nullable=False)
    productos_json = db.Column(db.Text, nullable=False)  # JSON con productos
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'nombre_cliente': self.nombre_cliente,
            'dni_cliente': self.dni_cliente,
            'lugar_cliente': self.lugar_cliente,
            'monto_objetivo': float(self.monto_objetivo),
            'total': float(self.total),
            'diferencia': float(self.diferencia),
            'productos': json.loads(self.productos_json),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Algoritmo RÁPIDO de generación de boleta (enfoque greedy optimizado)
def generar_boleta_optimizada(monto_objetivo, tolerancia=5):
    """
    Genera una boleta óptima de manera RÁPIDA usando enfoque greedy.
    REQUIERE MÍNIMO 3 PRODUCTOS DIFERENTES

    Args:
        monto_objetivo (float): Monto objetivo a alcanzar
        tolerancia (float): Tolerancia permitida (default: 5)

    Returns:
        dict: Boleta con productos seleccionados y total
    """
    productos = Producto.query.filter(Producto.stock > 0).all()

    if not productos:
        return {'productos': [], 'total': 0, 'error': 'No hay productos disponibles'}

    if len(productos) < 3:
        return {'productos': [], 'total': 0, 'error': 'Se requieren al menos 3 productos diferentes en inventario'}

    monto_min = monto_objetivo - tolerancia
    monto_max = monto_objetivo + tolerancia

    # Preparar productos para el algoritmo
    items = []
    for p in productos:
        precio = float(p.precio_unitario)
        cantidad_min = p.cantidad_minima_despacho if (p.tiene_despacho_minimo and p.cantidad_minima_despacho) else 1
        items.append({
            'producto': p,
            'precio': precio,
            'cantidad_min': cantidad_min,
            'stock': p.stock
        })

    # Ordenar por precio (de menor a mayor)
    items.sort(key=lambda x: x['precio'])

    mejor_solucion = None
    mejor_diferencia = float('inf')

    # Estrategia 1: Agregar PRIMERO 3 productos con cantidad mínima, luego optimizar
    solucion = {}
    total = 0.0

    # Paso 1: Agregar los primeros 3 productos más baratos con cantidad mínima
    productos_agregados = 0
    for item in items:
        if productos_agregados >= 3:
            break

        precio = item['precio']
        cantidad_min = item['cantidad_min']
        producto = item['producto']

        # Verificar que podemos agregar al menos la cantidad mínima
        costo_minimo = precio * cantidad_min
        if total + costo_minimo <= monto_max and cantidad_min <= item['stock']:
            solucion[producto.id] = {'producto': producto, 'cantidad': cantidad_min}
            total += costo_minimo
            productos_agregados += 1

    # Paso 2: Si tenemos 3 productos, intentar completar hasta el monto objetivo
    if len(solucion) >= 3:
        # Intentar agregar más cantidad a los productos existentes
        for prod_id in list(solucion.keys()):
            item_data = solucion[prod_id]
            producto = item_data['producto']
            cantidad_actual = item_data['cantidad']

            # Encontrar el item original
            item_original = next((i for i in items if i['producto'].id == prod_id), None)
            if not item_original:
                continue

            precio = item_original['precio']
            stock = item_original['stock']

            # Calcular cuántas unidades más podemos agregar
            espacio_restante = monto_max - total
            unidades_adicionales = min(int(espacio_restante / precio), stock - cantidad_actual)

            if unidades_adicionales > 0:
                # Agregar de a una hasta acercarnos al objetivo
                for extra in range(1, unidades_adicionales + 1):
                    nuevo_total = total + (precio * extra)
                    if monto_min <= nuevo_total <= monto_max:
                        solucion[prod_id]['cantidad'] += extra
                        total = nuevo_total
                        break

            # Si ya estamos en rango, salir
            if monto_min <= total <= monto_max:
                break

        # Validar solución
        if monto_min <= total <= monto_max:
            diferencia = abs(total - monto_objetivo)
            mejor_diferencia = diferencia
            mejor_solucion = solucion

    # Estrategia 2: Si no funcionó, intentar con productos más caros
    if mejor_solucion is None:
        items.reverse()  # De caro a barato
        solucion = {}
        total = 0.0

        # Agregar primeros 3 productos más caros con cantidad mínima
        productos_agregados = 0
        for item in items:
            if productos_agregados >= 3:
                break

            precio = item['precio']
            cantidad_min = item['cantidad_min']
            producto = item['producto']

            costo_minimo = precio * cantidad_min
            if total + costo_minimo <= monto_max and cantidad_min <= item['stock']:
                solucion[producto.id] = {'producto': producto, 'cantidad': cantidad_min}
                total += costo_minimo
                productos_agregados += 1

        # Completar hasta el monto
        if len(solucion) >= 3:
            for prod_id in list(solucion.keys()):
                item_data = solucion[prod_id]
                producto = item_data['producto']
                cantidad_actual = item_data['cantidad']

                item_original = next((i for i in items if i['producto'].id == prod_id), None)
                if not item_original:
                    continue

                precio = item_original['precio']
                stock = item_original['stock']
                espacio_restante = monto_max - total
                unidades_adicionales = min(int(espacio_restante / precio), stock - cantidad_actual)

                if unidades_adicionales > 0:
                    for extra in range(1, unidades_adicionales + 1):
                        nuevo_total = total + (precio * extra)
                        if monto_min <= nuevo_total <= monto_max:
                            solucion[prod_id]['cantidad'] += extra
                            total = nuevo_total
                            break

                if monto_min <= total <= monto_max:
                    break

            if monto_min <= total <= monto_max:
                diferencia = abs(total - monto_objetivo)
                if diferencia < mejor_diferencia:
                    mejor_diferencia = diferencia
                    mejor_solucion = solucion

    if mejor_solucion is None:
        return {
            'productos': [],
            'total': 0,
            'error': f'No se encontró combinación válida para el monto ${monto_objetivo} (±${tolerancia}). Se requieren mínimo 3 productos diferentes.'
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
    """Generar boleta basada en monto objetivo y guardarla en BD"""
    import json
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

        # Generar boleta con algoritmo optimizado
        resultado = generar_boleta_optimizada(monto_objetivo, tolerancia)

        # Agregar información del cliente
        resultado['nombre'] = data['nombre']
        resultado['dni'] = data['dni']
        resultado['lugar'] = data['lugar']

        # Guardar en base de datos (solo si se generó correctamente)
        if 'error' not in resultado and resultado['productos']:
            nueva_boleta = Boleta(
                nombre_cliente=data['nombre'],
                dni_cliente=data['dni'],
                lugar_cliente=data['lugar'],
                monto_objetivo=monto_objetivo,
                total=resultado['total'],
                diferencia=resultado['diferencia'],
                productos_json=json.dumps(resultado['productos'])
            )
            db.session.add(nueva_boleta)
            db.session.commit()
            resultado['boleta_id'] = nueva_boleta.id

        return jsonify(resultado)
    except ValueError:
        return jsonify({'error': 'Monto objetivo debe ser un número válido'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/boletas', methods=['GET'])
def obtener_boletas():
    """Obtener historial de boletas generadas"""
    boletas = Boleta.query.order_by(Boleta.created_at.desc()).limit(50).all()
    return jsonify([b.to_dict() for b in boletas])


if __name__ == '__main__':
    # Crear tablas si no existen
    with app.app_context():
        db.create_all()

    app.run(debug=True, host='0.0.0.0', port=5000)
