"""Manejadores de comandos y mensajes del bot de rendición de gastos internos.

Cada manejador delega el acceso a datos en servicios.py y se limita a
coordinar la conversación: leer el estado actual de la solicitud, invocar al
servicio correspondiente y responder al usuario en español.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import estados
import servicios
import validadores

MENSAJE_BIENVENIDA = (
    "¡Hola! Soy el bot de rendición de gastos internos.\n\n"
    "Vamos a iniciar una nueva solicitud de reembolso de gastos."
)

MENSAJE_AYUDA = (
    "Comandos disponibles:\n"
    "/start - Inicia o retoma una solicitud de rendición de gastos.\n"
    "/ayuda - Muestra este mensaje de ayuda.\n"
    "/cancelar - Cancela la solicitud activa."
)

MENSAJE_SOLICITUD_EN_CURSO = "Ya tenés una solicitud en curso. Continuemos donde la dejamos."

MENSAJE_PEDIR_LEGAJO = "Para comenzar, indicame tu número de legajo."

MENSAJE_LEGAJO_INVALIDO = (
    "No pudimos validar tu legajo: no corresponde a un empleado activo habilitado.\n"
    "La solicitud fue cancelada. Si creés que se trata de un error, comunicate con tu área de Recursos Humanos."
)

MENSAJE_LEGAJO_VALIDO = "¡Hola, {nombre} {apellido}! Validamos tu legajo correctamente."

MENSAJE_PEDIR_CATEGORIA = "Elegí la categoría del gasto que querés rendir:"

MENSAJE_CATEGORIA_REGISTRADA = "Categoría registrada: {categoria}."

MENSAJE_CATEGORIA_NO_DISPONIBLE = (
    "Esa categoría ya no está disponible. Por favor, elegí una de las opciones vigentes."
)

MENSAJE_ACCION_NO_ESPERADA = "Esa acción no corresponde en este momento de tu solicitud."

MENSAJE_PEDIR_FECHA = "Ingrese la fecha del gasto en formato DD/MM/AAAA."

MENSAJE_FECHA_REGISTRADA = "Fecha registrada: {fecha}. Ingrese el monto del gasto."

MENSAJE_FECHA_INVALIDA_REINTENTAR = (
    "La fecha ingresada no es válida. Use el formato DD/MM/AAAA. Intentos restantes: {restantes}."
)

MENSAJE_SOLICITUD_CANCELADA_POR_INTENTOS_FECHA = (
    "La solicitud fue cancelada porque se alcanzó la cantidad máxima de intentos para ingresar una fecha válida."
)

MENSAJE_USAR_START = "No tenés una solicitud activa. Enviá /start para iniciar una rendición de gastos."

MENSAJE_ESPERANDO_PROXIMO_PASO = (
    "Tu solicitud está en curso. En una próxima etapa continuaremos con los siguientes pasos."
)

MENSAJE_SIN_SOLICITUD_ACTIVA = "No tenés ninguna solicitud activa para cancelar."

MENSAJE_SOLICITUD_CANCELADA_POR_USUARIO = "Tu solicitud fue cancelada. Si querés iniciar una nueva, enviá /start."

MOTIVO_CANCELACION_LEGAJO_INVALIDO = "Legajo inválido o usuario no habilitado."

MOTIVO_CANCELACION_POR_USUARIO = "El usuario canceló la solicitud mediante el comando /cancelar."

MOTIVO_CANCELACION_INTENTOS_FECHA = "Cantidad máxima de intentos alcanzada al ingresar la fecha del gasto."


def _obtener_telegram_user_id(update: Update) -> str:
    """Extrae el identificador del usuario de Telegram como texto, tal como se almacena en la base."""
    return str(update.effective_user.id)


async def _solicitar_legajo(update: Update) -> None:
    """Envía el mensaje pidiendo al usuario que indique su número de legajo."""
    await update.message.reply_text(MENSAJE_PEDIR_LEGAJO)


async def _solicitar_categoria(update: Update) -> None:
    """Muestra las categorías de gasto activas como botones en línea, identificadas por su código."""
    categorias = servicios.listar_categorias_activas()
    teclado = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(categoria["descripcion"], callback_data=f"categoria:{categoria['codigo']}")]
            for categoria in categorias
        ]
    )
    await update.effective_message.reply_text(MENSAJE_PEDIR_CATEGORIA, reply_markup=teclado)


async def _solicitar_fecha(update: Update) -> None:
    """Envía el mensaje pidiendo la fecha del gasto en el formato esperado."""
    await update.effective_message.reply_text(MENSAJE_PEDIR_FECHA)


async def _continuar_segun_estado(update: Update, solicitud) -> None:
    """Retoma la conversación según el estado de conversación actual de la solicitud."""
    estado_conversacion = solicitud["estado_conversacion_codigo"]

    if estado_conversacion == estados.ESTADO_CONVERSACION_ESPERANDO_LEGAJO:
        await _solicitar_legajo(update)
    elif estado_conversacion == estados.ESTADO_CONVERSACION_ESPERANDO_CATEGORIA:
        await _solicitar_categoria(update)
    elif estado_conversacion == estados.ESTADO_CONVERSACION_ESPERANDO_FECHA:
        await _solicitar_fecha(update)
    else:
        await update.effective_message.reply_text(MENSAJE_ESPERANDO_PROXIMO_PASO)


async def _procesar_legajo(update: Update, solicitud) -> None:
    """Valida el legajo recibido y avanza o cancela la solicitud según el resultado."""
    legajo = update.message.text.strip()
    empleado = servicios.buscar_empleado_activo_por_legajo(legajo)

    if empleado is None:
        servicios.cancelar_solicitud(solicitud["id"], MOTIVO_CANCELACION_LEGAJO_INVALIDO)
        await update.message.reply_text(MENSAJE_LEGAJO_INVALIDO)
        return

    servicios.registrar_legajo_valido(solicitud["id"], empleado["id"])
    await update.message.reply_text(
        MENSAJE_LEGAJO_VALIDO.format(nombre=empleado["nombre"], apellido=empleado["apellido"])
    )
    await _solicitar_categoria(update)


async def _procesar_fecha(update: Update, solicitud) -> None:
    """Valida la fecha del gasto recibida y avanza, reintenta o cancela la solicitud según el resultado.

    La validación realizada acá se limita al formato y a que la fecha exista
    en el calendario. Las reglas de negocio sobre qué fechas son aceptables
    (por ejemplo, que correspondan al mes en curso) se aplican más adelante,
    durante la validación de la política de gastos.
    """
    texto_fecha = update.message.text.strip()

    try:
        fecha_gasto = validadores.validar_fecha_gasto(texto_fecha)
    except ValueError:
        intentos = servicios.incrementar_intentos_fecha(solicitud["id"])

        if intentos >= estados.MAX_INTENTOS_VALIDACION:
            servicios.cancelar_solicitud(solicitud["id"], MOTIVO_CANCELACION_INTENTOS_FECHA)
            await update.message.reply_text(MENSAJE_SOLICITUD_CANCELADA_POR_INTENTOS_FECHA)
            return

        restantes = estados.MAX_INTENTOS_VALIDACION - intentos
        await update.message.reply_text(MENSAJE_FECHA_INVALIDA_REINTENTAR.format(restantes=restantes))
        return

    servicios.registrar_fecha_solicitud(solicitud["id"], fecha_gasto)
    await update.message.reply_text(MENSAJE_FECHA_REGISTRADA.format(fecha=fecha_gasto.strftime("%d/%m/%Y")))


async def manejar_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inicia una nueva solicitud o retoma la solicitud activa del usuario de Telegram."""
    telegram_user_id = _obtener_telegram_user_id(update)
    solicitud = servicios.obtener_solicitud_activa_por_telegram(telegram_user_id)

    if solicitud is None:
        await update.message.reply_text(MENSAJE_BIENVENIDA)
        servicios.crear_solicitud_inicial(telegram_user_id)
        await _solicitar_legajo(update)
        return

    await update.message.reply_text(MENSAJE_SOLICITUD_EN_CURSO)
    await _continuar_segun_estado(update, solicitud)


async def manejar_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde al comando /ayuda con la lista de comandos disponibles."""
    await update.message.reply_text(MENSAJE_AYUDA)


async def manejar_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancela la solicitud activa del usuario, si existe."""
    telegram_user_id = _obtener_telegram_user_id(update)
    solicitud = servicios.obtener_solicitud_activa_por_telegram(telegram_user_id)

    if solicitud is None:
        await update.message.reply_text(MENSAJE_SIN_SOLICITUD_ACTIVA)
        return

    servicios.cancelar_solicitud(solicitud["id"], MOTIVO_CANCELACION_POR_USUARIO)
    await update.message.reply_text(MENSAJE_SOLICITUD_CANCELADA_POR_USUARIO)


async def manejar_mensaje_texto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enruta los mensajes de texto según el estado de conversación de la solicitud activa."""
    telegram_user_id = _obtener_telegram_user_id(update)
    solicitud = servicios.obtener_solicitud_activa_por_telegram(telegram_user_id)

    if solicitud is None:
        await update.message.reply_text(MENSAJE_USAR_START)
        return

    estado_conversacion = solicitud["estado_conversacion_codigo"]

    if estado_conversacion == estados.ESTADO_CONVERSACION_ESPERANDO_LEGAJO:
        await _procesar_legajo(update, solicitud)
        return

    if estado_conversacion == estados.ESTADO_CONVERSACION_ESPERANDO_FECHA:
        await _procesar_fecha(update, solicitud)
        return

    await update.message.reply_text(MENSAJE_ESPERANDO_PROXIMO_PASO)


async def manejar_seleccion_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Procesa la selección de una categoría de gasto realizada con los botones en línea."""
    consulta = update.callback_query
    await consulta.answer()

    telegram_user_id = _obtener_telegram_user_id(update)
    solicitud = servicios.obtener_solicitud_activa_por_telegram(telegram_user_id)

    if solicitud is None:
        await update.effective_message.reply_text(MENSAJE_USAR_START)
        return

    if solicitud["estado_conversacion_codigo"] != estados.ESTADO_CONVERSACION_ESPERANDO_CATEGORIA:
        await update.effective_message.reply_text(MENSAJE_ACCION_NO_ESPERADA)
        return

    categoria_codigo = int(consulta.data.split(":", 1)[1])
    categoria = servicios.obtener_categoria_activa_por_codigo(categoria_codigo)

    if categoria is None:
        await update.effective_message.reply_text(MENSAJE_CATEGORIA_NO_DISPONIBLE)
        return

    servicios.registrar_categoria_solicitud(solicitud["id"], categoria_codigo)
    confirmacion = MENSAJE_CATEGORIA_REGISTRADA.format(categoria=categoria["descripcion"])
    await update.effective_message.reply_text(f"{confirmacion} {MENSAJE_PEDIR_FECHA}")
