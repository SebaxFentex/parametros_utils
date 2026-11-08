"""Parámetros de ejecución de tareas Python."""

import logging

from ._parametro import Parametro
from ._preguntas import solicitar_opciones, solicitar_periodo, solicitar_si_no
from ._resolucion import obtener_parametros
from ._validacion import validar_opciones, validar_periodo, validar_si_no

__all__ = [
    "Parametro",
    "obtener_parametros",
    "solicitar_opciones",
    "solicitar_periodo",
    "solicitar_si_no",
    "validar_opciones",
    "validar_periodo",
    "validar_si_no",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())
