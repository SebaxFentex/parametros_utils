"""Solicita respuestas al operador y reintenta las entradas inválidas.

Presenta las preguntas y los menús del consumidor, delegando el contenido a la
validación pura. No analiza argumentos, aplica predeterminados ni conoce las
definiciones o el almacenamiento de una ejecución completa.
"""

from collections.abc import Callable
from datetime import date

from ._validacion import (
    _recortar_texto_obligatorio,
    _validar_menu_opciones,
    validar_opciones,
    validar_periodo,
    validar_si_no,
)


def solicitar_periodo(pregunta: str) -> date:
    """Solicita un periodo YYYYMM y devuelve una fecha con día 1.

    Args:
        pregunta: Texto del consumidor; conserva sus espacios finales.

    Returns:
        Primer día del mes indicado por la respuesta válida del operador.

    Raises:
        TypeError: Si la pregunta no es texto.
        ValueError: Si la pregunta está vacía.
        EOFError: Si se cierra la entrada.
        KeyboardInterrupt: Si el operador interrumpe la pregunta.
    """
    return _solicitar_valor_parametro(pregunta, validar_periodo)


def solicitar_si_no(pregunta: str) -> bool:
    """Solicita una respuesta si/sí/no hasta obtener un booleano.

    Args:
        pregunta: Texto del consumidor; conserva sus espacios finales.

    Returns:
        True para si/sí o False para no, sin distinguir mayúsculas.

    Raises:
        TypeError: Si la pregunta no es texto.
        ValueError: Si la pregunta está vacía.
        EOFError: Si se cierra la entrada.
        KeyboardInterrupt: Si el operador interrumpe la pregunta.
    """
    return _solicitar_valor_parametro(pregunta, validar_si_no)


def solicitar_opciones(
    pregunta: str,
    menu_opciones: dict[str, str],
    *,
    codigo_todos: str | None = None,
) -> set[str]:
    """Muestra el menú y solicita un conjunto válido de códigos seleccionados.

    Args:
        pregunta: Texto del consumidor; conserva sus espacios finales.
        menu_opciones: Diccionario de códigos admitidos a etiquetas visibles.
        codigo_todos: Código opcional para seleccionar todo el menú.

    Returns:
        Códigos seleccionados sin duplicados ni garantía de orden.

    Raises:
        TypeError: Si la pregunta o el menú tienen tipos incorrectos.
        ValueError: Si la pregunta o el menú son inválidos.
        EOFError: Si se cierra la entrada.
        KeyboardInterrupt: Si el operador interrumpe la pregunta.
    """
    _recortar_texto_obligatorio(pregunta, "pregunta")
    _validar_menu_opciones(menu_opciones, codigo_todos)

    if codigo_todos is not None:
        print(f"  {codigo_todos} = Todos")
    for codigo_opcion, etiqueta_opcion in menu_opciones.items():
        print(f"  {codigo_opcion} = {etiqueta_opcion}")

    return _solicitar_valor_parametro(
        pregunta,
        lambda texto_seleccion: validar_opciones(
            texto_seleccion, menu_opciones, codigo_todos=codigo_todos
        ),
    )


def _solicitar_valor_parametro[T](
    pregunta: str, validar_respuesta: Callable[[str], T]
) -> T:
    """Lee y valida una respuesta, reintentando solo errores de contenido."""
    _recortar_texto_obligatorio(pregunta, "pregunta")

    while True:
        respuesta_operador = input(pregunta)
        try:
            return validar_respuesta(respuesta_operador)
        except ValueError as exc:
            # Los errores de tipo y la cancelación deben llegar al consumidor.
            print(f"Error: {exc}")
