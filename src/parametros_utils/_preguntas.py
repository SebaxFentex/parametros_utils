"""Preguntas interactivas y reintentos de parámetros de ejecución."""

from collections.abc import Callable
from datetime import date

from ._validacion import (
    _texto_obligatorio,
    _validar_menu,
    validar_opciones,
    validar_periodo,
    validar_si_no,
)


def solicitar_periodo(pregunta: str) -> date:
    """Solicita un periodo hasta recibir YYYYMM válido.

    Raises:
        TypeError: Si la pregunta no es texto.
        ValueError: Si la pregunta está vacía.
        EOFError: Si se cierra la entrada.
        KeyboardInterrupt: Si el operador interrumpe la pregunta.
    """
    return _solicitar_valor(pregunta, validar_periodo)


def solicitar_si_no(pregunta: str) -> bool:
    """Solicita una respuesta si/sí/no hasta obtener un booleano.

    Raises:
        TypeError: Si la pregunta no es texto.
        ValueError: Si la pregunta está vacía.
        EOFError: Si se cierra la entrada.
        KeyboardInterrupt: Si el operador interrumpe la pregunta.
    """
    return _solicitar_valor(pregunta, validar_si_no)


def solicitar_opciones(
    pregunta: str,
    opciones: dict[str, str],
    *,
    codigo_todos: str | None = None,
) -> set[str]:
    """Muestra el menú recibido y solicita una selección válida.

    Raises:
        TypeError: Si la pregunta o el menú tienen tipos incorrectos.
        ValueError: Si la pregunta o el menú son inválidos.
        EOFError: Si se cierra la entrada.
        KeyboardInterrupt: Si el operador interrumpe la pregunta.
    """
    _texto_obligatorio(pregunta, "pregunta")
    _validar_menu(opciones, codigo_todos)
    if codigo_todos is not None:
        print(f"  {codigo_todos} = Todos")
    for codigo, etiqueta in opciones.items():
        print(f"  {codigo} = {etiqueta}")
    return _solicitar_valor(
        pregunta,
        lambda texto: validar_opciones(texto, opciones, codigo_todos=codigo_todos),
    )


def _solicitar_valor[T](pregunta: str, validador: Callable[[str], T]) -> T:
    """Lee y valida una respuesta, reintentando solo errores de contenido."""
    _texto_obligatorio(pregunta, "pregunta")
    while True:
        texto = input(pregunta)
        try:
            return validador(texto)
        except ValueError as exc:
            print(f"Error: {exc}")
