"""Capa de servicios: encapsula el acceso a datos del flujo de rendición de gastos.

Cada función abre su propia conexión mediante obtener_conexion(), realiza una
unidad de trabajo completa (consulta o transacción) y cierra la conexión. Así
los manejadores de Telegram no necesitan conocer detalles de SQL ni de SQLite.
"""

import sqlite3
import uuid
from datetime import date, datetime

import base_datos
import estados


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


def buscar_empleado_activo_por_legajo(legajo: str) -> sqlite3.Row | None:
    """Busca un usuario empleado activo por legajo.

    Devuelve None si no existe, si está inactivo o si su rol no es Empleado.
    """
    conexion = base_datos.obtener_conexion()
    try:
        return conexion.execute(
            """
            SELECT * FROM usuarios
            WHERE legajo = ?
              AND activo = 1
              AND rol_codigo = ?
            LIMIT 1;
            """,
            (legajo, estados.ROL_EMPLEADO),
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
