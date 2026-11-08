"""Interpretación y validación de valores textuales de parámetros."""

from datetime import date


def validar_periodo(texto: str) -> date:
    """Interpreta YYYYMM como el primer día del mes.

    Raises:
        TypeError: Si el valor no es texto.
        ValueError: Si no son seis dígitos ASCII o la fecha no es válida.
    """
    limpio = _texto_obligatorio(texto, "periodo")
    if len(limpio) != 6 or not limpio.isascii() or not limpio.isdigit():
        raise ValueError(
            "El periodo debe tener formato YYYYMM con seis dígitos de 0 a 9."
        )
    try:
        return date(int(limpio[:4]), int(limpio[4:]), 1)
    except ValueError as exc:
        raise ValueError(f"Periodo inválido: {limpio!r}. {exc}") from exc


def validar_si_no(texto: str) -> bool:
    """Interpreta si/sí/no sin distinguir mayúsculas ni espacios exteriores.

    Raises:
        TypeError: Si el valor no es texto.
        ValueError: Si no es una de las tres respuestas admitidas.
    """
    limpio = _texto_obligatorio(texto, "si/no").lower()
    if limpio in {"si", "sí"}:
        return True
    if limpio == "no":
        return False
    raise ValueError("La respuesta debe ser 'si', 'sí' o 'no'.")


def validar_opciones(
    texto: str,
    opciones: dict[str, str],
    *,
    codigo_todos: str | None = None,
) -> set[str]:
    """Interpreta códigos separados por coma y expande todos si aparece solo.

    Raises:
        TypeError: Si los valores o la configuración tienen tipos incorrectos.
        ValueError: Si el menú es inválido, hay códigos desconocidos, la selección
            queda vacía o se mezcla todos con otro código.
    """
    _validar_menu(opciones, codigo_todos)
    limpio = _texto_obligatorio(texto, "opciones")
    elegidas = {codigo.strip() for codigo in limpio.split(",") if codigo.strip()}
    if not elegidas:
        raise ValueError("Debes seleccionar al menos una opción.")
    desconocidas = elegidas - set(opciones)
    if codigo_todos is not None:
        desconocidas.discard(codigo_todos)
    if desconocidas:
        raise ValueError(f"Opciones desconocidas: {', '.join(sorted(desconocidas))}.")
    if codigo_todos in elegidas:
        if len(elegidas) != 1:
            raise ValueError(
                "El código de todos no puede mezclarse con otras opciones."
            )
        return set(opciones)
    return elegidas


def _validar_menu(opciones: object, codigo_todos: object) -> None:
    """Comprueba el menú del consumidor antes de interpretar o preguntar."""
    if not isinstance(opciones, dict):
        raise TypeError("Las opciones deben ser un diccionario de código a etiqueta.")
    if not opciones:
        raise ValueError("El menú de opciones no puede estar vacío.")
    for codigo, etiqueta in opciones.items():
        _validar_codigo(codigo)
        _texto_obligatorio(etiqueta, "etiqueta de opción")
    if codigo_todos is not None:
        _validar_codigo(codigo_todos)
        if codigo_todos in opciones:
            raise ValueError(
                "El código de todos no puede ser también una opción del menú."
            )


def _validar_codigo(codigo: object) -> None:
    """Rechaza códigos vacíos, con espacios exteriores o con separadores."""
    limpio = _texto_obligatorio(codigo, "código de opción")
    if limpio != codigo or "," in limpio:
        raise ValueError("Los códigos no admiten comas ni espacios exteriores.")


def _texto_obligatorio(valor: object, nombre: str) -> str:
    """Devuelve texto sin espacios exteriores, rechazando tipos y vacíos."""
    if not isinstance(valor, str):
        raise TypeError(
            f"El valor de {nombre} debe ser texto; llegó {type(valor).__name__}."
        )
    limpio = valor.strip()
    if not limpio:
        raise ValueError(f"El valor de {nombre} no puede estar vacío.")
    return limpio
