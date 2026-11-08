"""Interpretación y validación de valores textuales de parámetros."""

from datetime import date


def validar_periodo(texto_periodo: str) -> date:
    """Convierte un periodo YYYYMM en una fecha con día 1.

    Args:
        texto_periodo: Seis dígitos ASCII, con espacios exteriores opcionales.

    Returns:
        Primer día del mes indicado, dentro de los límites del propio date.

    Raises:
        TypeError: Si el valor no es texto.
        ValueError: Si no son seis dígitos ASCII o la fecha no es válida.
    """
    periodo_recortado = _recortar_texto_obligatorio(texto_periodo, "periodo")
    if (
        len(periodo_recortado) != 6
        or not periodo_recortado.isascii()
        or not periodo_recortado.isdigit()
    ):
        raise ValueError(
            "El periodo debe tener formato YYYYMM con seis dígitos de 0 a 9."
        )
    try:
        return date(int(periodo_recortado[:4]), int(periodo_recortado[4:]), 1)
    except ValueError as exc:
        raise ValueError(f"Periodo inválido: {periodo_recortado!r}. {exc}") from exc


def validar_si_no(respuesta_si_no: str) -> bool:
    """Convierte si/sí en True y no en False, recortando espacios exteriores.

    Args:
        respuesta_si_no: Respuesta textual sin distinción de mayúsculas.

    Returns:
        Booleano correspondiente a una de las respuestas admitidas.

    Raises:
        TypeError: Si el valor no es texto.
        ValueError: Si no es una de las tres respuestas admitidas.
    """
    respuesta_normalizada = _recortar_texto_obligatorio(
        respuesta_si_no, "si/no"
    ).lower()
    if respuesta_normalizada in {"si", "sí"}:
        return True
    if respuesta_normalizada == "no":
        return False
    raise ValueError("La respuesta debe ser 'si', 'sí' o 'no'.")


def validar_opciones(
    texto_seleccion: str,
    menu_opciones: dict[str, str],
    *,
    codigo_todos: str | None = None,
) -> set[str]:
    """Devuelve los códigos seleccionados y expande todos cuando aparece solo.

    Args:
        texto_seleccion: Códigos separados por coma; se recorta cada fragmento.
        menu_opciones: Diccionario de códigos admitidos a etiquetas visibles.
        codigo_todos: Código opcional que representa todas las claves del menú.

    Returns:
        Conjunto no vacío de códigos textuales, sin duplicados ni garantía de orden.

    Raises:
        TypeError: Si los valores o la configuración tienen tipos incorrectos.
        ValueError: Si el menú es inválido, hay códigos desconocidos, la selección
            queda vacía o se mezcla todos con otro código.
    """
    _validar_menu_opciones(menu_opciones, codigo_todos)
    seleccion_recortada = _recortar_texto_obligatorio(texto_seleccion, "opciones")
    codigos_seleccionados = {
        codigo_opcion.strip()
        for codigo_opcion in seleccion_recortada.split(",")
        if codigo_opcion.strip()
    }
    if not codigos_seleccionados:
        raise ValueError("Debes seleccionar al menos una opción.")
    codigos_desconocidos = codigos_seleccionados - set(menu_opciones)
    if codigo_todos is not None:
        codigos_desconocidos.discard(codigo_todos)
    if codigos_desconocidos:
        raise ValueError(
            f"Códigos de opción desconocidos: {', '.join(sorted(codigos_desconocidos))}."
        )
    if codigo_todos in codigos_seleccionados:
        if len(codigos_seleccionados) != 1:
            raise ValueError(
                "El código de todos no puede mezclarse con otras opciones."
            )
        return set(menu_opciones)
    return codigos_seleccionados


def _validar_menu_opciones(menu_opciones: object, codigo_todos: object) -> None:
    """Comprueba el menú del consumidor antes de interpretar o preguntar."""
    if not isinstance(menu_opciones, dict):
        raise TypeError("Las opciones deben ser un diccionario de código a etiqueta.")
    if not menu_opciones:
        raise ValueError("El menú de opciones no puede estar vacío.")
    for codigo_opcion, etiqueta_opcion in menu_opciones.items():
        _validar_codigo_opcion(codigo_opcion)
        _recortar_texto_obligatorio(etiqueta_opcion, "etiqueta de opción")
    if codigo_todos is not None:
        _validar_codigo_opcion(codigo_todos)
        if codigo_todos in menu_opciones:
            raise ValueError(
                "El código de todos no puede ser también una opción del menú."
            )


def _validar_codigo_opcion(codigo_opcion: object) -> None:
    """Rechaza códigos vacíos, con espacios exteriores o con separadores."""
    codigo_recortado = _recortar_texto_obligatorio(codigo_opcion, "código de opción")
    if codigo_recortado != codigo_opcion or "," in codigo_recortado:
        raise ValueError("Los códigos no admiten comas ni espacios exteriores.")


def _recortar_texto_obligatorio(entrada_textual: object, nombre_campo: str) -> str:
    """Devuelve texto sin espacios exteriores, rechazando tipos y vacíos."""
    if not isinstance(entrada_textual, str):
        raise TypeError(
            f"El campo {nombre_campo} debe ser texto; "
            f"llegó {type(entrada_textual).__name__}."
        )
    texto_recortado = entrada_textual.strip()
    if not texto_recortado:
        raise ValueError(f"El campo {nombre_campo} no puede estar vacío.")
    return texto_recortado
