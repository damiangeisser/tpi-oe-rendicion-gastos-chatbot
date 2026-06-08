"""Manejadores de comandos y mensajes del bot de rendición de gastos internos.

Cada manejador delega el acceso a datos en servicios.py y se limita a
coordinar la conversación: leer el estado actual de la solicitud, invocar al
servicio correspondiente y responder al usuario en español.
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import configuracion
import estados
import servicios
import validadores

logger = logging.getLogger(__name__)

MENSAJE_BIENVENIDA = (
    "¡Hola! Soy el bot de rendición de gastos internos.\n\n"
    "Podés iniciar una solicitud de reembolso o gestionar solicitudes pendientes, según tu rol.\n\n"
    "Ingresá tu legajo para continuar o enviá /ayuda para ver las opciones disponibles."
)

MENSAJE_AYUDA = (
    "Comandos disponibles:\n\n"
    "/start - Identificarte e iniciar el flujo según tu rol.\n"
    "/cancelar - Cancelar tu solicitud actual.\n"
    "/pendientes - Ver solicitudes pendientes de revisión si sos supervisor.\n"
    "/aprobar LEGAJO - Aprobar una solicitud pendiente.\n"
    "/rechazar LEGAJO MOTIVO - Rechazar una solicitud pendiente indicando el motivo.\n"
    "/finalizar - Finalizar la sesión actual para identificarte nuevamente."
)

MENSAJE_SUPERVISOR_IDENTIFICADO = (
    "Hola, {nombre}. Identificamos tu usuario como supervisor. "
    "Podés enviar /pendientes para consultar solicitudes pendientes de revisión."
)

MENSAJE_NO_AUTORIZADO_SUPERVISOR = (
    "Para usar esta función, primero identificate como supervisor enviando /start y luego tu legajo."
)

MENSAJE_APROBAR_FALTA_LEGAJO = "Indicá el legajo del empleado. Ejemplo: /aprobar E1001."

MENSAJE_RECHAZAR_FALTA_LEGAJO = (
    "Indicá el legajo del empleado y el motivo del rechazo. "
    "Ejemplo: /rechazar E1001 El comprobante no corresponde al gasto informado."
)

MENSAJE_RECHAZO_FALTA_MOTIVO = (
    "Indicá el motivo del rechazo. Ejemplo: /rechazar E1001 El comprobante no corresponde al gasto informado."
)

MENSAJE_SOLICITUD_PENDIENTE_NO_ENCONTRADA = "No se encontró una solicitud pendiente de revisión para ese legajo."

MENSAJE_SOLICITUDES_PENDIENTES_AMBIGUAS = (
    "Se encontró más de una solicitud pendiente para ese legajo. No se puede resolver automáticamente."
)

MENSAJE_SOLICITUD_APROBADA_CONFIRMACION_SUPERVISOR = "La solicitud del legajo {legajo} fue aprobada correctamente."

MENSAJE_SOLICITUD_APROBADA_NOTIFICACION_EMPLEADO = (
    "Tu solicitud fue aprobada por el supervisor. El reintegro quedó registrado para su gestión. "
    "Podés enviar /start para iniciar una nueva solicitud."
)

MENSAJE_SOLICITUD_RECHAZADA_CONFIRMACION_SUPERVISOR = "La solicitud del legajo {legajo} fue rechazada correctamente."

MENSAJE_SOLICITUD_RECHAZADA_NOTIFICACION_EMPLEADO = (
    "Tu solicitud fue rechazada por el supervisor.\n\n"
    "Motivo:\n{motivo}\n\n"
    "Podés enviar /start para iniciar una nueva solicitud."
)

MENSAJE_FINALIZAR_SOLICITUD_EN_CURSO = "Tenés una solicitud en curso. Para finalizarla, primero enviá /cancelar."

MENSAJE_FINALIZAR_SESION_FINALIZADA = "Sesión finalizada correctamente. Podés enviar /start para identificarte nuevamente."

MENSAJE_FINALIZAR_CON_REVISION_PENDIENTE = (
    "Sesión finalizada correctamente. La solicitud pendiente seguirá en revisión. "
    "Podés enviar /start para identificarte nuevamente."
)

MENSAJE_FINALIZAR_SIN_SESION_ACTIVA = "No tenés una sesión activa. Podés enviar /start para identificarte."

MENSAJE_SOLICITUD_EN_CURSO = "Ya tenés una solicitud en curso. Continuemos donde la dejamos."

MENSAJE_PEDIR_LEGAJO = "Para comenzar, indicame tu número de legajo."

MENSAJE_LEGAJO_INVALIDO = (
    "No pudimos validar tu legajo: no corresponde a un empleado activo habilitado.\n"
    "La solicitud fue cancelada. Si creés que se trata de un error, comunicate con tu área de Recursos Humanos."
)

MENSAJE_LEGAJO_VALIDO = "¡Hola, {nombre} {apellido}! Validamos tu legajo correctamente."

MENSAJE_LEGAJO_DEBE_SER_TEXTO = "Ingresá tu legajo como texto."

MENSAJE_PEDIR_CATEGORIA = "Elegí la categoría del gasto que querés rendir:"

MENSAJE_CATEGORIA_REGISTRADA = "Categoría registrada: {categoria}."

MENSAJE_CATEGORIA_NO_DISPONIBLE = (
    "Esa categoría ya no está disponible. Por favor, elegí una de las opciones vigentes."
)

MENSAJE_ACCION_NO_ESPERADA = "Esa acción no corresponde en este momento de tu solicitud."

MENSAJE_PEDIR_FECHA = "Ingresá la fecha del gasto en formato DD/MM/AAAA."

MENSAJE_FECHA_REGISTRADA = "Fecha registrada: {fecha}."

MENSAJE_FECHA_INVALIDA_REINTENTAR = (
    "La fecha ingresada no es válida. Usá el formato DD/MM/AAAA. Intentos restantes: {restantes}."
)

MENSAJE_SOLICITUD_CANCELADA_POR_INTENTOS_FECHA = (
    "La solicitud fue cancelada porque se alcanzó la cantidad máxima de intentos para ingresar una fecha válida."
)

MENSAJE_PEDIR_MONTO = "Ingresá el monto del gasto."

MENSAJE_MONTO_REGISTRADO = "Monto registrado: ${monto}."

MENSAJE_MONTO_INVALIDO_REINTENTAR = (
    "El monto ingresado no es válido. Ingresá un número positivo. Intentos restantes: {restantes}."
)

MENSAJE_SOLICITUD_CANCELADA_POR_INTENTOS_MONTO = (
    "La solicitud fue cancelada porque se alcanzó la cantidad máxima de intentos para ingresar un monto válido."
)

MENSAJE_PEDIR_COMPROBANTE = "Enviá el comprobante del gasto en formato JPG."

MENSAJE_COMPROBANTE_INVALIDO_REINTENTAR = (
    "El comprobante no es válido. Tenés que enviar un archivo JPG que no supere el tamaño máximo permitido. "
    "Intentos restantes: {restantes}."
)

MENSAJE_SOLICITUD_CANCELADA_POR_INTENTOS_COMPROBANTE = (
    "La solicitud fue cancelada porque se alcanzó la cantidad máxima de intentos para enviar un comprobante válido."
)

MENSAJE_USAR_START = "No tenés una solicitud activa. Enviá /start para iniciar una rendición de gastos."

MENSAJE_SOLICITUD_PENDIENTE_DE_RESOLUCION = (
    "Ya contamos con todos los datos necesarios para esta solicitud. Te informaremos cuando sea resuelta. "
    "Podés enviar /cancelar para cancelar la solicitud actual o /finalizar para cerrar la sesión."
)

MENSAJE_SOLICITUD_PENDIENTE_DE_RESOLUCION_INICIO = (
    "Ya existe una solicitud pendiente de resolución. Te informaremos cuando sea resuelta. "
    "Podés enviar /cancelar para cancelar la solicitud actual o /finalizar para cerrar la sesión."
)

MENSAJE_SOLICITUD_DERIVADA_PENDIENTE_INICIO = (
    "Ya existe una solicitud pendiente de resolución. Te informaremos cuando sea resuelta. "
    "Podés enviar /cancelar para cancelar la solicitud actual o /finalizar para cerrar la sesión."
)

MENSAJE_ESPERANDO_PROXIMO_PASO = (
    "Tu solicitud está en curso. En una próxima etapa continuaremos con los siguientes pasos."
)

MENSAJE_SIN_SOLICITUD_ACTIVA = "No tenés una solicitud activa para cancelar."

MENSAJE_SOLICITUD_CANCELADA_POR_USUARIO = "Tu solicitud fue cancelada. Si querés iniciar una nueva, enviá /start."

MENSAJE_SOLICITUD_PENDIENTE_CANCELADA = (
    "La solicitud fue cancelada correctamente. Podés enviar /start para iniciar una nueva solicitud."
)

MOTIVO_CANCELACION_LEGAJO_INVALIDO = "Legajo inválido o usuario no habilitado."

MOTIVO_CANCELACION_POR_USUARIO = "El usuario canceló la solicitud mediante el comando /cancelar."

MOTIVO_CANCELACION_SOLICITUD_PENDIENTE = "Solicitud cancelada por el usuario."

MOTIVO_CANCELACION_INTENTOS_FECHA = "Cantidad máxima de intentos alcanzada al ingresar la fecha del gasto."

MOTIVO_CANCELACION_INTENTOS_MONTO = "Cantidad máxima de intentos alcanzada al ingresar el monto del gasto."

MOTIVO_CANCELACION_INTENTOS_COMPROBANTE = "Cantidad máxima de intentos alcanzada al enviar el comprobante."

def _obtener_telegram_user_id(update: Update) -> str:
    """Extrae el identificador del usuario de Telegram como texto, tal como se almacena en la base."""
    return str(update.effective_user.id)


def es_mensaje_texto(update: Update) -> bool:
    """Indica si el mensaje recibido contiene texto.

    Telegram entrega los mensajes de solo emojis como texto, por lo que
    también se consideran mensajes de texto a los efectos de esta función;
    su validez como legajo, fecha o monto la determina el validador
    correspondiente.
    """
    mensaje = update.effective_message
    return mensaje is not None and mensaje.text is not None


def _obtener_solicitud_pendiente_resolucion(telegram_user_id: str):
    """Devuelve la última solicitud del usuario si ya tiene todos los datos y espera resolución.

    Permite distinguir el caso de una persona que ya completó su solicitud
    (comprobante recibido, conversación finalizada, pero todavía en curso
    administrativamente) de quien simplemente no tiene ninguna solicitud.
    """
    ultima_solicitud = servicios.obtener_ultima_solicitud_por_telegram(telegram_user_id)
    if ultima_solicitud is not None and servicios.solicitud_tiene_datos_completos_pendiente_resolucion(ultima_solicitud):
        return ultima_solicitud
    return None


def _obtener_solicitud_pendiente_revision_supervisor(telegram_user_id: str):
    """Devuelve la solicitud activa del usuario si está derivada y a la espera de revisión del supervisor.

    Permite distinguir, entre las solicitudes activas de la cuenta, la que ya
    no requiere ninguna acción de carga por parte de la persona empleada
    porque quedó en manos de un supervisor para su revisión.
    """
    solicitud = servicios.obtener_solicitud_activa_por_telegram(telegram_user_id)
    if (
        solicitud is not None
        and solicitud["estado_solicitud_codigo"] == estados.ESTADO_SOLICITUD_DERIVADA_SUPERVISOR
        and solicitud["estado_conversacion_codigo"] == estados.ESTADO_CONVERSACION_ESPERANDO_REVISION_SUPERVISOR
    ):
        return solicitud
    return None


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


async def _solicitar_monto(update: Update) -> None:
    """Envía el mensaje pidiendo el monto del gasto."""
    await update.effective_message.reply_text(MENSAJE_PEDIR_MONTO)


async def _solicitar_comprobante(update: Update) -> None:
    """Envía el mensaje pidiendo el comprobante del gasto en formato JPG."""
    await update.effective_message.reply_text(MENSAJE_PEDIR_COMPROBANTE)


async def _continuar_segun_estado(update: Update, solicitud) -> None:
    """Retoma la conversación según el estado de conversación actual de la solicitud."""
    estado_conversacion = solicitud["estado_conversacion_codigo"]

    if estado_conversacion == estados.ESTADO_CONVERSACION_ESPERANDO_LEGAJO:
        await _solicitar_legajo(update)
    elif estado_conversacion == estados.ESTADO_CONVERSACION_ESPERANDO_CATEGORIA:
        await _solicitar_categoria(update)
    elif estado_conversacion == estados.ESTADO_CONVERSACION_ESPERANDO_FECHA:
        await _solicitar_fecha(update)
    elif estado_conversacion == estados.ESTADO_CONVERSACION_ESPERANDO_MONTO:
        await _solicitar_monto(update)
    elif estado_conversacion == estados.ESTADO_CONVERSACION_ESPERANDO_COMPROBANTE:
        await _solicitar_comprobante(update)
    else:
        await update.effective_message.reply_text(MENSAJE_ESPERANDO_PROXIMO_PASO)


async def _procesar_legajo(update: Update, solicitud) -> None:
    """Valida el legajo recibido y continúa según el rol de la persona identificada.

    El legajo debe llegar como texto. Cualquier otro tipo de mensaje (foto,
    documento, sticker, etc.) se trata como legajo inválido y cancela la
    solicitud, igual que un legajo que no corresponde a un usuario activo
    habilitado. Un legajo válido vincula la cuenta de Telegram con el usuario
    interno: si pertenece a un empleado, la solicitud de reembolso continúa;
    si pertenece a un supervisor, se lo identifica para la gestión de
    revisiones y se elimina la solicitud creada al iniciar la conversación,
    ya que nunca llegó a representar un pedido de reembolso real.
    """
    mensaje = update.effective_message

    if not es_mensaje_texto(update):
        servicios.cancelar_solicitud(solicitud["id"], MOTIVO_CANCELACION_LEGAJO_INVALIDO)
        await mensaje.reply_text(MENSAJE_LEGAJO_DEBE_SER_TEXTO)
        return

    legajo = mensaje.text.strip()
    usuario = servicios.buscar_usuario_activo_por_legajo(legajo)

    if usuario is None:
        servicios.cancelar_solicitud(solicitud["id"], MOTIVO_CANCELACION_LEGAJO_INVALIDO)
        await mensaje.reply_text(MENSAJE_LEGAJO_INVALIDO)
        return

    telegram_user_id = _obtener_telegram_user_id(update)
    servicios.vincular_usuario_telegram(usuario["id"], telegram_user_id)

    if usuario["rol_codigo"] == estados.ROL_SUPERVISOR:
        servicios.eliminar_solicitud(solicitud["id"])
        await mensaje.reply_text(MENSAJE_SUPERVISOR_IDENTIFICADO.format(nombre=usuario["nombre"]))
        return

    servicios.registrar_legajo_valido(solicitud["id"], usuario["id"])
    await mensaje.reply_text(
        MENSAJE_LEGAJO_VALIDO.format(nombre=usuario["nombre"], apellido=usuario["apellido"])
    )
    await _solicitar_categoria(update)


async def _procesar_fecha(update: Update, solicitud) -> None:
    """Valida la fecha del gasto recibida y avanza, reintenta o cancela la solicitud según el resultado.

    La validación realizada acá se limita al formato y a que la fecha exista
    en el calendario. Las reglas de negocio sobre qué fechas son aceptables
    (por ejemplo, que correspondan al mes en curso) se aplican más adelante,
    durante la validación de la política de gastos. Cualquier mensaje que no
    sea de texto (foto, sticker, etc.) se trata como una fecha vacía, lo que
    cuenta como un intento inválido más, con la misma lógica de reintentos.
    """
    mensaje = update.effective_message
    texto_fecha = mensaje.text.strip() if es_mensaje_texto(update) else ""

    try:
        fecha_gasto = validadores.validar_fecha_gasto(texto_fecha)
    except ValueError:
        intentos = servicios.incrementar_intentos_fecha(solicitud["id"])

        if intentos >= estados.MAX_INTENTOS_VALIDACION:
            servicios.cancelar_solicitud(solicitud["id"], MOTIVO_CANCELACION_INTENTOS_FECHA)
            await mensaje.reply_text(MENSAJE_SOLICITUD_CANCELADA_POR_INTENTOS_FECHA)
            return

        restantes = estados.MAX_INTENTOS_VALIDACION - intentos
        await mensaje.reply_text(MENSAJE_FECHA_INVALIDA_REINTENTAR.format(restantes=restantes))
        return

    servicios.registrar_fecha_solicitud(solicitud["id"], fecha_gasto)
    confirmacion = MENSAJE_FECHA_REGISTRADA.format(fecha=fecha_gasto.strftime("%d/%m/%Y"))
    await mensaje.reply_text(f"{confirmacion} {MENSAJE_PEDIR_MONTO}")


async def _procesar_monto(update: Update, solicitud) -> None:
    """Valida el monto del gasto recibido y avanza, reintenta o cancela la solicitud según el resultado.

    La validación realizada acá se limita a que el monto sea un número
    positivo bien formado. La comparación contra el monto máximo permitido
    por la política de gastos se realiza más adelante, durante la validación
    de la política, luego de validar el comprobante. Cualquier mensaje que no
    sea de texto (foto, sticker, etc.) se trata como un monto vacío, lo que
    cuenta como un intento inválido más, con la misma lógica de reintentos.
    """
    mensaje = update.effective_message
    texto_monto = mensaje.text.strip() if es_mensaje_texto(update) else ""

    try:
        monto = validadores.validar_monto_gasto(texto_monto)
    except ValueError:
        intentos = servicios.incrementar_intentos_monto(solicitud["id"])

        if intentos >= estados.MAX_INTENTOS_VALIDACION:
            servicios.cancelar_solicitud(solicitud["id"], MOTIVO_CANCELACION_INTENTOS_MONTO)
            await mensaje.reply_text(MENSAJE_SOLICITUD_CANCELADA_POR_INTENTOS_MONTO)
            return

        restantes = estados.MAX_INTENTOS_VALIDACION - intentos
        await mensaje.reply_text(MENSAJE_MONTO_INVALIDO_REINTENTAR.format(restantes=restantes))
        return

    servicios.registrar_monto_solicitud(solicitud["id"], monto)
    confirmacion = MENSAJE_MONTO_REGISTRADO.format(monto=f"{monto:.2f}")
    await mensaje.reply_text(f"{confirmacion} {MENSAJE_PEDIR_COMPROBANTE}")


def _validar_comprobante_recibido(mensaje) -> str:
    """Extrae el identificador del comprobante recibido y valida sus requisitos técnicos.

    Acepta fotos (mensaje.photo) y documentos (mensaje.document) en formato
    JPG/JPEG, validando lo que Telegram informe disponible sobre nombre de
    archivo, tipo MIME y tamaño. No descarga el archivo: solo inspecciona los
    metadatos que vienen incluidos en el mensaje. Devuelve el file_id si el
    comprobante cumple los requisitos técnicos; lanza ValueError con un
    mensaje en español en caso contrario.
    """
    if mensaje.photo:
        foto_mas_grande = mensaje.photo[-1]
        if foto_mas_grande.file_size is not None:
            validadores.validar_tamano_archivo(foto_mas_grande.file_size, configuracion.MAX_COMPROBANTE_SIZE_BYTES)
        else:
            logger.info("La foto recibida como comprobante no informó su tamaño; se valida solo lo disponible.")
        return foto_mas_grande.file_id

    if mensaje.document:
        documento = mensaje.document

        if not documento.file_name and not documento.mime_type:
            raise ValueError("No se pudo determinar el formato del archivo enviado. Debe enviar un archivo JPG.")

        if documento.file_name:
            validadores.validar_nombre_archivo_jpg(documento.file_name)
        if documento.mime_type:
            validadores.validar_mime_type_jpg(documento.mime_type)

        if documento.file_size is not None:
            validadores.validar_tamano_archivo(documento.file_size, configuracion.MAX_COMPROBANTE_SIZE_BYTES)
        else:
            logger.info("El documento recibido como comprobante no informó su tamaño; se valida solo lo disponible.")

        return documento.file_id

    raise ValueError("Debe enviar el comprobante como una foto o un archivo JPG.")


async def _procesar_comprobante(update: Update, solicitud) -> None:
    """Valida el comprobante recibido y, si es válido, resuelve la solicitud.

    Esta etapa verifica los requisitos técnicos del archivo (formato JPG y
    tamaño máximo permitido), reintenta o cancela la solicitud según el
    resultado igual que las demás validaciones, y si el comprobante es válido
    no se limita a guardarlo: ya se cuenta con todos los datos necesarios, así
    que a continuación se simula la validación por OCR y se aplica la
    política de gastos para resolver la solicitud (aprobación automática,
    derivación a supervisor o cancelación), informando a la persona usuaria
    del resultado final.
    """
    mensaje = update.effective_message

    try:
        comprobante_file_id = _validar_comprobante_recibido(mensaje)
    except ValueError:
        intentos = servicios.incrementar_intentos_comprobante(solicitud["id"])

        if intentos >= estados.MAX_INTENTOS_VALIDACION:
            servicios.cancelar_solicitud(solicitud["id"], MOTIVO_CANCELACION_INTENTOS_COMPROBANTE)
            await mensaje.reply_text(MENSAJE_SOLICITUD_CANCELADA_POR_INTENTOS_COMPROBANTE)
            return

        restantes = estados.MAX_INTENTOS_VALIDACION - intentos
        await mensaje.reply_text(MENSAJE_COMPROBANTE_INVALIDO_REINTENTAR.format(restantes=restantes))
        return

    servicios.registrar_comprobante_solicitud(solicitud["id"], comprobante_file_id)
    servicios.registrar_validacion_ocr_simulada(solicitud["id"])
    mensaje_resultado = servicios.validar_politica_y_resolver_solicitud(solicitud["id"])
    await mensaje.reply_text(mensaje_resultado)


async def manejar_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inicia una nueva solicitud o retoma la situación vigente de la cuenta de Telegram, según corresponda.

    La sesión de identidad (usuarios_telegram) es la que determina si hay
    algo para retomar: sin un vínculo activo, /start siempre vuelve a pedir
    el legajo, sin importar el historial de solicitudes de la cuenta, ya que
    /finalizar pudo haber cerrado la sesión sin cancelar ni modificar ninguna
    solicitud (por ejemplo, una derivada que sigue a la espera de revisión).
    """
    telegram_user_id = _obtener_telegram_user_id(update)

    if servicios.obtener_vinculo_telegram_activo(telegram_user_id) is not None:
        solicitud_en_carga = servicios.obtener_solicitud_en_carga_por_telegram(telegram_user_id)
        if solicitud_en_carga is not None:
            await update.message.reply_text(MENSAJE_SOLICITUD_EN_CURSO)
            await _continuar_segun_estado(update, solicitud_en_carga)
            return

        if _obtener_solicitud_pendiente_revision_supervisor(telegram_user_id) is not None:
            await update.message.reply_text(MENSAJE_SOLICITUD_DERIVADA_PENDIENTE_INICIO)
            return

        if _obtener_solicitud_pendiente_resolucion(telegram_user_id) is not None:
            await update.message.reply_text(MENSAJE_SOLICITUD_PENDIENTE_DE_RESOLUCION_INICIO)
            return

    await update.message.reply_text(MENSAJE_BIENVENIDA)
    servicios.crear_solicitud_inicial(telegram_user_id)
    await _solicitar_legajo(update)


async def manejar_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde al comando /ayuda con la lista de comandos disponibles."""
    await update.message.reply_text(MENSAJE_AYUDA)


async def manejar_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancela la solicitud activa del usuario, o la pendiente de resolución si no hay ninguna activa.

    Una solicitud que ya recibió todos sus datos (conversación finalizada,
    comprobante cargado) deja de estar "activa" pero sigue en curso a nivel
    administrativo a la espera de que alguien la resuelva. La persona usuaria
    también debe poder cancelarla mientras tanto.
    """
    telegram_user_id = _obtener_telegram_user_id(update)
    solicitud = servicios.obtener_solicitud_activa_por_telegram(telegram_user_id)

    if solicitud is not None:
        servicios.cancelar_solicitud(solicitud["id"], MOTIVO_CANCELACION_POR_USUARIO)
        await update.message.reply_text(MENSAJE_SOLICITUD_CANCELADA_POR_USUARIO)
        return

    solicitud_pendiente = _obtener_solicitud_pendiente_resolucion(telegram_user_id)
    if solicitud_pendiente is not None:
        servicios.cancelar_solicitud(solicitud_pendiente["id"], MOTIVO_CANCELACION_SOLICITUD_PENDIENTE)
        await update.message.reply_text(MENSAJE_SOLICITUD_PENDIENTE_CANCELADA)
        return

    await update.message.reply_text(MENSAJE_SIN_SOLICITUD_ACTIVA)


async def manejar_finalizar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cierra la sesión de identidad de Telegram sin afectar ninguna solicitud.

    A diferencia de /cancelar, que actúa sobre una solicitud, /finalizar actúa
    sobre el vínculo usuarios_telegram: permite que la cuenta vuelva a
    identificarse desde cero mediante /start. No cancela ni modifica
    solicitudes, salvo para impedir el cierre mientras se están cargando datos,
    ya que en ese caso la persona quedaría sin forma de continuar completándola.
    """
    telegram_user_id = _obtener_telegram_user_id(update)

    if servicios.usuario_tiene_solicitud_en_carga(telegram_user_id):
        await update.message.reply_text(MENSAJE_FINALIZAR_SOLICITUD_EN_CURSO)
        return

    if servicios.obtener_vinculo_telegram_activo(telegram_user_id) is None:
        await update.message.reply_text(MENSAJE_FINALIZAR_SIN_SESION_ACTIVA)
        return

    tiene_revision_pendiente = _obtener_solicitud_pendiente_revision_supervisor(telegram_user_id) is not None

    servicios.desactivar_vinculo_telegram(telegram_user_id)

    if tiene_revision_pendiente:
        await update.message.reply_text(MENSAJE_FINALIZAR_CON_REVISION_PENDIENTE)
    else:
        await update.message.reply_text(MENSAJE_FINALIZAR_SESION_FINALIZADA)


async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enruta cualquier mensaje (texto, foto, documento, sticker, etc.) según el estado de la solicitud.

    Todos los tipos de mensaje pasan por esta misma función para que la
    máquina de estados de la conversación sea una sola: tanto el texto como
    los archivos y otros contenidos multimedia pueden corresponder a un dato
    esperado (legajo, fecha, monto o comprobante) según en qué paso esté la
    solicitud, y cada _procesar_* sabe cómo tratar un mensaje que no es del
    tipo esperado.
    """
    telegram_user_id = _obtener_telegram_user_id(update)
    solicitud = servicios.obtener_solicitud_activa_por_telegram(telegram_user_id)

    if solicitud is None:
        if _obtener_solicitud_pendiente_resolucion(telegram_user_id) is not None:
            await update.effective_message.reply_text(MENSAJE_SOLICITUD_PENDIENTE_DE_RESOLUCION)
        else:
            await update.effective_message.reply_text(MENSAJE_USAR_START)
        return

    estado_conversacion = solicitud["estado_conversacion_codigo"]

    if estado_conversacion == estados.ESTADO_CONVERSACION_ESPERANDO_LEGAJO:
        await _procesar_legajo(update, solicitud)
        return

    if estado_conversacion == estados.ESTADO_CONVERSACION_ESPERANDO_FECHA:
        await _procesar_fecha(update, solicitud)
        return

    if estado_conversacion == estados.ESTADO_CONVERSACION_ESPERANDO_MONTO:
        await _procesar_monto(update, solicitud)
        return

    if estado_conversacion == estados.ESTADO_CONVERSACION_ESPERANDO_COMPROBANTE:
        await _procesar_comprobante(update, solicitud)
        return

    await update.effective_message.reply_text(MENSAJE_ESPERANDO_PROXIMO_PASO)


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


async def _obtener_supervisor_autorizado(update: Update):
    """Verifica que quien envía un comando de supervisor esté identificado como tal.

    Devuelve el usuario supervisor activo vinculado a la cuenta de Telegram
    que escribe, o None si no está identificado, en cuyo caso ya se le
    informó cómo identificarse.
    """
    telegram_user_id = _obtener_telegram_user_id(update)
    supervisor = servicios.obtener_supervisor_por_telegram(telegram_user_id)

    if supervisor is None:
        await update.effective_message.reply_text(MENSAJE_NO_AUTORIZADO_SUPERVISOR)

    return supervisor


async def manejar_pendientes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde al comando /pendientes con el listado de solicitudes pendientes de revisión, identificadas por legajo."""
    supervisor = await _obtener_supervisor_autorizado(update)
    if supervisor is None:
        return

    await update.effective_message.reply_text(servicios.construir_mensaje_pendientes_revision())


async def manejar_aprobar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde al comando /aprobar LEGAJO aprobando, si corresponde, la solicitud pendiente de ese empleado."""
    supervisor = await _obtener_supervisor_autorizado(update)
    if supervisor is None:
        return

    if not context.args:
        await update.effective_message.reply_text(MENSAJE_APROBAR_FALTA_LEGAJO)
        return

    legajo = context.args[0].strip()
    solicitudes_pendientes = servicios.buscar_solicitudes_pendientes_por_legajo(legajo)

    if not solicitudes_pendientes:
        await update.effective_message.reply_text(MENSAJE_SOLICITUD_PENDIENTE_NO_ENCONTRADA)
        return

    if len(solicitudes_pendientes) > 1:
        await update.effective_message.reply_text(MENSAJE_SOLICITUDES_PENDIENTES_AMBIGUAS)
        return

    solicitud = solicitudes_pendientes[0]
    servicios.aprobar_solicitud_por_supervisor(solicitud["id"], supervisor["id"])

    await update.effective_message.reply_text(MENSAJE_SOLICITUD_APROBADA_CONFIRMACION_SUPERVISOR.format(legajo=legajo))
    await context.bot.send_message(
        chat_id=int(solicitud["telegram_user_id"]),
        text=MENSAJE_SOLICITUD_APROBADA_NOTIFICACION_EMPLEADO,
    )


async def manejar_rechazar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde al comando /rechazar LEGAJO MOTIVO rechazando, si corresponde, la solicitud pendiente de ese empleado."""
    supervisor = await _obtener_supervisor_autorizado(update)
    if supervisor is None:
        return

    if not context.args:
        await update.effective_message.reply_text(MENSAJE_RECHAZAR_FALTA_LEGAJO)
        return

    if len(context.args) < 2:
        await update.effective_message.reply_text(MENSAJE_RECHAZO_FALTA_MOTIVO)
        return

    legajo = context.args[0].strip()
    motivo_rechazo = " ".join(context.args[1:]).strip()
    solicitudes_pendientes = servicios.buscar_solicitudes_pendientes_por_legajo(legajo)

    if not solicitudes_pendientes:
        await update.effective_message.reply_text(MENSAJE_SOLICITUD_PENDIENTE_NO_ENCONTRADA)
        return

    if len(solicitudes_pendientes) > 1:
        await update.effective_message.reply_text(MENSAJE_SOLICITUDES_PENDIENTES_AMBIGUAS)
        return

    solicitud = solicitudes_pendientes[0]
    servicios.rechazar_solicitud_por_supervisor(solicitud["id"], supervisor["id"], motivo_rechazo)

    await update.effective_message.reply_text(MENSAJE_SOLICITUD_RECHAZADA_CONFIRMACION_SUPERVISOR.format(legajo=legajo))
    await context.bot.send_message(
        chat_id=int(solicitud["telegram_user_id"]),
        text=MENSAJE_SOLICITUD_RECHAZADA_NOTIFICACION_EMPLEADO.format(motivo=motivo_rechazo),
    )
