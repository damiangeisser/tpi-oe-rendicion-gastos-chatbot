-- ============================================================
-- ESQUEMA DE BASE DE DATOS
-- Proyecto: Rendición de gastos internos mediante chatbot
-- Motor: SQLite
--
-- NOTA SOBRE EL MOTOR DE BASE DE DATOS
--
-- Se utiliza SQLite por ser un motor que permite persistir los datos
-- en un archivo local sin requerir la instalación o administración
-- de un servidor de base de datos externo, y sus capacidades son suficientes
-- la ejecución y demostración del trabajo práctico.
--
-- En SQLite, las claves foráneas se declaran dentro de la sentencia
-- CREATE TABLE ya que no permite agregar restricciones FOREIGN KEY posteriormente
-- mediante una sentencia ALTER TABLE estándar. Por este motivo, algunas claves
-- foráneas se declaran durante la creación de tablas aunque la tabla
-- referenciada se cree más adelante en el mismo script.
--
-- Antes de cargar datos, todas las tablas deben haber sido creadas y la
-- validación de claves foráneas debe estar activada mediante:
--
-- PRAGMA foreign_keys = ON;
-- ============================================================

PRAGMA foreign_keys = ON;

-- ============================================================
-- TABLAS DE REFERENCIA INICIALES
-- ============================================================

CREATE TABLE IF NOT EXISTS lookup_roles (
    id TEXT PRIMARY KEY,
    codigo INTEGER NOT NULL UNIQUE,
    descripcion TEXT NOT NULL UNIQUE,
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),

    creado_por TEXT,
    modificado_por TEXT,
    creado_en TEXT NOT NULL,
    modificado_en TEXT NOT NULL,

    FOREIGN KEY (creado_por) REFERENCES usuarios(id),
    FOREIGN KEY (modificado_por) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS lookup_areas (
    id TEXT PRIMARY KEY,
    codigo INTEGER NOT NULL UNIQUE,
    descripcion TEXT NOT NULL UNIQUE,
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),

    creado_por TEXT,
    modificado_por TEXT,
    creado_en TEXT NOT NULL,
    modificado_en TEXT NOT NULL,

    FOREIGN KEY (creado_por) REFERENCES usuarios(id),
    FOREIGN KEY (modificado_por) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS lookup_categorias_gasto (
    id TEXT PRIMARY KEY,
    codigo INTEGER NOT NULL UNIQUE,
    descripcion TEXT NOT NULL UNIQUE,
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),

    creado_por TEXT,
    modificado_por TEXT,
    creado_en TEXT NOT NULL,
    modificado_en TEXT NOT NULL,

    FOREIGN KEY (creado_por) REFERENCES usuarios(id),
    FOREIGN KEY (modificado_por) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS lookup_estados_solicitud (
    id TEXT PRIMARY KEY,
    codigo INTEGER NOT NULL UNIQUE,
    descripcion TEXT NOT NULL UNIQUE,
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),

    creado_por TEXT,
    modificado_por TEXT,
    creado_en TEXT NOT NULL,
    modificado_en TEXT NOT NULL,

    FOREIGN KEY (creado_por) REFERENCES usuarios(id),
    FOREIGN KEY (modificado_por) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS lookup_estados_conversacion (
    id TEXT PRIMARY KEY,
    codigo INTEGER NOT NULL UNIQUE,
    descripcion TEXT NOT NULL UNIQUE,
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),

    creado_por TEXT,
    modificado_por TEXT,
    creado_en TEXT NOT NULL,
    modificado_en TEXT NOT NULL,

    FOREIGN KEY (creado_por) REFERENCES usuarios(id),
    FOREIGN KEY (modificado_por) REFERENCES usuarios(id)
);

-- ============================================================
-- USUARIOS
-- ============================================================

CREATE TABLE IF NOT EXISTS usuarios (
    id TEXT PRIMARY KEY,
    legajo TEXT UNIQUE,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,

    rol_codigo INTEGER NOT NULL,
    area_codigo INTEGER NOT NULL,

    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),

    creado_por TEXT,
    modificado_por TEXT,
    creado_en TEXT NOT NULL,
    modificado_en TEXT NOT NULL,

    FOREIGN KEY (rol_codigo) REFERENCES lookup_roles(codigo),
    FOREIGN KEY (area_codigo) REFERENCES lookup_areas(codigo),
    FOREIGN KEY (creado_por) REFERENCES usuarios(id),
    FOREIGN KEY (modificado_por) REFERENCES usuarios(id)
);

-- ============================================================
-- POLÍTICAS DE GASTOS
-- ============================================================

CREATE TABLE IF NOT EXISTS politicas_gastos (
    id TEXT PRIMARY KEY,

    area_codigo INTEGER NOT NULL,
    categoria_gasto_codigo INTEGER NOT NULL,
    monto_maximo REAL NOT NULL CHECK (monto_maximo > 0),
    requiere_comprobante INTEGER NOT NULL DEFAULT 1 CHECK (requiere_comprobante IN (0, 1)),
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),

    creado_por TEXT,
    modificado_por TEXT,
    creado_en TEXT NOT NULL,
    modificado_en TEXT NOT NULL,

    UNIQUE (area_codigo, categoria_gasto_codigo),

    FOREIGN KEY (area_codigo) REFERENCES lookup_areas(codigo),
    FOREIGN KEY (categoria_gasto_codigo) REFERENCES lookup_categorias_gasto(codigo),
    FOREIGN KEY (creado_por) REFERENCES usuarios(id),
    FOREIGN KEY (modificado_por) REFERENCES usuarios(id)
);

-- ============================================================
-- SOLICITUDES
-- ============================================================

CREATE TABLE IF NOT EXISTS solicitudes (
    id TEXT PRIMARY KEY,

    telegram_user_id TEXT NOT NULL,
    solicitante_id TEXT,
    usuario_asignado_id TEXT,

    categoria_gasto_codigo INTEGER,
    politica_gasto_id TEXT,

    estado_solicitud_codigo INTEGER NOT NULL,
    estado_conversacion_codigo INTEGER NOT NULL,

    fecha_gasto TEXT,
    monto REAL CHECK (monto IS NULL OR monto > 0),

    comprobante_file_id TEXT,

    validacion_ocr_simulada INTEGER CHECK (
        validacion_ocr_simulada IN (0, 1)
        OR validacion_ocr_simulada IS NULL
    ),
    resultado_validacion_ocr TEXT,

    intentos_fecha INTEGER NOT NULL DEFAULT 0 CHECK (intentos_fecha >= 0),
    intentos_monto INTEGER NOT NULL DEFAULT 0 CHECK (intentos_monto >= 0),
    intentos_comprobante INTEGER NOT NULL DEFAULT 0 CHECK (intentos_comprobante >= 0),

    motivo_cancelacion TEXT,
    motivo_rechazo TEXT,

    creado_por TEXT,
    modificado_por TEXT,
    creado_en TEXT NOT NULL,
    modificado_en TEXT NOT NULL,

    FOREIGN KEY (solicitante_id) REFERENCES usuarios(id),
    FOREIGN KEY (usuario_asignado_id) REFERENCES usuarios(id),
    FOREIGN KEY (categoria_gasto_codigo) REFERENCES lookup_categorias_gasto(codigo),
    FOREIGN KEY (politica_gasto_id) REFERENCES politicas_gastos(id),
    FOREIGN KEY (estado_solicitud_codigo) REFERENCES lookup_estados_solicitud(codigo),
    FOREIGN KEY (estado_conversacion_codigo) REFERENCES lookup_estados_conversacion(codigo),
    FOREIGN KEY (creado_por) REFERENCES usuarios(id),
    FOREIGN KEY (modificado_por) REFERENCES usuarios(id)
);