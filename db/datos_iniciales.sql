PRAGMA foreign_keys = ON;

-- ============================================================
-- DATOS INICIALES
-- Proyecto: Rendición de gastos internos mediante chatbot
-- Motor: SQLite
-- ============================================================

BEGIN TRANSACTION;

-- ============================================================
-- LOOKUP: ROLES
-- Se insertan primero porque usuarios depende de roles.
-- Los metadatos se cargan inicialmente en NULL porque todavía no
-- existe el usuario administrador.
-- ============================================================

INSERT INTO lookup_roles (
    id, codigo, descripcion, activo, creado_por, modificado_por, creado_en, modificado_en
) VALUES
('6fc35dec-74cf-465b-a2dc-5274becb0b93', 1, 'Empleado', 1, NULL, NULL, '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('99615834-04e7-47ae-a738-65cbdcc77e9a', 2, 'Supervisor', 1, NULL, NULL, '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('733c7d99-8291-44ea-b362-080cce9f5626', 3, 'Administrador', 1, NULL, NULL, '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('f5d62bcb-d5f3-4e35-8979-b877e20f0e2d', 4, 'Sistema', 1, NULL, NULL, '2026-01-01T00:00:00', '2026-01-01T00:00:00');

-- ============================================================
-- LOOKUP: ÁREAS
-- Se insertan antes de usuarios porque usuarios depende de áreas.
-- ============================================================

INSERT INTO lookup_areas (
    id, codigo, descripcion, activo, creado_por, modificado_por, creado_en, modificado_en
) VALUES
('9da0cf7e-309a-4ecd-85e0-35787052a9fa', 1, 'Administración', 1, NULL, NULL, '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('2a547c2c-b4da-4745-a25b-f4a3fa2fdff0', 2, 'Finanzas', 1, NULL, NULL, '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('b2be5f5b-0da1-496f-ab92-a564aa3d0d4d', 3, 'Ventas', 1, NULL, NULL, '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('ce3b36e1-2678-4879-8ac7-cb65f08e1da0', 4, 'Sistemas', 1, NULL, NULL, '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('9928c507-705b-467a-910d-3c6d5c8d03ac', 5, 'Soporte', 1, NULL, NULL, '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('6316f747-05ff-4e36-ad03-a42870277806', 6, 'Recursos Humanos', 1, NULL, NULL, '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('814acbf3-6a2a-443c-b756-738476fe01c3', 7, 'Operaciones', 1, NULL, NULL, '2026-01-01T00:00:00', '2026-01-01T00:00:00');

-- Se crea el usuario administrador para luego actualizar los
-- registros anteriores con su ID como creador y modificador
-- y así mantener la consistencia de los datos.

INSERT INTO usuarios (
    id, legajo, nombre, apellido, email,
    rol_codigo, area_codigo, activo,
    creado_por, modificado_por, creado_en, modificado_en
) VALUES (
    '219c931b-b3d4-4364-a3cb-2c9d94578482',
    'A0001',
    'Sofía',
    'Martínez',
    'sofia.martinez@empresa.local',
    3,
    4,
    1,
    NULL,
    NULL,
    '2026-01-01T00:00:00',
    '2026-01-01T00:00:00'
);

UPDATE lookup_roles
SET creado_por = '219c931b-b3d4-4364-a3cb-2c9d94578482',
    modificado_por = '219c931b-b3d4-4364-a3cb-2c9d94578482',
    modificado_en = '2026-01-01T00:00:00'
WHERE creado_por IS NULL;

UPDATE lookup_areas
SET creado_por = '219c931b-b3d4-4364-a3cb-2c9d94578482',
    modificado_por = '219c931b-b3d4-4364-a3cb-2c9d94578482',
    modificado_en = '2026-01-01T00:00:00'
WHERE creado_por IS NULL;

UPDATE usuarios
SET creado_por = '219c931b-b3d4-4364-a3cb-2c9d94578482',
    modificado_por = '219c931b-b3d4-4364-a3cb-2c9d94578482',
    modificado_en = '2026-01-01T00:00:00'
WHERE id = '219c931b-b3d4-4364-a3cb-2c9d94578482';

-- ============================================================
-- USUARIOS DE PRUEBA
-- Sistema, supervisor y tres empleados.
-- ============================================================

INSERT INTO usuarios (
    id, legajo, nombre, apellido, email,
    rol_codigo, area_codigo, activo,
    creado_por, modificado_por, creado_en, modificado_en
) VALUES
(
    '112767ec-6e2a-4c1b-81e3-ff4f0cc332b9',
    NULL,
    'Sistema',
    'Chatbot',
    'sistema.chatbot@empresa.local',
    4,
    4,
    1,
    '219c931b-b3d4-4364-a3cb-2c9d94578482',
    '219c931b-b3d4-4364-a3cb-2c9d94578482',
    '2026-01-01T00:00:00',
    '2026-01-01T00:00:00'
),
(
    'd4eb029d-dc7c-4fe2-8627-a33a3264b88a',
    'S0001',
    'Martín',
    'Silva',
    'martin.silva@empresa.local',
    2,
    2,
    1,
    '219c931b-b3d4-4364-a3cb-2c9d94578482',
    '219c931b-b3d4-4364-a3cb-2c9d94578482',
    '2026-01-01T00:00:00',
    '2026-01-01T00:00:00'
),
(
    '7f2d2d9a-43bd-4af0-aad7-c246d615e24d',
    'E1001',
    'Laura',
    'Fernández',
    'laura.fernandez@empresa.local',
    1,
    3,
    1,
    '219c931b-b3d4-4364-a3cb-2c9d94578482',
    '219c931b-b3d4-4364-a3cb-2c9d94578482',
    '2026-01-01T00:00:00',
    '2026-01-01T00:00:00'
),
(
    '6f7b81cf-d08b-4803-858e-910ea099a72a',
    'E1002',
    'Diego',
    'Ramírez',
    'diego.ramirez@empresa.local',
    1,
    7,
    1,
    '219c931b-b3d4-4364-a3cb-2c9d94578482',
    '219c931b-b3d4-4364-a3cb-2c9d94578482',
    '2026-01-01T00:00:00',
    '2026-01-01T00:00:00'
),
(
    '611d784d-f772-4ed5-8c72-06d2f913280d',
    'E1003',
    'Camila',
    'Torres',
    'camila.torres@empresa.local',
    1,
    5,
    1,
    '219c931b-b3d4-4364-a3cb-2c9d94578482',
    '219c931b-b3d4-4364-a3cb-2c9d94578482',
    '2026-01-01T00:00:00',
    '2026-01-01T00:00:00'
);

-- ============================================================
-- LOOKUP: CATEGORÍAS DE GASTO
-- ============================================================

INSERT INTO lookup_categorias_gasto (
    id, codigo, descripcion, activo, creado_por, modificado_por, creado_en, modificado_en
) VALUES
('beb1cb05-61b8-4986-b578-4dd4a669fe23', 1, 'Viáticos', 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('d0d6f89a-25f2-478e-8fd9-b27db5ecc559', 2, 'Comidas', 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('4fe7d047-95fe-453b-b06d-2c13fe9d09b4', 3, 'Transporte', 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('3fc93c5f-9656-41c5-8e8d-549011044306', 4, 'Librería', 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('3d2c13c5-f03f-498d-b7ec-189bf451efbc', 5, 'Otros', 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00');

-- ============================================================
-- LOOKUP: ESTADOS DE SOLICITUD
-- ============================================================

INSERT INTO lookup_estados_solicitud (
    id, codigo, descripcion, activo, creado_por, modificado_por, creado_en, modificado_en
) VALUES
('4a9b1de9-f502-4f55-8f6f-97d21a4f89a5', 1, 'En curso', 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('71687e1e-0566-4f9f-a2b0-df2d40de01d8', 2, 'Aprobada', 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('e52d46f9-eb7b-47ca-9f84-85c43e2e1f93', 3, 'Rechazada', 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('97931e8e-b746-4886-b131-71e9ce224d10', 4, 'Cancelada', 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('2d0e0482-b70b-4745-b75e-69f67c9c900d', 5, 'Derivada a supervisor', 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00');

-- ============================================================
-- LOOKUP: ESTADOS DE CONVERSACIÓN
-- ============================================================

INSERT INTO lookup_estados_conversacion (
    id, codigo, descripcion, activo, creado_por, modificado_por, creado_en, modificado_en
) VALUES
('c11e3ffe-d030-4fd1-a403-0abdafd97b93', 1, 'Inicio', 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('906f080e-b15a-4258-a3c8-d37392fa2d17', 2, 'Esperando legajo', 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('f2b91438-e8ef-4ec8-a018-1fdc7bf8ac7a', 3, 'Esperando categoría', 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('84b18080-1fa3-424e-a81e-f32dd81ea7e4', 4, 'Esperando fecha', 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('1f111a3c-5c3a-4337-bd40-6a4e6c463f2e', 5, 'Esperando monto', 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('8accd195-b311-443a-8605-c57f26f27541', 6, 'Esperando comprobante', 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('38aceaba-4d44-4a22-b4b6-ad734cdff268', 7, 'Esperando revisión de supervisor', 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('96a4533c-4134-4c6a-b6b0-6cdfb2ff88b0', 8, 'Finalizado', 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00');

-- ============================================================
-- POLÍTICAS DE GASTOS
-- Regla:
-- - Administración, Finanzas, Sistemas, Soporte y RR. HH.:
--   solo Librería y Otros.
-- - Ventas:
--   Viáticos, Comidas, Transporte y Otros.
-- - Operaciones:
--   Viáticos, Transporte y Otros.
--
-- Todas las políticas requieren comprobante JPG.
-- ============================================================

INSERT INTO politicas_gastos (
    id, area_codigo, categoria_gasto_codigo, monto_maximo, requiere_comprobante, activo,
    creado_por, modificado_por, creado_en, modificado_en
) VALUES
-- Administración
('3f776e06-356f-4133-8cd6-3c711c62219d', 1, 4, 90000.00, 1, 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('69be7b3e-b972-4365-a53e-5d0871d17a38', 1, 5, 120000.00, 1, 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),

-- Finanzas
('2f66cfa6-d0bb-42a6-8e70-b6fa1c61e7aa', 2, 4, 80000.00, 1, 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('3c31b289-8502-4ff0-8027-28bb04d0cc1e', 2, 5, 100000.00, 1, 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),

-- Ventas
('f6e98803-f298-43e6-9950-a6a0f8bd499f', 3, 1, 260000.00, 1, 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('2cd6659f-1204-463d-9ee1-a6b6364f5f6c', 3, 2, 160000.00, 1, 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('b882b3c1-ec3b-4a68-ac85-86eb55e4d027', 3, 3, 180000.00, 1, 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('ed08bd79-47ee-4774-85af-b7680c48db28', 3, 5, 140000.00, 1, 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),

-- Sistemas
('d9976f6d-804a-49aa-a38b-fc9fad2f94de', 4, 4, 90000.00, 1, 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('d2f849d3-bc16-4336-bd07-366d671273cd', 4, 5, 170000.00, 1, 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),

-- Soporte
('a3da6550-9e3d-492f-b596-1598f264d59f', 5, 4, 85000.00, 1, 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('392cd3bd-b0a2-4c2c-a119-57260842d61b', 5, 5, 140000.00, 1, 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),

-- Recursos Humanos
('42b8a21c-8dfc-482c-b0d6-f934008cdb8e', 6, 4, 95000.00, 1, 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('739864e9-32f0-4589-995a-e80bf9631c40', 6, 5, 150000.00, 1, 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),

-- Operaciones
('97df4363-7098-4c56-8ccb-a9d9569cfd2d', 7, 1, 300000.00, 1, 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('532890cc-2f58-4d0b-8146-44a3f8a1a576', 7, 3, 220000.00, 1, 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00'),
('f4b8edac-a1d1-48ea-9b31-d5b394c60118', 7, 5, 180000.00, 1, 1, '219c931b-b3d4-4364-a3cb-2c9d94578482', '219c931b-b3d4-4364-a3cb-2c9d94578482', '2026-01-01T00:00:00', '2026-01-01T00:00:00');

COMMIT;