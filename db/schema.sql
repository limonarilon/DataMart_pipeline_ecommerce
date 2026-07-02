-- ============================================================
-- DataMart · Esquema de base de datos destino (SQLite)
-- ============================================================

-- Tabla de ventas válidas (el "dato bueno" del negocio)
CREATE TABLE IF NOT EXISTS ventas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no      TEXT NOT NULL,
    stock_code      TEXT NOT NULL,
    description     TEXT,
    quantity        INTEGER NOT NULL,
    invoice_date    TEXT NOT NULL,
    unit_price      REAL NOT NULL,
    customer_id     TEXT,              -- se guarda ENMASCARADO (ética)
    total_venta     REAL NOT NULL,
    country         TEXT,
    job_id          TEXT NOT NULL,
    fecha_carga     TEXT NOT NULL
);

-- Tabla de devoluciones (regla de negocio: Quantity < 0 / InvoiceNo con prefijo 'C')
-- No son errores de calidad, son eventos de negocio válidos y se separan para no
-- distorsionar las métricas de ventas.
CREATE TABLE IF NOT EXISTS devoluciones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no      TEXT NOT NULL,
    stock_code      TEXT NOT NULL,
    description     TEXT,
    quantity        INTEGER NOT NULL,
    invoice_date    TEXT NOT NULL,
    unit_price      REAL NOT NULL,
    customer_id     TEXT,
    total_devuelto  REAL NOT NULL,
    country         TEXT,
    job_id          TEXT NOT NULL,
    fecha_carga     TEXT NOT NULL
);

-- Tabla de registros rechazados (errores de calidad de datos), con causa y trazabilidad
CREATE TABLE IF NOT EXISTS rechazos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no      TEXT,
    stock_code      TEXT,
    description     TEXT,
    quantity        INTEGER,
    invoice_date    TEXT,
    unit_price      REAL,
    customer_id     TEXT,
    country         TEXT,
    causa           TEXT NOT NULL,      -- descripcion_faltante / duplicado / cliente_no_identificado / precio_invalido / cantidad_cero
    job_id          TEXT NOT NULL,
    fecha_carga     TEXT NOT NULL
);

-- Tabla de logs de ejecución (evidencia y trazabilidad del pipeline / control de flujo)
CREATE TABLE IF NOT EXISTS logs_ejecucion (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id              TEXT NOT NULL,
    fecha_inicio        TEXT NOT NULL,
    total_leidos        INTEGER NOT NULL,
    total_validos       INTEGER NOT NULL,
    total_devoluciones  INTEGER NOT NULL,
    total_rechazados    INTEGER NOT NULL,
    tiempo_ms           REAL NOT NULL,
    origen_archivo      TEXT NOT NULL
);

-- Índices para optimizar las consultas del dashboard (bloque de optimización)
CREATE INDEX IF NOT EXISTS idx_ventas_country ON ventas(country);
CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(invoice_date);
CREATE INDEX IF NOT EXISTS idx_ventas_stock ON ventas(stock_code);
CREATE INDEX IF NOT EXISTS idx_rechazos_causa ON rechazos(causa);
