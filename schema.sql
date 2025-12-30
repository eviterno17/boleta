-- Crear la base de datos
CREATE DATABASE IF NOT EXISTS boletas_db;
USE boletas_db;

-- Crear tabla de productos
CREATE TABLE IF NOT EXISTS productos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    precio_unitario DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    tiene_despacho_minimo BOOLEAN DEFAULT FALSE,
    cantidad_minima_despacho INT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Crear tabla de boletas
CREATE TABLE IF NOT EXISTS boletas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_cliente VARCHAR(255) NOT NULL,
    dni_cliente VARCHAR(50) NOT NULL,
    lugar_cliente VARCHAR(255) NOT NULL,
    monto_objetivo DECIMAL(10, 2) NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    diferencia DECIMAL(10, 2) NOT NULL,
    productos_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_cliente (dni_cliente),
    INDEX idx_fecha (created_at)
);

-- Insertar algunos productos de ejemplo
INSERT INTO productos (nombre, precio_unitario, stock, tiene_despacho_minimo, cantidad_minima_despacho) VALUES
('Arroz 1kg', 1500.00, 100, TRUE, 5),
('Fideos 500g', 800.00, 150, FALSE, NULL),
('Aceite 1L', 2500.00, 80, TRUE, 3),
('Azúcar 1kg', 1200.00, 120, FALSE, NULL),
('Leche 1L', 1000.00, 90, TRUE, 6),
('Pan de molde', 1800.00, 60, FALSE, NULL),
('Café instantáneo 100g', 3500.00, 70, FALSE, NULL),
('Té en bolsitas', 1400.00, 100, FALSE, NULL),
('Sal 1kg', 600.00, 200, TRUE, 10),
('Harina 1kg', 1100.00, 110, FALSE, NULL);
