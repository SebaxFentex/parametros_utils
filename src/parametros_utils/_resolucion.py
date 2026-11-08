"""Resolución de argumentos y preguntas de una tarea consumidora."""

import argparse
from collections.abc import Sequence
from datetime import date

from ._parametro import Parametro, _comprobar_texto
from ._preguntas import solicitar_opciones, solicitar_periodo, solicitar_si_no
from ._validacion import _validar_menu, validar_opciones, validar_periodo, validar_si_no


def obtener_parametros(
    parametros: Sequence[Parametro],
    *,
    descripcion: str,
    argumentos: Sequence[str] | None = None,
) -> dict[str, date | bool | set[str]]:
    """Resuelve todas las entradas declaradas y devuelve sus valores validados.

    En automático usa el argumento explícito o el predeterminado textual.
    Con --interactivo solicita todas las entradas sin usar predeterminados.

    Raises:
        TypeError: Si las declaraciones o argumentos tienen tipos incorrectos.
        ValueError: Si hay declaraciones duplicadas o configuración inválida.
        SystemExit: Con 0 por ayuda o con 2 por errores de argumentos.
        EOFError: Si se cierra la entrada interactiva.
        KeyboardInterrupt: Si el operador cancela la entrada interactiva.
    """
    declaraciones = _comprobar_declaraciones(parametros)
    _comprobar_texto(descripcion, "descripción")
    _comprobar_argumentos(argumentos)
    analizador = argparse.ArgumentParser(description=descripcion, allow_abbrev=False)
    analizador.add_argument(
        "--interactivo",
        action="store_true",
        help="Solicita todos los parámetros por pantalla; incompatible con valores explícitos.",
    )
    for parametro in declaraciones:
        analizador.add_argument(
            f"--{parametro.nombre}",
            dest=parametro.nombre,
            help=parametro.ayuda or parametro.pregunta,
        )
    entradas = analizador.parse_args(argumentos)
    if entradas.interactivo:
        explicitos = [
            f"--{p.nombre}"
            for p in declaraciones
            if getattr(entradas, p.nombre) is not None
        ]
        if explicitos:
            analizador.error(
                f"--interactivo no admite valores explícitos: {', '.join(explicitos)}."
            )
        return {parametro.nombre: _solicitar(parametro) for parametro in declaraciones}

    resultado: dict[str, date | bool | set[str]] = {}
    for parametro in declaraciones:
        texto = getattr(entradas, parametro.nombre)
        if texto is None:
            texto = parametro.predeterminado
        if texto is None:
            analizador.error(
                f"Falta --{parametro.nombre}: no se definió un valor predeterminado."
            )
        try:
            resultado[parametro.nombre] = _interpretar(parametro, texto)
        except ValueError as exc:
            analizador.error(f"--{parametro.nombre}: {exc}")
    return resultado


def _interpretar(parametro: Parametro, texto: str) -> date | bool | set[str]:
    """Interpreta una entrada con el validador de su tipo declarado."""
    if parametro.tipo == "periodo":
        return validar_periodo(texto)
    if parametro.tipo == "si_no":
        return validar_si_no(texto)
    assert parametro.opciones is not None
    return validar_opciones(
        texto, parametro.opciones, codigo_todos=parametro.codigo_todos
    )


def _solicitar(parametro: Parametro) -> date | bool | set[str]:
    """Solicita una entrada usando la pregunta y el menú del consumidor."""
    if parametro.tipo == "periodo":
        return solicitar_periodo(parametro.pregunta)
    if parametro.tipo == "si_no":
        return solicitar_si_no(parametro.pregunta)
    assert parametro.opciones is not None
    return solicitar_opciones(
        parametro.pregunta, parametro.opciones, codigo_todos=parametro.codigo_todos
    )


def _comprobar_declaraciones(parametros: object) -> tuple[Parametro, ...]:
    """Comprueba una secuencia de declaraciones con nombres únicos."""
    if not isinstance(parametros, Sequence) or isinstance(parametros, (str, bytes)):
        raise TypeError("Los parámetros deben ser una secuencia de objetos Parametro.")
    declaraciones: list[Parametro] = []
    nombres: set[str] = set()
    for parametro in parametros:
        if not isinstance(parametro, Parametro):
            raise TypeError("Cada declaración debe ser un objeto Parametro.")
        if parametro.nombre in nombres:
            raise ValueError(f"Parámetro repetido: {parametro.nombre!r}.")
        nombres.add(parametro.nombre)
        if parametro.tipo == "opciones":
            _validar_menu(parametro.opciones, parametro.codigo_todos)
        declaraciones.append(parametro)
    return tuple(declaraciones)


def _comprobar_argumentos(argumentos: object) -> None:
    """Comprueba argumentos explícitos sin leer sys.argv ni interpretar valores."""
    if argumentos is None:
        return
    if not isinstance(argumentos, Sequence) or isinstance(argumentos, (str, bytes)):
        raise TypeError("Los argumentos deben ser una secuencia de textos o None.")
    for argumento in argumentos:
        if not isinstance(argumento, str):
            raise TypeError("Cada argumento debe ser texto.")
