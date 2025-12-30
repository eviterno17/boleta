// Estado de la aplicación
const app = {
    productos: [],
    init() {
        this.cargarProductos();
        this.configurarEventos();
    },

    configurarEventos() {
        // Formulario de producto
        document.getElementById('form-producto').addEventListener('submit', (e) => {
            e.preventDefault();
            this.agregarProducto();
        });

        // Checkbox de despacho mínimo
        document.getElementById('tiene_despacho_minimo').addEventListener('change', (e) => {
            const cantidadInput = document.getElementById('cantidad_minima_despacho');
            cantidadInput.disabled = !e.target.checked;
            if (!e.target.checked) {
                cantidadInput.value = '';
            }
        });

        // Formulario de boleta
        document.getElementById('form-boleta').addEventListener('submit', (e) => {
            e.preventDefault();
            this.generarBoleta();
        });
    },

    async cargarProductos() {
        try {
            const response = await fetch('/api/productos');
            if (!response.ok) throw new Error('Error al cargar productos');

            this.productos = await response.json();
            this.renderizarProductos();
        } catch (error) {
            this.mostrarMensaje('error', 'Error al cargar productos: ' + error.message);
        }
    },

    async agregarProducto() {
        const formData = new FormData(document.getElementById('form-producto'));
        const data = {
            nombre: formData.get('nombre'),
            precio_unitario: parseFloat(formData.get('precio_unitario')),
            stock: parseInt(formData.get('stock')) || 0,
            tiene_despacho_minimo: formData.get('tiene_despacho_minimo') === 'on',
            cantidad_minima_despacho: formData.get('cantidad_minima_despacho')
                ? parseInt(formData.get('cantidad_minima_despacho'))
                : null
        };

        // Validaciones
        if (!data.nombre || data.precio_unitario <= 0) {
            this.mostrarMensaje('error', 'Por favor complete los campos requeridos correctamente');
            return;
        }

        if (data.tiene_despacho_minimo && !data.cantidad_minima_despacho) {
            this.mostrarMensaje('error', 'Debe especificar la cantidad mínima de despacho');
            return;
        }

        try {
            const response = await fetch('/api/productos', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Error al agregar producto');
            }

            this.mostrarMensaje('exito', 'Producto agregado exitosamente');
            document.getElementById('form-producto').reset();
            document.getElementById('cantidad_minima_despacho').disabled = true;
            this.cargarProductos();
        } catch (error) {
            this.mostrarMensaje('error', 'Error: ' + error.message);
        }
    },

    async eliminarProducto(id) {
        if (!confirm('¿Está seguro de eliminar este producto?')) {
            return;
        }

        try {
            const response = await fetch(`/api/productos/${id}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Error al eliminar producto');
            }

            this.mostrarMensaje('exito', 'Producto eliminado exitosamente');
            this.cargarProductos();
        } catch (error) {
            this.mostrarMensaje('error', 'Error: ' + error.message);
        }
    },

    async generarBoleta() {
        const nombre = document.getElementById('nombre_cliente').value.trim();
        const dni = document.getElementById('dni_cliente').value.trim();
        const lugar = document.getElementById('lugar_cliente').value.trim();
        const monto_objetivo = parseFloat(document.getElementById('monto_objetivo').value);
        const tolerancia = parseFloat(document.getElementById('tolerancia').value) || 5;

        // Validaciones
        if (!nombre || !dni || !lugar) {
            alert('Por favor complete todos los campos requeridos (Nombre, DNI, Lugar)');
            return;
        }

        if (!monto_objetivo || monto_objetivo <= 0) {
            alert('Por favor ingrese un monto objetivo válido');
            return;
        }

        try {
            const response = await fetch('/api/generar-boleta', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    nombre,
                    dni,
                    lugar,
                    monto_objetivo,
                    tolerancia
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Error al generar boleta');
            }

            const boleta = await response.json();
            this.mostrarBoleta(boleta);
        } catch (error) {
            alert('Error: ' + error.message);
            document.getElementById('resultado-boleta').style.display = 'none';
        }
    },

    renderizarProductos() {
        const tbody = document.querySelector('#tabla-productos tbody');
        tbody.innerHTML = '';

        if (this.productos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">No hay productos registrados</td></tr>';
            return;
        }

        this.productos.forEach(producto => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${producto.id}</td>
                <td>${producto.nombre}</td>
                <td>$${producto.precio_unitario.toFixed(2)}</td>
                <td>${producto.stock}</td>
                <td>${producto.tiene_despacho_minimo ? 'Sí' : 'No'}</td>
                <td>${producto.cantidad_minima_despacho || '-'}</td>
                <td>
                    <button class="btn btn-danger" onclick="app.eliminarProducto(${producto.id})">
                        Eliminar
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    },

    mostrarBoleta(boleta) {
        const resultadoDiv = document.getElementById('resultado-boleta');
        const infoDiv = document.getElementById('info-boleta');
        const tbody = document.querySelector('#tabla-boleta tbody');

        // Si hay error
        if (boleta.error) {
            infoDiv.innerHTML = `
                <p style="color: #f56565; font-weight: bold;">${boleta.error}</p>
            `;
            tbody.innerHTML = '';
            document.getElementById('total-boleta').textContent = '0.00';
            resultadoDiv.style.display = 'block';
            return;
        }

        // Mostrar información de la boleta
        infoDiv.innerHTML = `
            <div style="margin-bottom: 15px; padding-bottom: 15px; border-bottom: 2px solid #667eea;">
                <p><strong>Nombre:</strong> ${boleta.nombre}</p>
                <p><strong>DNI:</strong> ${boleta.dni}</p>
                <p><strong>Lugar:</strong> ${boleta.lugar}</p>
            </div>
            <p><strong>Monto Objetivo:</strong> $${boleta.monto_objetivo.toFixed(2)}</p>
            <p><strong>Diferencia:</strong> $${boleta.diferencia.toFixed(2)}</p>
            <p style="color: #48bb78;"><strong>Productos encontrados:</strong> ${boleta.productos.length}</p>
        `;

        // Mostrar productos de la boleta
        tbody.innerHTML = '';
        boleta.productos.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${item.nombre}</td>
                <td>$${item.precio_unitario.toFixed(2)}</td>
                <td>${item.cantidad}</td>
                <td>$${item.subtotal.toFixed(2)}</td>
            `;
            tbody.appendChild(tr);
        });

        document.getElementById('total-boleta').textContent = boleta.total.toFixed(2);
        resultadoDiv.style.display = 'block';

        // Scroll suave a la boleta
        resultadoDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    },

    mostrarMensaje(tipo, mensaje) {
        const mensajeDiv = document.getElementById('mensaje-productos');
        mensajeDiv.className = `mensaje ${tipo}`;
        mensajeDiv.textContent = mensaje;

        // Ocultar después de 5 segundos
        setTimeout(() => {
            mensajeDiv.style.display = 'none';
        }, 5000);
    }
};

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
