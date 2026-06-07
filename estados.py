"""Constantes de códigos de las tablas de referencia (lookup) y de control de intentos."""

# ------------------------------------------------------------
# Roles (lookup_roles.codigo)
# ------------------------------------------------------------
ROL_EMPLEADO = 1
ROL_SUPERVISOR = 2
ROL_ADMINISTRADOR = 3
ROL_SISTEMA = 4

# ------------------------------------------------------------
# Estados de solicitud (lookup_estados_solicitud.codigo)
# ------------------------------------------------------------
ESTADO_SOLICITUD_EN_CURSO = 1
ESTADO_SOLICITUD_APROBADA = 2
ESTADO_SOLICITUD_RECHAZADA = 3
ESTADO_SOLICITUD_CANCELADA = 4
ESTADO_SOLICITUD_DERIVADA_SUPERVISOR = 5

# ------------------------------------------------------------
# Estados de conversación (lookup_estados_conversacion.codigo)
# ------------------------------------------------------------
ESTADO_CONVERSACION_INICIO = 1
ESTADO_CONVERSACION_ESPERANDO_LEGAJO = 2
ESTADO_CONVERSACION_ESPERANDO_CATEGORIA = 3
ESTADO_CONVERSACION_ESPERANDO_FECHA = 4
ESTADO_CONVERSACION_ESPERANDO_MONTO = 5
ESTADO_CONVERSACION_ESPERANDO_COMPROBANTE = 6
ESTADO_CONVERSACION_ESPERANDO_REVISION_SUPERVISOR = 7
ESTADO_CONVERSACION_FINALIZADO = 8

# ------------------------------------------------------------
# Categorías de gasto (lookup_categorias_gasto.codigo)
# ------------------------------------------------------------
CATEGORIA_GASTO_OTROS = 5

# ------------------------------------------------------------
# Límites de reintentos
# ------------------------------------------------------------
MAX_INTENTOS_VALIDACION = 3
