"""Carga y validación de la configuración del proyecto a partir de variables de entorno."""

import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError(
        "Falta definir TELEGRAM_BOT_TOKEN en el archivo .env."
    )

DATABASE_PATH = os.getenv("DATABASE_PATH")
if not DATABASE_PATH:
    raise RuntimeError(
        "Falta definir DATABASE_PATH en el archivo .env."
    )

_max_comprobante_size_mb_texto = os.getenv("MAX_COMPROBANTE_SIZE_MB")
if not _max_comprobante_size_mb_texto:
    raise RuntimeError(
        "Falta definir MAX_COMPROBANTE_SIZE_MB en el archivo .env."
    )

try:
    MAX_COMPROBANTE_SIZE_MB = int(_max_comprobante_size_mb_texto)
except ValueError as error:
    raise RuntimeError(
        "MAX_COMPROBANTE_SIZE_MB debe ser un número entero."
    ) from error

MAX_COMPROBANTE_SIZE_BYTES = MAX_COMPROBANTE_SIZE_MB * 1024 * 1024
