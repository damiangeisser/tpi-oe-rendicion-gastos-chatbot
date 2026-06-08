"""Utilidad para exportar las tablas de la base de datos a archivos CSV.

Genera, en una misma corrida, un archivo CSV por cada tabla real de la base de
datos dentro de la carpeta exportaciones/, además de un reporte legible de
solicitudes que combina información de las tablas relacionadas mediante joins
(usuario, área, categoría y estados).

Todos los archivos de una misma corrida comparten el mismo timestamp, generado
una única vez al inicio, para poder identificar fácilmente los archivos que
pertenecen a una misma exportación.

Pensado para inspeccionar los datos de demostración con planillas de cálculo,
por eso los archivos se codifican en utf-8-sig (UTF-8 con BOM).
"""

import csv
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import base_datos

DIRECTORIO_BASE = Path(__file__).resolve().parent
DIRECTORIO_EXPORTACIONES = DIRECTORIO_BASE / "exportaciones"

FORMATO_TIMESTAMP_EXPORTACION = "%Y%m%d_%H%M%S"

TABLAS_A_EXPORTAR = (
    "lookup_roles",
    "lookup_areas",
    "lookup_categorias_gasto",
    "lookup_estados_solicitud",
    "lookup_estados_conversacion",
    "usuarios",
    "usuarios_telegram",
    "politicas_gastos",
    "solicitudes",
)

NOMBRE_REPORTE_SOLICITUDES = "reporte_solicitudes"

CONSULTA_REPORTE_SOLICITUDES = """
    SELECT
        s.id AS solicitud_id,
        s.telegram_user_id AS telegram_user_id,
        solicitante.legajo AS solicitante_legajo,
        TRIM(COALESCE(solicitante.nombre, '') || ' ' || COALESCE(solicitante.apellido, '')) AS solicitante_nombre_completo,
        area.descripcion AS solicitante_area,
        TRIM(COALESCE(asignado.nombre, '') || ' ' || COALESCE(asignado.apellido, '')) AS usuario_asignado_nombre_completo,
        categoria.descripcion AS categoria,
        estado_solicitud.descripcion AS estado_solicitud,
        estado_conversacion.descripcion AS estado_conversacion,
        s.fecha_gasto AS fecha_gasto,
        s.monto AS monto,
        s.comprobante_file_id AS comprobante_file_id,
        s.validacion_ocr_simulada AS validacion_ocr_simulada,
        s.resultado_validacion_ocr AS resultado_validacion_ocr,
        s.intentos_fecha AS intentos_fecha,
        s.intentos_monto AS intentos_monto,
        s.intentos_comprobante AS intentos_comprobante,
        s.motivo_cancelacion AS motivo_cancelacion,
        s.motivo_rechazo AS motivo_rechazo,
        s.creado_en AS creado_en,
        s.modificado_en AS modificado_en
    FROM solicitudes AS s
    LEFT JOIN usuarios AS solicitante ON solicitante.id = s.solicitante_id
    LEFT JOIN lookup_areas AS area ON area.codigo = solicitante.area_codigo
    LEFT JOIN usuarios AS asignado ON asignado.id = s.usuario_asignado_id
    LEFT JOIN lookup_categorias_gasto AS categoria ON categoria.codigo = s.categoria_gasto_codigo
    LEFT JOIN lookup_estados_solicitud AS estado_solicitud ON estado_solicitud.codigo = s.estado_solicitud_codigo
    LEFT JOIN lookup_estados_conversacion AS estado_conversacion ON estado_conversacion.codigo = s.estado_conversacion_codigo
    ORDER BY s.creado_en;
"""


def generar_timestamp_exportacion() -> str:
    """Genera el timestamp de la corrida de exportación, con formato AAAAMMDD_HHMMSS.

    Se calcula una única vez al inicio de la corrida para que todos los
    archivos generados compartan el mismo identificador temporal.
    """
    return datetime.now().strftime(FORMATO_TIMESTAMP_EXPORTACION)


def construir_ruta_csv(nombre_base: str, timestamp: str) -> Path:
    """Arma la ruta destino de un CSV combinando su nombre base y el timestamp de la corrida."""
    return DIRECTORIO_EXPORTACIONES / f"{nombre_base}_{timestamp}.csv"


def obtener_columnas_tabla(conexion: sqlite3.Connection, nombre_tabla: str) -> list[str]:
    """Obtiene los nombres de columnas de una tabla real, en su orden de definición.

    El nombre de la tabla proviene exclusivamente de TABLAS_A_EXPORTAR, una
    lista fija definida en este módulo y no de una entrada del usuario, por lo
    que es seguro construir la sentencia PRAGMA a partir de dicho nombre.
    """
    filas = conexion.execute(f"PRAGMA table_info({nombre_tabla});").fetchall()
    return [fila["name"] for fila in filas]


def _escribir_csv(ruta_archivo: Path, encabezados, filas) -> None:
    """Escribe un archivo CSV en utf-8-sig, incluyendo encabezados aunque no haya filas."""
    with ruta_archivo.open("w", newline="", encoding="utf-8-sig") as archivo_csv:
        escritor = csv.writer(archivo_csv)
        escritor.writerow(encabezados)
        for fila in filas:
            escritor.writerow(tuple(fila))


def exportar_tabla(conexion: sqlite3.Connection, nombre_tabla: str, timestamp: str) -> None:
    """Exporta el contenido completo de una tabla real a un CSV propio de esta corrida.

    Se utiliza SELECT * porque el nombre de la tabla es fijo (proviene de
    TABLAS_A_EXPORTAR) y no de una entrada del usuario, por lo que no existe
    riesgo de inyección SQL.
    """
    columnas = obtener_columnas_tabla(conexion, nombre_tabla)
    filas = conexion.execute(f"SELECT * FROM {nombre_tabla};").fetchall()

    ruta_archivo = construir_ruta_csv(nombre_tabla, timestamp)
    _escribir_csv(ruta_archivo, columnas, filas)
    print(f"Tabla '{nombre_tabla}' -> {ruta_archivo} ({len(filas)} fila(s) exportada(s)).")


def exportar_reporte_solicitudes(conexion: sqlite3.Connection, timestamp: str) -> None:
    """Genera el reporte legible de solicitudes combinando datos de varias tablas mediante joins.

    A diferencia de las exportaciones de tablas, este archivo no es un volcado
    directo de una tabla: es un reporte derivado, pensado para que una persona
    pueda leer el estado de cada solicitud sin tener que cruzar códigos a mano.
    """
    cursor = conexion.execute(CONSULTA_REPORTE_SOLICITUDES)
    encabezados = [columna[0] for columna in cursor.description]
    filas = cursor.fetchall()

    ruta_archivo = construir_ruta_csv(NOMBRE_REPORTE_SOLICITUDES, timestamp)
    _escribir_csv(ruta_archivo, encabezados, filas)
    print(f"Reporte '{NOMBRE_REPORTE_SOLICITUDES}' -> {ruta_archivo} ({len(filas)} fila(s) exportada(s)).")


def main() -> None:
    """Exporta todas las tablas configuradas y el reporte de solicitudes a archivos CSV."""
    timestamp = generar_timestamp_exportacion()

    try:
        DIRECTORIO_EXPORTACIONES.mkdir(exist_ok=True)

        conexion = base_datos.obtener_conexion()
        try:
            for nombre_tabla in TABLAS_A_EXPORTAR:
                exportar_tabla(conexion, nombre_tabla, timestamp)
            exportar_reporte_solicitudes(conexion, timestamp)
        finally:
            conexion.close()
    except (sqlite3.Error, OSError) as error:
        print(f"Error al exportar los datos: {error}")
        sys.exit(1)

    print(f"Exportación completada correctamente (timestamp {timestamp}). Archivos disponibles en: {DIRECTORIO_EXPORTACIONES}")


if __name__ == "__main__":
    main()
