"""Utilidad para exportar las tablas de la base de datos a archivos CSV.

Genera un archivo CSV por cada tabla relevante dentro de la carpeta
exportaciones/, además de un detalle legible de las solicitudes que combina
información de las tablas relacionadas (usuario, área, categoría y estados).

Pensado para inspeccionar los datos de demostración con planillas de cálculo,
por eso los archivos se codifican en utf-8-sig (UTF-8 con BOM).
"""

import csv
import sqlite3
import sys
from pathlib import Path

import base_datos

DIRECTORIO_BASE = Path(__file__).resolve().parent
DIRECTORIO_EXPORTACIONES = DIRECTORIO_BASE / "exportaciones"

TABLAS_A_EXPORTAR = (
    "lookup_roles",
    "lookup_areas",
    "lookup_categorias_gasto",
    "lookup_estados_solicitud",
    "lookup_estados_conversacion",
    "usuarios",
    "politicas_gastos",
    "solicitudes",
)

CONSULTA_SOLICITUDES_DETALLE = """
    SELECT
        s.id AS solicitud_id,
        s.telegram_user_id AS telegram_user_id,
        TRIM(COALESCE(u.nombre, '') || ' ' || COALESCE(u.apellido, '')) AS solicitante_nombre_completo,
        u.legajo AS solicitante_legajo,
        a.descripcion AS solicitante_area,
        c.descripcion AS categoria,
        es.descripcion AS estado_solicitud,
        ec.descripcion AS estado_conversacion,
        s.fecha_gasto AS fecha_gasto,
        s.monto AS monto,
        s.validacion_ocr_simulada AS validacion_ocr_simulada,
        s.resultado_validacion_ocr AS resultado_validacion_ocr,
        s.motivo_cancelacion AS motivo_cancelacion,
        s.motivo_rechazo AS motivo_rechazo,
        s.creado_en AS creado_en,
        s.modificado_en AS modificado_en
    FROM solicitudes AS s
    LEFT JOIN usuarios AS u ON u.id = s.solicitante_id
    LEFT JOIN lookup_areas AS a ON a.codigo = u.area_codigo
    LEFT JOIN lookup_categorias_gasto AS c ON c.codigo = s.categoria_gasto_codigo
    LEFT JOIN lookup_estados_solicitud AS es ON es.codigo = s.estado_solicitud_codigo
    LEFT JOIN lookup_estados_conversacion AS ec ON ec.codigo = s.estado_conversacion_codigo
    ORDER BY s.creado_en;
"""


def _escribir_csv(ruta_archivo: Path, encabezados, filas) -> None:
    """Escribe un archivo CSV en utf-8-sig, incluyendo encabezados aunque no haya filas."""
    with ruta_archivo.open("w", newline="", encoding="utf-8-sig") as archivo_csv:
        escritor = csv.writer(archivo_csv)
        escritor.writerow(encabezados)
        for fila in filas:
            escritor.writerow(tuple(fila))


def _exportar_tabla(conexion: sqlite3.Connection, nombre_tabla: str) -> None:
    """Exporta una tabla completa a exportaciones/<tabla>.csv.

    El nombre de la tabla proviene exclusivamente de TABLAS_A_EXPORTAR, una
    lista fija definida en este módulo y no de una entrada del usuario, por lo
    que es seguro construir la sentencia SELECT a partir de dicho nombre.
    """
    cursor = conexion.execute(f"SELECT * FROM {nombre_tabla};")
    encabezados = [columna[0] for columna in cursor.description]
    filas = cursor.fetchall()

    ruta_archivo = DIRECTORIO_EXPORTACIONES / f"{nombre_tabla}.csv"
    _escribir_csv(ruta_archivo, encabezados, filas)
    print(f"Tabla '{nombre_tabla}' exportada a {ruta_archivo} ({len(filas)} fila(s)).")


def _exportar_detalle_solicitudes(conexion: sqlite3.Connection) -> None:
    """Exporta un detalle legible de las solicitudes a exportaciones/solicitudes_detalle.csv."""
    cursor = conexion.execute(CONSULTA_SOLICITUDES_DETALLE)
    encabezados = [columna[0] for columna in cursor.description]
    filas = cursor.fetchall()

    ruta_archivo = DIRECTORIO_EXPORTACIONES / "solicitudes_detalle.csv"
    _escribir_csv(ruta_archivo, encabezados, filas)
    print(f"Detalle de solicitudes exportado a {ruta_archivo} ({len(filas)} fila(s)).")


def main() -> None:
    """Exporta todas las tablas configuradas y el detalle de solicitudes a archivos CSV."""
    try:
        DIRECTORIO_EXPORTACIONES.mkdir(exist_ok=True)

        conexion = base_datos.obtener_conexion()
        try:
            for nombre_tabla in TABLAS_A_EXPORTAR:
                _exportar_tabla(conexion, nombre_tabla)
            _exportar_detalle_solicitudes(conexion)
        finally:
            conexion.close()
    except (sqlite3.Error, OSError) as error:
        print(f"Error al exportar los datos: {error}")
        sys.exit(1)

    print(f"Exportación completada correctamente. Archivos disponibles en: {DIRECTORIO_EXPORTACIONES}")


if __name__ == "__main__":
    main()
