"""Script de inicialización de la base de datos para entornos de desarrollo y demostración.

Elimina la base de datos existente (si existe) y la vuelve a crear ejecutando
en orden el script de esquema y el script de datos iniciales.
"""

import sqlite3
import sys
from pathlib import Path

DIRECTORIO_BASE = Path(__file__).resolve().parent
DIRECTORIO_DB = DIRECTORIO_BASE / "db"

RUTA_BASE_DATOS = DIRECTORIO_DB / "rendicion_gastos.db"
RUTA_ESQUEMA = DIRECTORIO_DB / "esquema.sql"
RUTA_DATOS_INICIALES = DIRECTORIO_DB / "datos_iniciales.sql"


def leer_script_sql(ruta: Path) -> str:
    """Lee un archivo de script SQL en formato UTF-8."""
    return ruta.read_text(encoding="utf-8")


def eliminar_base_datos_existente(ruta: Path) -> None:
    """Elimina el archivo de base de datos si existe, para recrearlo desde cero."""
    if ruta.exists():
        ruta.unlink()


def crear_base_datos(ruta: Path, script_esquema: str, script_datos_iniciales: str) -> None:
    """Crea la base de datos ejecutando primero el esquema y luego los datos iniciales."""
    conexion = sqlite3.connect(ruta)
    try:
        conexion.execute("PRAGMA foreign_keys = ON;")
        conexion.executescript(script_esquema)
        conexion.executescript(script_datos_iniciales)
        conexion.commit()
    except sqlite3.Error:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def main() -> None:
    try:
        script_esquema = leer_script_sql(RUTA_ESQUEMA)
        script_datos_iniciales = leer_script_sql(RUTA_DATOS_INICIALES)

        eliminar_base_datos_existente(RUTA_BASE_DATOS)
        crear_base_datos(RUTA_BASE_DATOS, script_esquema, script_datos_iniciales)
    except FileNotFoundError as error:
        print(f"Error: no se encontró el archivo requerido: {error.filename}")
        sys.exit(1)
    except sqlite3.Error as error:
        print(f"Error al inicializar la base de datos: {error}")
        sys.exit(1)

    print(f"Base de datos inicializada correctamente en: {RUTA_BASE_DATOS}")


if __name__ == "__main__":
    main()
