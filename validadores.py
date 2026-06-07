"""Funciones de validación de datos ingresados por el usuario durante la conversación.

Cada validador recibe el texto crudo escrito por la persona usuaria, verifica
que tenga un formato y contenido válidos, y devuelve el valor ya convertido al
tipo de dato correspondiente. Si el texto no es válido, se lanza ValueError
con un mensaje en español que explica el motivo.
"""

import re
from datetime import date, datetime

PATRON_FECHA = re.compile(r"^\d{2}/\d{2}/\d{4}$")


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
