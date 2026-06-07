"""Acceso a la conexión de la base de datos SQLite del proyecto."""

import sqlite3
from pathlib import Path

from configuracion import DATABASE_PATH

RUTA_BASE_DATOS = Path(DATABASE_PATH)


def obtener_conexion() -> sqlite3.Connection:
    """Abre una conexión a la base de datos con las claves foráneas activadas.

    Cada conexión SQLite debe habilitar PRAGMA foreign_keys = ON de forma
    explícita, ya que esta validación no se conserva entre conexiones.
    """
    conexion = sqlite3.connect(RUTA_BASE_DATOS)
    conexion.execute("PRAGMA foreign_keys = ON;")
    conexion.row_factory = sqlite3.Row
    return conexion
