"""Funciones de validación de datos ingresados por el usuario durante la conversación.

Cada validador recibe el texto crudo escrito por la persona usuaria, verifica
que tenga un formato y contenido válidos, y devuelve el valor ya convertido al
tipo de dato correspondiente. Si el texto no es válido, se lanza ValueError
con un mensaje en español que explica el motivo.
"""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

PATRON_FECHA = re.compile(r"^\d{2}/\d{2}/\d{4}$")

PATRON_MONTO = re.compile(r"^-?\d+([.,]\d+)?$")

EXTENSIONES_JPG = (".jpg", ".jpeg")

MIME_TYPES_JPG = ("image/jpeg", "image/jpg")


def validar_fecha_gasto(texto_fecha: str) -> date:
    """Valida el texto ingresado como fecha del gasto en formato DD/MM/AAAA.

    Devuelve un objeto date si el texto representa una fecha real con ese
    formato. Lanza ValueError con un mensaje en español si el texto está
    vacío, no respeta el formato esperado o no corresponde a una fecha que
    exista en el calendario (por ejemplo, 31/02/2026).
    """
    texto_fecha = (texto_fecha or "").strip()
    if not texto_fecha:
        raise ValueError("La fecha no puede estar vacía. Ingresela en formato DD/MM/AAAA.")

    if not PATRON_FECHA.match(texto_fecha):
        raise ValueError("El formato de la fecha no es válido. Ingresela en formato DD/MM/AAAA.")

    try:
        return datetime.strptime(texto_fecha, "%d/%m/%Y").date()
    except ValueError as error:
        raise ValueError("La fecha ingresada no existe en el calendario. Ingresela en formato DD/MM/AAAA.") from error


def validar_monto_gasto(texto_monto: str) -> float:
    """Valida el texto ingresado como monto del gasto y lo convierte a un número.

    Acepta números positivos con un único separador decimal, ya sea coma
    (estilo argentino, por ejemplo 1500,50) o punto (por ejemplo 1500.50).
    No admite separadores de miles, ya que combinarlos con el separador
    decimal vuelve ambiguo el formato (por ejemplo 1.500,50 o 1,500.50).

    Devuelve un float si el texto representa un número positivo válido. Lanza
    ValueError con un mensaje en español si el texto está vacío, no respeta
    el formato esperado, o representa un número cero o negativo.
    """
    texto_monto = (texto_monto or "").strip()
    if not texto_monto:
        raise ValueError("El monto no puede estar vacío. Ingrese un número positivo, por ejemplo 1500,50.")

    if not PATRON_MONTO.match(texto_monto):
        raise ValueError(
            "El formato del monto no es válido. Ingrese un número positivo, "
            "usando como mucho una coma o un punto decimal, por ejemplo 1500,50 o 1500.50."
        )

    try:
        monto = Decimal(texto_monto.replace(",", "."))
    except InvalidOperation as error:
        raise ValueError("El monto ingresado no es un número válido.") from error

    if monto <= 0:
        raise ValueError("El monto debe ser un número positivo mayor a cero.")

    return float(monto)


def validar_nombre_archivo_jpg(nombre_archivo: str) -> None:
    """Valida que el nombre de archivo informado corresponda a una imagen JPG/JPEG.

    No devuelve ningún valor; lanza ValueError con un mensaje en español si
    el nombre está vacío, ausente o no tiene extensión .jpg/.jpeg
    (sin distinguir mayúsculas de minúsculas).
    """
    nombre_archivo = (nombre_archivo or "").strip()
    if not nombre_archivo:
        raise ValueError("El archivo enviado no tiene un nombre válido. Debe enviar un archivo JPG.")

    if not nombre_archivo.lower().endswith(EXTENSIONES_JPG):
        raise ValueError("El archivo debe tener formato JPG o JPEG (extensión .jpg o .jpeg).")


def validar_mime_type_jpg(mime_type: str) -> None:
    """Valida que el tipo MIME informado corresponda a una imagen JPG/JPEG.

    No devuelve ningún valor; lanza ValueError con un mensaje en español si
    el tipo MIME está vacío, ausente o no es image/jpeg (por ejemplo,
    application/pdf o image/png).
    """
    mime_type = (mime_type or "").strip().lower()
    if not mime_type:
        raise ValueError("No se pudo determinar el tipo de archivo enviado. Debe enviar un archivo JPG.")

    if mime_type not in MIME_TYPES_JPG:
        raise ValueError("El tipo de archivo enviado no corresponde a una imagen JPG/JPEG.")


def validar_tamano_archivo(tamano_bytes: int, maximo_bytes: int) -> None:
    """Valida que el tamaño del archivo no supere el máximo permitido.

    No devuelve ningún valor; lanza ValueError con un mensaje en español si
    el tamaño en bytes supera el máximo configurado para los comprobantes.
    """
    if tamano_bytes > maximo_bytes:
        maximo_mb = maximo_bytes / (1024 * 1024)
        raise ValueError(f"El archivo enviado supera el tamaño máximo permitido de {maximo_mb:.0f} MB.")
