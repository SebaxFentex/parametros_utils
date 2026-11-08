"""Parámetros de ejecución de tareas Python."""

import logging

from ._parametro import Parametro, ParametroOpciones, ParametroPeriodo, ParametroSiNo
from ._preguntas import solicitar_opciones, solicitar_periodo, solicitar_si_no
from ._resolucion import obtener_parametros
from ._resultados import ParametrosResueltos
from ._validacion import validar_opciones, validar_periodo, validar_si_no

__all__ = [
    "Parametro",
    "ParametroOpciones",
    "ParametroPeriodo",
    "ParametroSiNo",
    "ParametrosResueltos",
    "obtener_parametros",
    "solicitar_opciones",
    "solicitar_periodo",
    "solicitar_si_no",
    "validar_opciones",
    "validar_periodo",
    "validar_si_no",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())
