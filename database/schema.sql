
CREATE DATABASE IF NOT EXISTS db_hidrofact;
USE db_hidrofact;

-- TABLA: login
-- Almacena credenciales del administrador
CREATE TABLE login (
    idLogin INT PRIMARY KEY AUTO_INCREMENT,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    clave VARCHAR(255) NOT NULL,
    rol VARCHAR(20) DEFAULT 'Administrador'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLA: usuarios
-- Almacena información de clientes
CREATE TABLE usuarios (
    idUsuario INT PRIMARY KEY AUTO_INCREMENT,
    num_contador VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(100),
    estado ENUM('Activo', 'Inactivo') DEFAULT 'Activo',
    INDEX idx_contador (num_contador),
    INDEX idx_nombre (nombre),
    INDEX idx_estado (estado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLA: lecturas
-- Registra lecturas mensuales del contador
CREATE TABLE lecturas (
    idLectura INT PRIMARY KEY AUTO_INCREMENT,
    idUsuario INT NOT NULL,
    fechaLectura DATE NOT NULL,
    lecturaAnterior DECIMAL(10,2) NOT NULL,
    lecturaActual DECIMAL(10,2) NOT NULL,
    consumoM3 DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (idUsuario) REFERENCES usuarios(idUsuario) ON DELETE CASCADE,
    INDEX idx_usuario (idUsuario),
    INDEX idx_fecha (fechaLectura)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLA: facturas
-- Almacena facturas generadas
CREATE TABLE facturas (
    idFactura INT PRIMARY KEY AUTO_INCREMENT,
    idUsuario INT NOT NULL,
    idLectura INT NULL,
    fechaEmision DATE NOT NULL,
    fechaVencimiento DATE NOT NULL,
    tipoFactura VARCHAR(50) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL DEFAULT 0,
    mora DECIMAL(10,2) NOT NULL DEFAULT 0,
    montoTotal DECIMAL(10,2) NOT NULL,
    estado ENUM('Pendiente', 'Pagada', 'Vencida') DEFAULT 'Pendiente',
    FOREIGN KEY (idUsuario) REFERENCES usuarios(idUsuario) ON DELETE CASCADE,
    FOREIGN KEY (idLectura) REFERENCES lecturas(idLectura) ON DELETE SET NULL,
    INDEX idx_usuario (idUsuario),
    INDEX idx_estado (estado),
    INDEX idx_fecha_emision (fechaEmision)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLA: pagos
-- Registra pagos realizados
CREATE TABLE pagos (
    idPago INT PRIMARY KEY AUTO_INCREMENT,
    idFactura INT NOT NULL,
    fechaPago DATE NOT NULL,
    montoPagado DECIMAL(10,2) NOT NULL,
    metodoPago VARCHAR(50),
    FOREIGN KEY (idFactura) REFERENCES facturas(idFactura) ON DELETE CASCADE,
    INDEX idx_factura (idFactura),
    INDEX idx_fecha (fechaPago)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLA: tarifas
-- Almacena precios de servicios
CREATE TABLE tarifas (
    idTarifa INT PRIMARY KEY AUTO_INCREMENT,
    concepto VARCHAR(100) UNIQUE NOT NULL,
    precioUnitario DECIMAL(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;