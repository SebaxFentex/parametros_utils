"""Analiza la invocación de consola sin interpretar valores de parámetros.

Este módulo concentra argparse, la ayuda y sus códigos de salida. Entrega el modo
y las entradas textuales a resolución; no aplica predeterminados, solicita
respuestas ni almacena valores resueltos.
"""

import argparse
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import NoReturn

from ._modelos import ParametroOpciones, ParametroPeriodo, ParametroSiNo
from ._validacion import _comprobar_tipo_textual


@dataclass(frozen=True, slots=True)
class _ArgumentosEjecucion:
    """Agrupa las entradas analizadas y conserva cómo informar un error CLI.

    Las entradas siguen siendo texto o None. El analizador se mantiene aquí para
    que los errores posteriores conserven la ayuda de uso y SystemExit(2).
    """

    interactivo: bool
    entradas_textuales: dict[str, str | None]
    _analizador: argparse.ArgumentParser = field(repr=False)

    def informar_error(self, mensaje: str) -> NoReturn:
        """Informa un error de argumentos y termina con el código de argparse."""
        self._analizador.error(mensaje)


def _analizar_argumentos_ejecucion(
    definiciones_parametros: Sequence[
        ParametroPeriodo | ParametroSiNo | ParametroOpciones
    ],
    *,
    descripcion: str,
    argumentos: Sequence[str] | None,
) -> _ArgumentosEjecucion:
    """Analiza la consola y rechaza la mezcla de modos antes de resolver valores."""
    _comprobar_tipo_textual(descripcion, "descripción")
    _comprobar_argumentos_ejecucion(argumentos)

    analizador = _crear_analizador(definiciones_parametros, descripcion)
    argumentos_analizados = analizador.parse_args(argumentos)

    # La ayuda termina en parse_args, antes de interpretar cualquier predeterminado.
    entradas_textuales = {
        definicion_parametro.nombre: _leer_argumento_parametro(
            argumentos_analizados, definicion_parametro.nombre
        )
        for definicion_parametro in definiciones_parametros
    }
    argumentos_ejecucion = _ArgumentosEjecucion(
        interactivo=argumentos_analizados.interactivo is True,
        entradas_textuales=entradas_textuales,
        _analizador=analizador,
    )

    if argumentos_ejecucion.interactivo:
        argumentos_explicitos = [
            f"--{nombre_parametro}"
            for nombre_parametro, entrada_textual in entradas_textuales.items()
            if entrada_textual is not None
        ]
        if argumentos_explicitos:
            argumentos_ejecucion.informar_error(
                "--interactivo no admite valores explícitos: "
                f"{', '.join(argumentos_explicitos)}."
            )

    return argumentos_ejecucion


def _crear_analizador(
    definiciones_parametros: Sequence[
        ParametroPeriodo | ParametroSiNo | ParametroOpciones
    ],
    descripcion: str,
) -> argparse.ArgumentParser:
    """Registra el modo interactivo y una opción textual por definición."""
    analizador = argparse.ArgumentParser(description=descripcion, allow_abbrev=False)
    analizador.add_argument(
        "--interactivo",
        action="store_true",
        help="Solicita todos los parámetros por pantalla; incompatible con valores explícitos.",
    )

    for definicion_parametro in definiciones_parametros:
        analizador.add_argument(
            f"--{definicion_parametro.nombre}",
            # El prefijo evita colisiones con atributos propios de Namespace.
            dest=f"parametro_{definicion_parametro.nombre}",
            metavar=definicion_parametro.nombre.upper(),
            help=definicion_parametro.ayuda or definicion_parametro.pregunta,
        )

    return analizador


def _leer_argumento_parametro(
    argumentos_analizados: argparse.Namespace, nombre_parametro: str
) -> str | None:
    """Recupera la entrada textual de una definición sin interpretar su contenido."""
    entrada_textual: object = getattr(
        argumentos_analizados, f"parametro_{nombre_parametro}"
    )
    if entrada_textual is None or isinstance(entrada_textual, str):
        return entrada_textual
    raise TypeError("El argumento del parámetro debe ser texto o estar omitido.")


def _comprobar_argumentos_ejecucion(argumentos_ejecucion: object) -> None:
    """Comprueba argumentos explícitos sin leer sys.argv ni interpretar valores."""
    if argumentos_ejecucion is None:
        return
    if not isinstance(argumentos_ejecucion, Sequence) or isinstance(
        argumentos_ejecucion, (str, bytes)
    ):
        raise TypeError("Los argumentos deben ser una secuencia de textos o None.")

    for argumento in argumentos_ejecucion:
        if not isinstance(argumento, str):
            raise TypeError("Cada argumento debe ser texto.")
