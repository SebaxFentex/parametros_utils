"""Expone la API pública de parámetros de ejecución de tareas Python.

El consumidor importa desde este paquete. Los módulos con prefijo _ son internos;
la resolución, los modelos y los adaptadores de consola permanecen separados.
"""

import logging

from ._modelos import (
    Parametro,
    ParametroOpciones,
    ParametroPeriodo,
    ParametroSiNo,
    ParametrosResueltos,
)
from ._preguntas import solicitar_opciones, solicitar_periodo, solicitar_si_no
from ._resolucion import obtener_parametros
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
