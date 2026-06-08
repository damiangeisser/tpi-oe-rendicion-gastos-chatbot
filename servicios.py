"""Capa de servicios: encapsula el acceso a datos del flujo de rendición de gastos.

Cada función abre su propia conexión mediante obtener_conexion(), realiza una
unidad de trabajo completa (consulta o transacción) y cierra la conexión. Así
los manejadores de Telegram no necesitan conocer detalles de SQL ni de SQLite.
"""

import logging
import sqlite3
import uuid
from datetime import date, datetime

import base_datos
import estados

logger = logging.getLogger(__name__)


def _ahora() -> str:
    """Devuelve la fecha y hora actual en formato ISO con precisión de segundos."""
    return datetime.now().isoformat(timespec="seconds")


def _determinar_modificado_por(conexion: sqlite3.Connection, solicitud_id: str) -> str | None:
    """Determina quién debe figurar como modificador de la solicitud.

    Si ya se identificó al solicitante, es esa persona quien realiza la
    acción; en caso contrario, se utiliza el usuario Sistema como respaldo.
    """
    fila_solicitud = conexion.execute(
        "SELECT solicitante_id FROM solicitudes WHERE id = ?;", (solicitud_id,)
    ).fetchone()
    solicitante_id = fila_solicitud["solicitante_id"] if fila_solicitud is not None else None
    if solicitante_id is not None:
        return solicitante_id

    fila_sistema = conexion.execute(
        "SELECT id FROM usuarios WHERE rol_codigo = ? AND activo = 1 LIMIT 1;",
        (estados.ROL_SISTEMA,),
    ).fetchone()
    return fila_sistema["id"] if fila_sistema is not None else None


def obtener_usuario_sistema() -> sqlite3.Row | None:
    """Busca el usuario de rol Sistema, utilizado como creador/modificador de registros automáticos."""
    conexion = base_datos.obtener_conexion()
    try:
        return conexion.execute(
            "SELECT * FROM usuarios WHERE rol_codigo = ? AND activo = 1 LIMIT 1;",
            (estados.ROL_SISTEMA,),
        ).fetchone()
    finally:
        conexion.close()


def vincular_usuario_telegram(usuario_id: str, telegram_user_id: str) -> None:
    """Crea o actualiza el vínculo entre un usuario interno y su cuenta de Telegram.

    En este prototipo la relación es estrictamente uno a uno (ambas columnas
    son UNIQUE): una cuenta de Telegram corresponde a un único usuario interno
    y viceversa. Por eso, antes de fijar el nuevo par, se eliminan los
    vínculos existentes que choquen con él en cualquiera de sus dos columnas
    (por ejemplo, si la cuenta ya estaba vinculada a otro usuario, o si el
    usuario ya estaba vinculado a otra cuenta): dejarlos activos impediría
    crear el vínculo correcto sin violar las restricciones UNIQUE. Si ya
    existía exactamente el mismo par, se reutiliza esa fila y solo se
    actualiza su fecha de modificación. El propio usuario identificado figura
    como responsable de la operación, ya que es quien valida su legajo.
    """
    ahora = _ahora()
    conexion = base_datos.obtener_conexion()
    try:
        with conexion:
            conexion.execute(
                """
                DELETE FROM usuarios_telegram
                WHERE (usuario_id = ? OR telegram_user_id = ?)
                  AND NOT (usuario_id = ? AND telegram_user_id = ?);
                """,
                (usuario_id, telegram_user_id, usuario_id, telegram_user_id),
            )

            vinculo = conexion.execute(
                "SELECT id FROM usuarios_telegram WHERE usuario_id = ? AND telegram_user_id = ?;",
                (usuario_id, telegram_user_id),
            ).fetchone()

            if vinculo is not None:
                conexion.execute(
                    """
                    UPDATE usuarios_telegram
                    SET activo = 1,
                        modificado_por = ?,
                        modificado_en = ?
                    WHERE id = ?;
                    """,
                    (usuario_id, ahora, vinculo["id"]),
                )
            else:
                conexion.execute(
                    """
                    INSERT INTO usuarios_telegram (
                        id, usuario_id, telegram_user_id, activo,
                        creado_por, modificado_por, creado_en, modificado_en
                    ) VALUES (?, ?, ?, 1, ?, ?, ?, ?);
                    """,
                    (str(uuid.uuid4()), usuario_id, telegram_user_id, usuario_id, usuario_id, ahora, ahora),
                )
    finally:
        conexion.close()


def obtener_usuario_por_telegram(telegram_user_id: str) -> sqlite3.Row | None:
    """Busca el usuario interno activo vinculado a una cuenta de Telegram, si existe."""
    conexion = base_datos.obtener_conexion()
    try:
        return conexion.execute(
            """
            SELECT usuario.*
            FROM usuarios_telegram AS vinculo
            JOIN usuarios AS usuario ON usuario.id = vinculo.usuario_id
            WHERE vinculo.telegram_user_id = ?
              AND vinculo.activo = 1
              AND usuario.activo = 1
            LIMIT 1;
            """,
            (telegram_user_id,),
        ).fetchone()
    finally:
        conexion.close()


def obtener_supervisor_por_telegram(telegram_user_id: str) -> sqlite3.Row | None:
    """Busca el supervisor activo vinculado a una cuenta de Telegram, si existe."""
    usuario = obtener_usuario_por_telegram(telegram_user_id)
    if usuario is not None and usuario["rol_codigo"] == estados.ROL_SUPERVISOR:
        return usuario
    return None


def usuario_es_supervisor_telegram(telegram_user_id: str) -> bool:
    """Indica si la cuenta de Telegram está vinculada a un supervisor activo."""
    return obtener_supervisor_por_telegram(telegram_user_id) is not None


def obtener_vinculo_telegram_activo(telegram_user_id: str) -> sqlite3.Row | None:
    """Busca el vínculo activo entre una cuenta de Telegram y un usuario interno, si existe.

    A diferencia de obtener_usuario_por_telegram, devuelve la fila de
    usuarios_telegram (no la del usuario interno): sirve para saber si la
    cuenta de Telegram tiene una sesión de identidad abierta, sin importar
    si el usuario vinculado sigue activo.
    """
    conexion = base_datos.obtener_conexion()
    try:
        return conexion.execute(
            "SELECT * FROM usuarios_telegram WHERE telegram_user_id = ? AND activo = 1 LIMIT 1;",
            (telegram_user_id,),
        ).fetchone()
    finally:
        conexion.close()


def desactivar_vinculo_telegram(telegram_user_id: str) -> None:
    """Cierra la sesión de identidad de una cuenta de Telegram desactivando su vínculo, sin eliminarlo.

    Permite que la cuenta vuelva a identificarse desde cero mediante /start
    sin perder el historial del vínculo anterior. El propio usuario vinculado
    queda registrado como responsable del cierre, ya que es quien decide
    finalizar su sesión.
    """
    ahora = _ahora()
    conexion = base_datos.obtener_conexion()
    try:
        with conexion:
            vinculo = conexion.execute(
                "SELECT * FROM usuarios_telegram WHERE telegram_user_id = ? AND activo = 1 LIMIT 1;",
                (telegram_user_id,),
            ).fetchone()
            if vinculo is None:
                return

            conexion.execute(
                """
                UPDATE usuarios_telegram
                SET activo = 0,
                    modificado_por = ?,
                    modificado_en = ?
                WHERE id = ?;
                """,
                (vinculo["usuario_id"], ahora, vinculo["id"]),
            )
    finally:
        conexion.close()


def obtener_solicitud_activa_por_telegram(telegram_user_id: str) -> sqlite3.Row | None:
    """Busca la solicitud activa (no finalizada) del usuario de Telegram, si existe.

    Cada conversación de Telegram corresponde a una única solicitud activa,
    es decir, una solicitud cuyo estado_conversacion_codigo no es Finalizado.
    """
    conexion = base_datos.obtener_conexion()
    try:
        return conexion.execute(
            """
            SELECT * FROM solicitudes
            WHERE telegram_user_id = ?
              AND estado_conversacion_codigo != ?
            ORDER BY creado_en DESC
            LIMIT 1;
            """,
            (telegram_user_id, estados.ESTADO_CONVERSACION_FINALIZADO),
        ).fetchone()
    finally:
        conexion.close()


def obtener_solicitud_en_carga_por_telegram(telegram_user_id: str) -> sqlite3.Row | None:
    """Busca la solicitud del usuario de Telegram que todavía está cargando datos del lado del empleado, si existe.

    Una solicitud está en carga cuando sigue en curso y su conversación se
    encuentra en alguno de los pasos de relevamiento de datos (legajo,
    categoría, fecha, monto o comprobante): en esos casos, cerrar la sesión
    dejaría a la persona sin forma de continuar completándola.

    A diferencia de obtener_solicitud_activa_por_telegram, esta función
    excluye explícitamente las solicitudes derivadas a un supervisor: una vez
    derivada, la solicitud ya no requiere ninguna acción de carga por parte
    de la persona empleada, sino que queda a la espera de la revisión de otra
    persona.
    """
    conexion = base_datos.obtener_conexion()
    try:
        return conexion.execute(
            """
            SELECT * FROM solicitudes
            WHERE telegram_user_id = ?
              AND estado_solicitud_codigo = ?
              AND estado_conversacion_codigo IN (?, ?, ?, ?, ?)
            ORDER BY creado_en DESC
            LIMIT 1;
            """,
            (
                telegram_user_id,
                estados.ESTADO_SOLICITUD_EN_CURSO,
                estados.ESTADO_CONVERSACION_ESPERANDO_LEGAJO,
                estados.ESTADO_CONVERSACION_ESPERANDO_CATEGORIA,
                estados.ESTADO_CONVERSACION_ESPERANDO_FECHA,
                estados.ESTADO_CONVERSACION_ESPERANDO_MONTO,
                estados.ESTADO_CONVERSACION_ESPERANDO_COMPROBANTE,
            ),
        ).fetchone()
    finally:
        conexion.close()


def usuario_tiene_solicitud_en_carga(telegram_user_id: str) -> bool:
    """Indica si la cuenta de Telegram tiene una solicitud activa que todavía está cargando datos."""
    return obtener_solicitud_en_carga_por_telegram(telegram_user_id) is not None


def crear_solicitud_inicial(telegram_user_id: str) -> sqlite3.Row:
    """Crea una nueva solicitud para el usuario de Telegram, a la espera del legajo.

    El creador y modificador inicial es el usuario Sistema, ya que todavía no
    se identificó a la persona solicitante.
    """
    usuario_sistema = obtener_usuario_sistema()
    creado_por = usuario_sistema["id"] if usuario_sistema is not None else None

    solicitud_id = str(uuid.uuid4())
    ahora = _ahora()

    conexion = base_datos.obtener_conexion()
    try:
        with conexion:
            conexion.execute(
                """
                INSERT INTO solicitudes (
                    id, telegram_user_id, solicitante_id, usuario_asignado_id,
                    estado_solicitud_codigo, estado_conversacion_codigo,
                    creado_por, modificado_por, creado_en, modificado_en
                ) VALUES (?, ?, NULL, NULL, ?, ?, ?, ?, ?, ?);
                """,
                (
                    solicitud_id,
                    telegram_user_id,
                    estados.ESTADO_SOLICITUD_EN_CURSO,
                    estados.ESTADO_CONVERSACION_ESPERANDO_LEGAJO,
                    creado_por,
                    creado_por,
                    ahora,
                    ahora,
                ),
            )
        return conexion.execute(
            "SELECT * FROM solicitudes WHERE id = ?;", (solicitud_id,)
        ).fetchone()
    finally:
        conexion.close()


def buscar_usuario_activo_por_legajo(legajo: str) -> sqlite3.Row | None:
    """Busca un usuario activo por legajo, sin importar su rol.

    Se utiliza para identificar a la persona que escribe al bot, ya sea
    empleado o supervisor: cada rol continúa luego por un camino distinto.
    Devuelve None si no existe ningún usuario activo con ese legajo.
    """
    conexion = base_datos.obtener_conexion()
    try:
        return conexion.execute(
            """
            SELECT * FROM usuarios
            WHERE legajo = ?
              AND activo = 1
            LIMIT 1;
            """,
            (legajo,),
        ).fetchone()
    finally:
        conexion.close()


def registrar_legajo_valido(solicitud_id: str, usuario_id: str) -> None:
    """Asocia el empleado validado a la solicitud y avanza la conversación a selección de categoría."""
    ahora = _ahora()
    conexion = base_datos.obtener_conexion()
    try:
        with conexion:
            conexion.execute(
                """
                UPDATE solicitudes
                SET solicitante_id = ?,
                    usuario_asignado_id = ?,
                    estado_conversacion_codigo = ?,
                    modificado_por = ?,
                    modificado_en = ?
                WHERE id = ?;
                """,
                (
                    usuario_id,
                    usuario_id,
                    estados.ESTADO_CONVERSACION_ESPERANDO_CATEGORIA,
                    usuario_id,
                    ahora,
                    solicitud_id,
                ),
            )
    finally:
        conexion.close()


def cancelar_solicitud(solicitud_id: str, motivo: str) -> None:
    """Cancela una solicitud, finaliza la conversación y registra el motivo de la cancelación.

    El modificador es el usuario Sistema, ya que la cancelación es una acción
    automática del chatbot (por legajo inválido, abandono u otro motivo).
    """
    usuario_sistema = obtener_usuario_sistema()
    modificado_por = usuario_sistema["id"] if usuario_sistema is not None else None
    ahora = _ahora()

    conexion = base_datos.obtener_conexion()
    try:
        with conexion:
            conexion.execute(
                """
                UPDATE solicitudes
                SET estado_solicitud_codigo = ?,
                    estado_conversacion_codigo = ?,
                    motivo_cancelacion = ?,
                    usuario_asignado_id = NULL,
                    modificado_por = ?,
                    modificado_en = ?
                WHERE id = ?;
                """,
                (
                    estados.ESTADO_SOLICITUD_CANCELADA,
                    estados.ESTADO_CONVERSACION_FINALIZADO,
                    motivo,
                    modificado_por,
                    ahora,
                    solicitud_id,
                ),
            )
    finally:
        conexion.close()


def eliminar_solicitud(solicitud_id: str) -> None:
    """Elimina una solicitud que todavía no llegó a identificar a su solicitante.

    Se utiliza cuando, durante la validación del legajo, se descubre que
    quien escribe es un supervisor: la solicitud creada al iniciar la
    conversación nunca llegó a representar un pedido de reembolso real
    (no tiene solicitante ni datos cargados), así que se elimina en lugar
    de dejarla cancelada como un registro fantasma sin dueño.
    """
    conexion = base_datos.obtener_conexion()
    try:
        with conexion:
            conexion.execute("DELETE FROM solicitudes WHERE id = ?;", (solicitud_id,))
    finally:
        conexion.close()


def listar_categorias_activas() -> list[sqlite3.Row]:
    """Devuelve las categorías de gasto activas, ordenadas por código."""
    conexion = base_datos.obtener_conexion()
    try:
        return conexion.execute(
            """
            SELECT codigo, descripcion
            FROM lookup_categorias_gasto
            WHERE activo = 1
            ORDER BY codigo;
            """
        ).fetchall()
    finally:
        conexion.close()


def obtener_categoria_activa_por_codigo(categoria_codigo: int) -> sqlite3.Row | None:
    """Busca una categoría de gasto activa por su código. Devuelve None si no existe o está inactiva."""
    conexion = base_datos.obtener_conexion()
    try:
        return conexion.execute(
            """
            SELECT * FROM lookup_categorias_gasto
            WHERE codigo = ?
              AND activo = 1
            LIMIT 1;
            """,
            (categoria_codigo,),
        ).fetchone()
    finally:
        conexion.close()


def registrar_categoria_solicitud(solicitud_id: str, categoria_codigo: int) -> None:
    """Guarda la categoría elegida y avanza la conversación a la espera de la fecha del gasto.

    El modificador registrado es el solicitante si ya fue identificado; si
    todavía no lo fue, se utiliza el usuario Sistema como respaldo.
    """
    ahora = _ahora()
    conexion = base_datos.obtener_conexion()
    try:
        modificado_por = _determinar_modificado_por(conexion, solicitud_id)

        with conexion:
            conexion.execute(
                """
                UPDATE solicitudes
                SET categoria_gasto_codigo = ?,
                    estado_conversacion_codigo = ?,
                    modificado_por = ?,
                    modificado_en = ?
                WHERE id = ?;
                """,
                (
                    categoria_codigo,
                    estados.ESTADO_CONVERSACION_ESPERANDO_FECHA,
                    modificado_por,
                    ahora,
                    solicitud_id,
                ),
            )
    finally:
        conexion.close()


def registrar_fecha_solicitud(solicitud_id: str, fecha_gasto: date) -> None:
    """Guarda la fecha del gasto y avanza la conversación a la espera del monto.

    La fecha se almacena en formato ISO (AAAA-MM-DD) y se reinicia el contador
    de intentos fallidos, ya que la validación del formato se superó.
    """
    ahora = _ahora()
    conexion = base_datos.obtener_conexion()
    try:
        modificado_por = _determinar_modificado_por(conexion, solicitud_id)

        with conexion:
            conexion.execute(
                """
                UPDATE solicitudes
                SET fecha_gasto = ?,
                    intentos_fecha = 0,
                    estado_conversacion_codigo = ?,
                    modificado_por = ?,
                    modificado_en = ?
                WHERE id = ?;
                """,
                (
                    fecha_gasto.isoformat(),
                    estados.ESTADO_CONVERSACION_ESPERANDO_MONTO,
                    modificado_por,
                    ahora,
                    solicitud_id,
                ),
            )
    finally:
        conexion.close()


def incrementar_intentos_fecha(solicitud_id: str) -> int:
    """Incrementa en uno el contador de intentos fallidos al ingresar la fecha del gasto.

    Devuelve el nuevo valor del contador, de forma que quien llama pueda
    decidir si corresponde reintentar o cancelar la solicitud.
    """
    ahora = _ahora()
    conexion = base_datos.obtener_conexion()
    try:
        modificado_por = _determinar_modificado_por(conexion, solicitud_id)

        with conexion:
            conexion.execute(
                """
                UPDATE solicitudes
                SET intentos_fecha = intentos_fecha + 1,
                    modificado_por = ?,
                    modificado_en = ?
                WHERE id = ?;
                """,
                (modificado_por, ahora, solicitud_id),
            )

        fila = conexion.execute(
            "SELECT intentos_fecha FROM solicitudes WHERE id = ?;", (solicitud_id,)
        ).fetchone()
        return fila["intentos_fecha"]
    finally:
        conexion.close()


def obtener_intentos_fecha(solicitud_id: str) -> int:
    """Devuelve la cantidad actual de intentos fallidos registrados al ingresar la fecha del gasto."""
    conexion = base_datos.obtener_conexion()
    try:
        fila = conexion.execute(
            "SELECT intentos_fecha FROM solicitudes WHERE id = ?;", (solicitud_id,)
        ).fetchone()
        return fila["intentos_fecha"] if fila is not None else 0
    finally:
        conexion.close()


def registrar_monto_solicitud(solicitud_id: str, monto: float) -> None:
    """Guarda el monto del gasto y avanza la conversación a la espera del comprobante.

    Se reinicia el contador de intentos fallidos, ya que la validación del
    monto se superó. La comparación contra el monto máximo permitido por la
    política de gastos se realiza más adelante, durante la validación de la
    política, luego de validar el comprobante.
    """
    ahora = _ahora()
    conexion = base_datos.obtener_conexion()
    try:
        modificado_por = _determinar_modificado_por(conexion, solicitud_id)

        with conexion:
            conexion.execute(
                """
                UPDATE solicitudes
                SET monto = ?,
                    intentos_monto = 0,
                    estado_conversacion_codigo = ?,
                    modificado_por = ?,
                    modificado_en = ?
                WHERE id = ?;
                """,
                (
                    monto,
                    estados.ESTADO_CONVERSACION_ESPERANDO_COMPROBANTE,
                    modificado_por,
                    ahora,
                    solicitud_id,
                ),
            )
    finally:
        conexion.close()


def incrementar_intentos_monto(solicitud_id: str) -> int:
    """Incrementa en uno el contador de intentos fallidos al ingresar el monto del gasto.

    Devuelve el nuevo valor del contador, de forma que quien llama pueda
    decidir si corresponde reintentar o cancelar la solicitud.
    """
    ahora = _ahora()
    conexion = base_datos.obtener_conexion()
    try:
        modificado_por = _determinar_modificado_por(conexion, solicitud_id)

        with conexion:
            conexion.execute(
                """
                UPDATE solicitudes
                SET intentos_monto = intentos_monto + 1,
                    modificado_por = ?,
                    modificado_en = ?
                WHERE id = ?;
                """,
                (modificado_por, ahora, solicitud_id),
            )

        fila = conexion.execute(
            "SELECT intentos_monto FROM solicitudes WHERE id = ?;", (solicitud_id,)
        ).fetchone()
        return fila["intentos_monto"]
    finally:
        conexion.close()


def registrar_comprobante_solicitud(solicitud_id: str, comprobante_file_id: str) -> None:
    """Guarda el identificador de Telegram del comprobante recibido y finaliza la conversación.

    Esta etapa solo valida los requisitos técnicos del archivo (formato JPG y
    tamaño máximo) y reinicia el contador de intentos fallidos. Con esto, ya
    se cuenta con todos los datos necesarios de la solicitud: la conversación
    se da por finalizada (no se solicita más información a la persona usuaria)
    y se libera la asignación, ya que todavía no hay nadie a cargo de
    resolverla. La solicitud en sí permanece en curso a nivel administrativo,
    porque la simulación de OCR y la validación de la política de gastos se
    realizan en etapas posteriores.
    """
    ahora = _ahora()
    conexion = base_datos.obtener_conexion()
    try:
        modificado_por = _determinar_modificado_por(conexion, solicitud_id)

        with conexion:
            conexion.execute(
                """
                UPDATE solicitudes
                SET comprobante_file_id = ?,
                    intentos_comprobante = 0,
                    estado_conversacion_codigo = ?,
                    usuario_asignado_id = NULL,
                    modificado_por = ?,
                    modificado_en = ?
                WHERE id = ?;
                """,
                (
                    comprobante_file_id,
                    estados.ESTADO_CONVERSACION_FINALIZADO,
                    modificado_por,
                    ahora,
                    solicitud_id,
                ),
            )
    finally:
        conexion.close()


def obtener_ultima_solicitud_por_telegram(telegram_user_id: str) -> sqlite3.Row | None:
    """Busca la solicitud más reciente del usuario de Telegram, sin importar su estado.

    A diferencia de obtener_solicitud_activa_por_telegram, esta función
    también puede devolver solicitudes con la conversación finalizada. Sirve
    para detectar el caso particular de una solicitud que ya recibió todos
    sus datos (conversación finalizada) pero todavía espera resolución
    administrativa.
    """
    conexion = base_datos.obtener_conexion()
    try:
        return conexion.execute(
            """
            SELECT * FROM solicitudes
            WHERE telegram_user_id = ?
            ORDER BY creado_en DESC
            LIMIT 1;
            """,
            (telegram_user_id,),
        ).fetchone()
    finally:
        conexion.close()


def solicitud_tiene_datos_completos_pendiente_resolucion(solicitud: sqlite3.Row) -> bool:
    """Indica si una solicitud ya recibió todos sus datos y espera resolución administrativa.

    Esto ocurre cuando la conversación está finalizada (ya se recibió un
    comprobante válido), pero la solicitud sigue en curso a nivel
    administrativo porque todavía nadie la resolvió.
    """
    return (
        solicitud["estado_solicitud_codigo"] == estados.ESTADO_SOLICITUD_EN_CURSO
        and solicitud["estado_conversacion_codigo"] == estados.ESTADO_CONVERSACION_FINALIZADO
        and solicitud["comprobante_file_id"] is not None
    )


def incrementar_intentos_comprobante(solicitud_id: str) -> int:
    """Incrementa en uno el contador de intentos fallidos al enviar el comprobante del gasto.

    Devuelve el nuevo valor del contador, de forma que quien llama pueda
    decidir si corresponde reintentar o cancelar la solicitud.
    """
    ahora = _ahora()
    conexion = base_datos.obtener_conexion()
    try:
        modificado_por = _determinar_modificado_por(conexion, solicitud_id)

        with conexion:
            conexion.execute(
                """
                UPDATE solicitudes
                SET intentos_comprobante = intentos_comprobante + 1,
                    modificado_por = ?,
                    modificado_en = ?
                WHERE id = ?;
                """,
                (modificado_por, ahora, solicitud_id),
            )

        fila = conexion.execute(
            "SELECT intentos_comprobante FROM solicitudes WHERE id = ?;", (solicitud_id,)
        ).fetchone()
        return fila["intentos_comprobante"]
    finally:
        conexion.close()


RESULTADO_VALIDACION_OCR_SIMULADA = (
    "Validación OCR simulada exitosa. El comprobante se considera consistente "
    "con la categoría, fecha y monto ingresados."
)

MOTIVO_CANCELACION_CATEGORIA_NO_PERMITIDA = "Categoría no permitida para el área del usuario."

MOTIVO_CANCELACION_SIN_SUPERVISOR_ACTIVO = "No existe un supervisor activo disponible para revisar la solicitud."

MOTIVO_DERIVACION_CATEGORIA_REVISION_MANUAL = "La categoría seleccionada requiere revisión manual."

MOTIVO_DERIVACION_MONTO_SUPERA_LIMITE = "El monto supera el límite de aprobación automática."

MOTIVO_DERIVACION_FECHA_FUERA_DE_MES_CORRIENTE = "La fecha del gasto no corresponde al mes corriente."

MENSAJE_SOLICITUD_APROBADA_AUTOMATICAMENTE = (
    "La solicitud fue aprobada automáticamente. El reintegro quedó registrado para su gestión. "
    "Podés enviar /start para iniciar una nueva solicitud."
)

MENSAJE_SOLICITUD_CANCELADA_SIN_SUPERVISOR = (
    "La solicitud fue cancelada porque no hay un supervisor activo disponible para revisión. "
    "Podés enviar /start para iniciar una nueva solicitud."
)


def registrar_validacion_ocr_simulada(solicitud_id: str) -> None:
    """Simula la validación por OCR del comprobante recibido y registra su resultado.

    Para no complejizar la lógica del prototipo, y dado que el objetivo del
    trabajo práctico es la automatización del proceso administrativo y no la
    implementación real de OCR, se simula la validación del comprobante. Si
    el archivo JPG superó la validación técnica, se considera que los datos
    detectados coinciden con la categoría, fecha y monto ingresados.
    """
    ahora = _ahora()
    conexion = base_datos.obtener_conexion()
    try:
        modificado_por = _determinar_modificado_por(conexion, solicitud_id)

        with conexion:
            conexion.execute(
                """
                UPDATE solicitudes
                SET validacion_ocr_simulada = 1,
                    resultado_validacion_ocr = ?,
                    modificado_por = ?,
                    modificado_en = ?
                WHERE id = ?;
                """,
                (RESULTADO_VALIDACION_OCR_SIMULADA, modificado_por, ahora, solicitud_id),
            )
    finally:
        conexion.close()


def obtener_solicitud_por_id(solicitud_id: str) -> sqlite3.Row | None:
    """Busca una solicitud por su identificador."""
    conexion = base_datos.obtener_conexion()
    try:
        return conexion.execute(
            "SELECT * FROM solicitudes WHERE id = ?;", (solicitud_id,)
        ).fetchone()
    finally:
        conexion.close()


def obtener_politica_gasto_activa(area_codigo: int, categoria_gasto_codigo: int) -> sqlite3.Row | None:
    """Busca la política de gastos activa para una combinación de área y categoría, si existe."""
    conexion = base_datos.obtener_conexion()
    try:
        return conexion.execute(
            """
            SELECT * FROM politicas_gastos
            WHERE area_codigo = ?
              AND categoria_gasto_codigo = ?
              AND activo = 1
            LIMIT 1;
            """,
            (area_codigo, categoria_gasto_codigo),
        ).fetchone()
    finally:
        conexion.close()


def obtener_supervisor_activo() -> sqlite3.Row | None:
    """Busca el primer usuario activo con rol Supervisor, utilizado para derivar solicitudes a revisión."""
    conexion = base_datos.obtener_conexion()
    try:
        return conexion.execute(
            "SELECT * FROM usuarios WHERE rol_codigo = ? AND activo = 1 LIMIT 1;",
            (estados.ROL_SUPERVISOR,),
        ).fetchone()
    finally:
        conexion.close()


def obtener_categorias_validas_por_area(area_codigo: int) -> list[str]:
    """Devuelve las descripciones de las categorías de gasto habilitadas para un área.

    Una categoría se considera habilitada para el área cuando existe una
    política de gastos activa que la vincula con esa área. Se utiliza para
    informar al usuario qué categorías sí puede rendir, cuando la elegida no
    está permitida.
    """
    conexion = base_datos.obtener_conexion()
    try:
        filas = conexion.execute(
            """
            SELECT categoria.descripcion AS descripcion
            FROM politicas_gastos AS politica
            JOIN lookup_categorias_gasto AS categoria ON categoria.codigo = politica.categoria_gasto_codigo
            WHERE politica.area_codigo = ?
              AND politica.activo = 1
              AND categoria.activo = 1
            ORDER BY categoria.descripcion;
            """,
            (area_codigo,),
        ).fetchall()
        return [fila["descripcion"] for fila in filas]
    finally:
        conexion.close()


def construir_mensaje_derivacion(motivos_derivacion: list[str]) -> str:
    """Arma el mensaje que informa la derivación a supervisor, listando todos los motivos aplicables."""
    encabezado_motivos = (
        "El motivo de la derivación fue:" if len(motivos_derivacion) == 1
        else "Los motivos de la derivación fueron:"
    )
    lista_motivos = "\n".join(f"- {motivo}" for motivo in motivos_derivacion)
    return (
        "La solicitud fue derivada al supervisor para revisión.\n\n"
        f"{encabezado_motivos}\n"
        f"{lista_motivos}\n\n"
        "Te informaremos cuando sea resuelta. Podés enviar /cancelar para cancelar la solicitud actual."
    )


def construir_mensaje_categoria_no_permitida(area: str, categoria_seleccionada: str, categorias_validas: list[str]) -> str:
    """Arma el mensaje de cancelación por categoría no permitida, detallando el área, la categoría elegida y las habilitadas."""
    if categorias_validas:
        seccion_categorias = "Categorías válidas para tu área:\n" + "\n".join(
            f"- {categoria}" for categoria in categorias_validas
        )
    else:
        seccion_categorias = "No se encontraron categorías habilitadas para tu área."

    return (
        "La solicitud fue cancelada porque la categoría seleccionada no está permitida para tu área.\n\n"
        f"Tu área: {area}\n"
        f"Categoría seleccionada: {categoria_seleccionada}\n\n"
        f"{seccion_categorias}\n\n"
        "Si tenés consultas sobre las categorías habilitadas, comunicate con tu área de Recursos Humanos.\n\n"
        "Podés enviar /start para iniciar una nueva solicitud."
    )


def fecha_pertenece_al_mes_corriente(fecha_gasto: date) -> bool:
    """Indica si la fecha del gasto corresponde al mes y año en curso."""
    hoy = datetime.now().date()
    return fecha_gasto.year == hoy.year and fecha_gasto.month == hoy.month


def _calcular_motivos_derivacion(categoria_gasto_codigo: int, monto: float, fecha_gasto: date, monto_maximo: float) -> list[str]:
    """Evalúa de forma independiente los tres motivos que obligan a derivar una solicitud a supervisor.

    Se utiliza tanto al resolver una solicitud recién cargada como al listar
    las solicitudes pendientes de revisión, ya que estas últimas no
    almacenan los motivos de derivación y deben recalcularse aplicando la
    misma política vigente para la categoría del área.
    """
    motivos = []
    if categoria_gasto_codigo == estados.CATEGORIA_GASTO_OTROS:
        motivos.append(MOTIVO_DERIVACION_CATEGORIA_REVISION_MANUAL)
    if monto > monto_maximo:
        motivos.append(MOTIVO_DERIVACION_MONTO_SUPERA_LIMITE)
    if not fecha_pertenece_al_mes_corriente(fecha_gasto):
        motivos.append(MOTIVO_DERIVACION_FECHA_FUERA_DE_MES_CORRIENTE)
    return motivos


def aprobar_solicitud_automaticamente(solicitud_id: str) -> None:
    """Aprueba la solicitud automáticamente por cumplir con la política de gastos vigente.

    No queda nadie asignado porque la resolución fue automática, y se limpian
    los motivos de cancelación o rechazo, ya que la solicitud fue aceptada.
    """
    ahora = _ahora()
    conexion = base_datos.obtener_conexion()
    try:
        modificado_por = _determinar_modificado_por(conexion, solicitud_id)

        with conexion:
            conexion.execute(
                """
                UPDATE solicitudes
                SET estado_solicitud_codigo = ?,
                    estado_conversacion_codigo = ?,
                    usuario_asignado_id = NULL,
                    motivo_cancelacion = NULL,
                    motivo_rechazo = NULL,
                    modificado_por = ?,
                    modificado_en = ?
                WHERE id = ?;
                """,
                (
                    estados.ESTADO_SOLICITUD_APROBADA,
                    estados.ESTADO_CONVERSACION_FINALIZADO,
                    modificado_por,
                    ahora,
                    solicitud_id,
                ),
            )
    finally:
        conexion.close()


def derivar_solicitud_a_supervisor(solicitud_id: str, supervisor_id: str) -> None:
    """Deriva la solicitud a un supervisor activo para que la revise manualmente."""
    ahora = _ahora()
    conexion = base_datos.obtener_conexion()
    try:
        modificado_por = _determinar_modificado_por(conexion, solicitud_id)

        with conexion:
            conexion.execute(
                """
                UPDATE solicitudes
                SET estado_solicitud_codigo = ?,
                    estado_conversacion_codigo = ?,
                    usuario_asignado_id = ?,
                    modificado_por = ?,
                    modificado_en = ?
                WHERE id = ?;
                """,
                (
                    estados.ESTADO_SOLICITUD_DERIVADA_SUPERVISOR,
                    estados.ESTADO_CONVERSACION_ESPERANDO_REVISION_SUPERVISOR,
                    supervisor_id,
                    modificado_por,
                    ahora,
                    solicitud_id,
                ),
            )
    finally:
        conexion.close()


def validar_politica_y_resolver_solicitud(solicitud_id: str) -> str:
    """Aplica la política de gastos del área y resuelve la solicitud según el resultado.

    Busca la política activa para el área del solicitante y la categoría
    elegida. Si no existe, cancela la solicitud porque la categoría no está
    permitida para esa área e informa el área, la categoría elegida y las
    categorías habilitadas para el área. Si existe, evalúa de forma
    independiente los tres motivos que obligan a derivar la solicitud a un
    supervisor (categoría "Otros", monto por encima del máximo permitido y
    fecha del gasto fuera del mes en curso) sin detenerse en el primero que
    encuentre, de modo de poder informar todos los motivos aplicables. Si no
    corresponde derivar, aprueba la solicitud automáticamente. Si corresponde
    derivar pero no hay ningún supervisor activo disponible, cancela la
    solicitud en su lugar.

    Devuelve el mensaje final, ya redactado en español, que debe enviarse a
    la persona usuaria informándole el resultado de su solicitud.
    """
    solicitud = obtener_solicitud_por_id(solicitud_id)

    conexion = base_datos.obtener_conexion()
    try:
        solicitante = conexion.execute(
            """
            SELECT usuario.area_codigo AS area_codigo, area.descripcion AS area_descripcion
            FROM usuarios AS usuario
            JOIN lookup_areas AS area ON area.codigo = usuario.area_codigo
            WHERE usuario.id = ?;
            """,
            (solicitud["solicitante_id"],),
        ).fetchone()
        categoria_seleccionada = conexion.execute(
            "SELECT descripcion FROM lookup_categorias_gasto WHERE codigo = ?;",
            (solicitud["categoria_gasto_codigo"],),
        ).fetchone()
    finally:
        conexion.close()

    politica = obtener_politica_gasto_activa(solicitante["area_codigo"], solicitud["categoria_gasto_codigo"])

    if politica is None:
        cancelar_solicitud(solicitud_id, MOTIVO_CANCELACION_CATEGORIA_NO_PERMITIDA)
        logger.info(
            "Solicitud %s cancelada: la categoría %s no está permitida para el área %s.",
            solicitud_id, solicitud["categoria_gasto_codigo"], solicitante["area_codigo"],
        )
        categorias_validas = obtener_categorias_validas_por_area(solicitante["area_codigo"])
        return construir_mensaje_categoria_no_permitida(
            solicitante["area_descripcion"], categoria_seleccionada["descripcion"], categorias_validas
        )

    fecha_gasto = date.fromisoformat(solicitud["fecha_gasto"])
    motivos_derivacion = _calcular_motivos_derivacion(
        solicitud["categoria_gasto_codigo"], solicitud["monto"], fecha_gasto, politica["monto_maximo"]
    )

    if not motivos_derivacion:
        aprobar_solicitud_automaticamente(solicitud_id)
        logger.info("Solicitud %s aprobada automáticamente según la política de gastos vigente.", solicitud_id)
        return MENSAJE_SOLICITUD_APROBADA_AUTOMATICAMENTE

    supervisor = obtener_supervisor_activo()
    if supervisor is None:
        cancelar_solicitud(solicitud_id, MOTIVO_CANCELACION_SIN_SUPERVISOR_ACTIVO)
        logger.info("Solicitud %s cancelada: no hay un supervisor activo disponible para revisión.", solicitud_id)
        return MENSAJE_SOLICITUD_CANCELADA_SIN_SUPERVISOR

    derivar_solicitud_a_supervisor(solicitud_id, supervisor["id"])
    logger.info(
        "Solicitud %s derivada al supervisor %s para revisión. Motivos: %s.",
        solicitud_id, supervisor["id"], motivos_derivacion,
    )
    return construir_mensaje_derivacion(motivos_derivacion)


MENSAJE_PENDIENTES_VACIO = "No hay solicitudes pendientes de revisión."

CONSULTA_SOLICITUDES_PENDIENTES_REVISION = """
    SELECT
        solicitud.id AS id,
        solicitud.categoria_gasto_codigo AS categoria_gasto_codigo,
        solicitud.fecha_gasto AS fecha_gasto,
        solicitud.monto AS monto,
        solicitante.legajo AS legajo,
        solicitante.nombre AS nombre,
        solicitante.apellido AS apellido,
        area.descripcion AS area_descripcion,
        categoria.descripcion AS categoria_descripcion,
        politica.monto_maximo AS monto_maximo
    FROM solicitudes AS solicitud
    JOIN usuarios AS solicitante ON solicitante.id = solicitud.solicitante_id
    JOIN lookup_areas AS area ON area.codigo = solicitante.area_codigo
    JOIN lookup_categorias_gasto AS categoria ON categoria.codigo = solicitud.categoria_gasto_codigo
    JOIN politicas_gastos AS politica
        ON politica.area_codigo = solicitante.area_codigo
       AND politica.categoria_gasto_codigo = solicitud.categoria_gasto_codigo
       AND politica.activo = 1
    WHERE solicitud.estado_solicitud_codigo = ?
      AND solicitud.estado_conversacion_codigo = ?
    ORDER BY solicitud.creado_en;
"""


def construir_mensaje_pendientes_revision() -> str:
    """Arma el mensaje con el listado de solicitudes pendientes de revisión, identificadas por legajo.

    Los motivos de derivación no se almacenan en la solicitud, así que se
    recalculan aplicando la misma política vigente para el área y la
    categoría de cada solicitud, igual que al momento de derivarla.
    """
    conexion = base_datos.obtener_conexion()
    try:
        filas = conexion.execute(
            CONSULTA_SOLICITUDES_PENDIENTES_REVISION,
            (estados.ESTADO_SOLICITUD_DERIVADA_SUPERVISOR, estados.ESTADO_CONVERSACION_ESPERANDO_REVISION_SUPERVISOR),
        ).fetchall()
    finally:
        conexion.close()

    if not filas:
        return MENSAJE_PENDIENTES_VACIO

    bloques = []
    for fila in filas:
        fecha_gasto = date.fromisoformat(fila["fecha_gasto"])
        motivos = _calcular_motivos_derivacion(fila["categoria_gasto_codigo"], fila["monto"], fecha_gasto, fila["monto_maximo"])
        lista_motivos = "\n".join(f"- {motivo}" for motivo in motivos)
        bloques.append(
            f"Legajo: {fila['legajo']}\n"
            f"Empleado: {fila['nombre']} {fila['apellido']}\n"
            f"Área: {fila['area_descripcion']}\n"
            f"Categoría: {fila['categoria_descripcion']}\n"
            f"Fecha: {fecha_gasto.strftime('%d/%m/%Y')}\n"
            f"Monto: ${fila['monto']:.2f}\n"
            "Motivos de derivación:\n"
            f"{lista_motivos}"
        )

    return "Solicitudes pendientes de revisión:\n\n" + "\n\n".join(bloques)


def buscar_solicitudes_pendientes_por_legajo(legajo: str) -> list[sqlite3.Row]:
    """Busca las solicitudes pendientes de revisión del supervisor para un legajo de empleado.

    Devuelve todas las coincidencias para que quien llama pueda distinguir
    entre no encontrar ninguna, encontrar una sola (caso resoluble) o
    encontrar más de una (caso ambiguo que no se resuelve automáticamente).
    """
    conexion = base_datos.obtener_conexion()
    try:
        return conexion.execute(
            """
            SELECT solicitud.*
            FROM solicitudes AS solicitud
            JOIN usuarios AS solicitante ON solicitante.id = solicitud.solicitante_id
            WHERE solicitante.legajo = ?
              AND solicitud.estado_solicitud_codigo = ?
              AND solicitud.estado_conversacion_codigo = ?
            ORDER BY solicitud.creado_en;
            """,
            (legajo, estados.ESTADO_SOLICITUD_DERIVADA_SUPERVISOR, estados.ESTADO_CONVERSACION_ESPERANDO_REVISION_SUPERVISOR),
        ).fetchall()
    finally:
        conexion.close()


def aprobar_solicitud_por_supervisor(solicitud_id: str, supervisor_id: str) -> None:
    """Aprueba una solicitud derivada, según la decisión manual de un supervisor.

    No queda nadie asignado porque la revisión ya concluyó, y se limpia
    cualquier motivo de rechazo previo, ya que la solicitud fue aceptada.
    """
    ahora = _ahora()
    conexion = base_datos.obtener_conexion()
    try:
        with conexion:
            conexion.execute(
                """
                UPDATE solicitudes
                SET estado_solicitud_codigo = ?,
                    estado_conversacion_codigo = ?,
                    usuario_asignado_id = NULL,
                    motivo_rechazo = NULL,
                    modificado_por = ?,
                    modificado_en = ?
                WHERE id = ?;
                """,
                (
                    estados.ESTADO_SOLICITUD_APROBADA,
                    estados.ESTADO_CONVERSACION_FINALIZADO,
                    supervisor_id,
                    ahora,
                    solicitud_id,
                ),
            )
    finally:
        conexion.close()


def rechazar_solicitud_por_supervisor(solicitud_id: str, supervisor_id: str, motivo_rechazo: str) -> None:
    """Rechaza una solicitud derivada, según la decisión manual de un supervisor, registrando el motivo informado.

    No queda nadie asignado porque la revisión ya concluyó.
    """
    ahora = _ahora()
    conexion = base_datos.obtener_conexion()
    try:
        with conexion:
            conexion.execute(
                """
                UPDATE solicitudes
                SET estado_solicitud_codigo = ?,
                    estado_conversacion_codigo = ?,
                    usuario_asignado_id = NULL,
                    motivo_rechazo = ?,
                    modificado_por = ?,
                    modificado_en = ?
                WHERE id = ?;
                """,
                (
                    estados.ESTADO_SOLICITUD_RECHAZADA,
                    estados.ESTADO_CONVERSACION_FINALIZADO,
                    motivo_rechazo,
                    supervisor_id,
                    ahora,
                    solicitud_id,
                ),
            )
    finally:
        conexion.close()
