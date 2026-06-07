"""Punto de entrada del chatbot de rendición de gastos internos.

Antes de iniciar el polling, se verifican los requisitos básicos de arranque
(configuración, base de datos y conexión con Telegram) para detectar problemas
de forma temprana y con mensajes claros en el log.
"""

import logging
import sqlite3
import sys
from pathlib import Path

from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

logger.info("Iniciando la aplicación de rendición de gastos internos...")

try:
    import configuracion
except RuntimeError as error:
    logger.error("Error al cargar la configuración: %s", error, exc_info=True)
    sys.exit(1)

logger.info(
    "Configuración cargada correctamente (DATABASE_PATH=%s, MAX_COMPROBANTE_SIZE_MB=%d).",
    configuracion.DATABASE_PATH,
    configuracion.MAX_COMPROBANTE_SIZE_MB,
)

import base_datos
import manejadores_bot


def verificar_base_datos() -> None:
    """Verifica que la base de datos exista, sea legible y tenga las claves foráneas activas.

    Se ejecuta como chequeo de arranque para detectar problemas de la base de
    datos antes de poner el bot a recibir mensajes.
    """
    ruta_base_datos = Path(configuracion.DATABASE_PATH)
    if not ruta_base_datos.exists():
        raise RuntimeError(f"No se encontró el archivo de base de datos: {ruta_base_datos}")

    conexion = base_datos.obtener_conexion()
    try:
        (claves_foraneas_activas,) = conexion.execute("PRAGMA foreign_keys;").fetchone()
        if claves_foraneas_activas != 1:
            raise RuntimeError("La conexión a la base de datos no tiene activas las claves foráneas.")

        tablas = conexion.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table';"
        ).fetchall()
        logger.info(
            "Base de datos verificada: claves foráneas activas y %d tabla(s) encontradas en %s.",
            len(tablas),
            ruta_base_datos,
        )
    finally:
        conexion.close()


async def registrar_identidad_bot(application: Application) -> None:
    """Tarea de post-inicialización: confirma la identidad del bot ante Telegram.

    Se ejecuta una única vez, antes de comenzar el polling, y deja constancia
    en el log de que el token configurado corresponde a un bot válido.
    """
    bot_info = await application.bot.get_me()
    logger.info(
        "Identidad del bot confirmada ante Telegram: @%s (%s).",
        bot_info.username,
        bot_info.first_name,
    )


def main() -> None:
    """Verifica los requisitos de arranque e inicia el bot mediante polling."""
    try:
        verificar_base_datos()
    except (RuntimeError, sqlite3.Error) as error:
        logger.error("Error al verificar la base de datos: %s", error, exc_info=True)
        sys.exit(1)

    aplicacion = (
        Application.builder()
        .token(configuracion.TELEGRAM_BOT_TOKEN)
        .post_init(registrar_identidad_bot)
        .build()
    )

    aplicacion.add_handler(CommandHandler("start", manejadores_bot.manejar_start))
    aplicacion.add_handler(CommandHandler("ayuda", manejadores_bot.manejar_ayuda))
    aplicacion.add_handler(CommandHandler("cancelar", manejadores_bot.manejar_cancelar))
    aplicacion.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, manejadores_bot.manejar_mensaje_texto)
    )
    aplicacion.add_handler(
        CallbackQueryHandler(manejadores_bot.manejar_seleccion_categoria, pattern=r"^categoria:\d+$")
    )

    try:
        logger.info("Iniciando el polling de Telegram...")
        logger.info("Bot iniciado correctamente. Esperando mensajes. Presione Ctrl+C para detener.")
        aplicacion.run_polling()
    except KeyboardInterrupt:
        pass
    except TelegramError as error:
        logger.error("No se pudo establecer la conexión con Telegram: %s", error, exc_info=True)
        sys.exit(1)
    except Exception as error:
        logger.error("Error inesperado al ejecutar el bot: %s", error, exc_info=True)
        sys.exit(1)

    logger.info("Bot detenido con Ctrl+C. Aplicación finalizada.")


if __name__ == "__main__":
    main()
