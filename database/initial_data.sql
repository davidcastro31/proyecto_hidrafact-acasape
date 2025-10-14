
USE db_hidrofact;


-- Usuario administrador por defecto
-- Usuario: admin
-- Contraseña: admin123
INSERT INTO login (usuario, clave, rol) 
VALUES ('admin', 'admin123', 'Administrador');

-- Tarifas del sistema
INSERT INTO tarifas (concepto, precioUnitario) VALUES
('CUOTA UNICA 1-5m³', 7.00),
('M³ ADICIONAL', 0.50),
('CONTADORES A 0m³', 2.00),
('MORA (RECIBO VENCIDO)', 2.00),
('RECONEXION (VOLUNTARIA)', 10.00),
('RECONEXION (POR IMPAGO)', 25.00),
('NUEVA ACOMETIDA', 500.00),
('CUOTA MENSUAL (NUEVA ACOMETIDA)', 15.00),
('PRIMA POR NUEVA ACOMETIDA', 200.00);

-- Usuario de ejemplo (opcional)
INSERT INTO usuarios (num_contador, nombre, correo, estado) 
VALUES ('22028184', 'GLORIA LETICIA HIDALGO VAZQUEZ', 'gloria@example.com', 'Activo');