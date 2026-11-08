"""Resolución de argumentos y preguntas de una tarea consumidora."""

import argparse
from collections.abc import Sequence

from ._parametro import (
    ParametroOpciones,
    ParametroPeriodo,
    ParametroSiNo,
    _comprobar_tipo_textual,
)
from ._resultados import ParametrosResueltos
from ._validacion import _validar_menu_opciones


def obtener_parametros(
    definiciones_parametros: Sequence[
        ParametroPeriodo | ParametroSiNo | ParametroOpciones
    ],
    *,
    descripcion: str,
    argumentos: Sequence[str] | None = None,
) -> ParametrosResueltos:
    """Resuelve las definiciones y devuelve sus resultados con acceso tipado.

    Args:
        definiciones_parametros: Definiciones con nombres únicos, en el orden
            en que se solicitarán si se habilita --interactivo.
        descripcion: Descripción de la tarea mostrada en la ayuda.
        argumentos: Argumentos explícitos; None lee sys.argv y [] indica que
            no se proporcionó ningún argumento.

    Returns:
        Resultados completos de esta ejecución. El acceso mediante cada
        definición conserva su tipo date, bool o set[str], sin metadatos de origen.

    Raises:
        TypeError: Si las definiciones o los argumentos tienen tipos incorrectos.
        ValueError: Si hay nombres duplicados o configuración inválida.
        SystemExit: Con 0 por ayuda o con 2 por errores de argumentos.
        EOFError: Si se cierra la entrada interactiva.
        KeyboardInterrupt: Si el operador cancela la entrada interactiva.
    """
    definiciones_parametros = _comprobar_definiciones_parametros(
        definiciones_parametros
    )
    _comprobar_tipo_textual(descripcion, "descripción")
    _comprobar_argumentos_ejecucion(argumentos)
    analizador = argparse.ArgumentParser(description=descripcion, allow_abbrev=False)
    analizador.add_argument(
        "--interactivo",
        action="store_true",
        help="Solicita todos los parámetros por pantalla; incompatible con valores explícitos.",
    )
    for definicion_parametro in definiciones_parametros:
        analizador.add_argument(
            f"--{definicion_parametro.nombre}",
            dest=f"parametro_{definicion_parametro.nombre}",
            metavar=definicion_parametro.nombre.upper(),
            help=definicion_parametro.ayuda or definicion_parametro.pregunta,
        )
    argumentos_analizados = analizador.parse_args(argumentos)
    parametros = ParametrosResueltos()
    if argumentos_analizados.interactivo:
        argumentos_explicitos = [
            f"--{definicion_parametro.nombre}"
            for definicion_parametro in definiciones_parametros
            if _leer_argumento_parametro(
                argumentos_analizados, definicion_parametro.nombre
            )
            is not None
        ]
        if argumentos_explicitos:
            analizador.error(
                "--interactivo no admite valores explícitos: "
                f"{', '.join(argumentos_explicitos)}."
            )
        for definicion_parametro in definiciones_parametros:
            definicion_parametro._resolver_valor_interactivo(parametros)
        return parametros

    for definicion_parametro in definiciones_parametros:
        entrada_textual = _leer_argumento_parametro(
            argumentos_analizados, definicion_parametro.nombre
        )
        if entrada_textual is None:
            entrada_textual = definicion_parametro.predeterminado
        if entrada_textual is None:
            analizador.error(
                f"Falta --{definicion_parametro.nombre}: "
                "no se definió un valor predeterminado."
            )
        try:
            definicion_parametro._resolver_valor_automatico(parametros, entrada_textual)
        except ValueError as exc:
            analizador.error(f"--{definicion_parametro.nombre}: {exc}")
    return parametros


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


def _comprobar_definiciones_parametros(
    definiciones_parametros: object,
) -> tuple[ParametroPeriodo | ParametroSiNo | ParametroOpciones, ...]:
    """Comprueba una secuencia de las tres variantes admitidas con nombres únicos."""
    if not isinstance(definiciones_parametros, Sequence) or isinstance(
        definiciones_parametros, (str, bytes)
    ):
        raise TypeError("Las definiciones de parámetros deben ser una secuencia.")
    definiciones_comprobadas: list[
        ParametroPeriodo | ParametroSiNo | ParametroOpciones
    ] = []
    nombres_parametros: set[str] = set()
    for definicion_parametro in definiciones_parametros:
        if not isinstance(
            definicion_parametro, (ParametroPeriodo, ParametroSiNo, ParametroOpciones)
        ):
            raise TypeError(
                "Cada definición debe ser una de las tres variantes admitidas."
            )
        if definicion_parametro.nombre in nombres_parametros:
            raise ValueError(f"Parámetro repetido: {definicion_parametro.nombre!r}.")
        nombres_parametros.add(definicion_parametro.nombre)
        if isinstance(definicion_parametro, ParametroOpciones):
            _validar_menu_opciones(
                definicion_parametro.menu_opciones, definicion_parametro.codigo_todos
            )
        definiciones_comprobadas.append(definicion_parametro)
    return tuple(definiciones_comprobadas)


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
