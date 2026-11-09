"""Coordina la resolución completa de los parámetros de una tarea.

Comprueba las definiciones y selecciona el recorrido automático o interactivo.
Los detalles de consola pertenecen a argumentos y preguntas; los modelos enlazan
cada definición con su resultado y la validación interpreta las entradas.
"""

from collections.abc import Sequence

from ._argumentos import _analizar_argumentos_ejecucion, _ArgumentosEjecucion
from ._modelos import (
    ParametroOpciones,
    ParametroPeriodo,
    ParametroSiNo,
    ParametrosResueltos,
)
from ._preguntas import solicitar_opciones, solicitar_periodo, solicitar_si_no
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
    argumentos_ejecucion = _analizar_argumentos_ejecucion(
        definiciones_parametros, descripcion=descripcion, argumentos=argumentos
    )

    # Cada llamada crea su resultado; las definiciones nunca acumulan valores.
    parametros = ParametrosResueltos()
    if argumentos_ejecucion.interactivo:
        _resolver_parametros_interactivos(definiciones_parametros, parametros)
    else:
        _resolver_parametros_automaticos(
            definiciones_parametros, argumentos_ejecucion, parametros
        )

    return parametros


def _resolver_parametros_automaticos(
    definiciones_parametros: Sequence[
        ParametroPeriodo | ParametroSiNo | ParametroOpciones
    ],
    argumentos_ejecucion: _ArgumentosEjecucion,
    parametros: ParametrosResueltos,
) -> None:
    """Resuelve argumentos o predeterminados sin solicitar entrada al operador."""
    for definicion_parametro in definiciones_parametros:
        entrada_textual = argumentos_ejecucion.entradas_textuales[
            definicion_parametro.nombre
        ]

        # Solo la omisión activa el predeterminado; el texto vacío debe fallar.
        if entrada_textual is None:
            entrada_textual = definicion_parametro.predeterminado
        if entrada_textual is None:
            argumentos_ejecucion.informar_error(
                f"Falta --{definicion_parametro.nombre}: "
                "no se definió un valor predeterminado."
            )

        try:
            _resolver_valor_automatico(
                definicion_parametro, entrada_textual, parametros
            )
        except ValueError as exc:
            argumentos_ejecucion.informar_error(
                f"--{definicion_parametro.nombre}: {exc}"
            )


def _resolver_valor_automatico(
    definicion_parametro: ParametroPeriodo | ParametroSiNo | ParametroOpciones,
    entrada_textual: str,
    parametros: ParametrosResueltos,
) -> None:
    """Interpreta y guarda una entrada conservando el tipo de su definición."""
    # Cada rama conserva la relación de tipos incluso con genéricos invariantes.
    if isinstance(definicion_parametro, ParametroPeriodo):
        periodo = definicion_parametro._interpretar_valor_parametro(entrada_textual)
        definicion_parametro._guardar_valor_parametro(parametros, periodo)

    elif isinstance(definicion_parametro, ParametroSiNo):
        respuesta_si_no = definicion_parametro._interpretar_valor_parametro(
            entrada_textual
        )
        definicion_parametro._guardar_valor_parametro(parametros, respuesta_si_no)

    else:
        codigos_seleccionados = definicion_parametro._interpretar_valor_parametro(
            entrada_textual
        )
        definicion_parametro._guardar_valor_parametro(parametros, codigos_seleccionados)


def _resolver_parametros_interactivos(
    definiciones_parametros: Sequence[
        ParametroPeriodo | ParametroSiNo | ParametroOpciones
    ],
    parametros: ParametrosResueltos,
) -> None:
    """Solicita y guarda todas las respuestas en el orden de las definiciones."""
    for definicion_parametro in definiciones_parametros:
        if isinstance(definicion_parametro, ParametroPeriodo):
            periodo = solicitar_periodo(definicion_parametro.pregunta)
            definicion_parametro._guardar_valor_parametro(parametros, periodo)

        elif isinstance(definicion_parametro, ParametroSiNo):
            respuesta_si_no = solicitar_si_no(definicion_parametro.pregunta)
            definicion_parametro._guardar_valor_parametro(parametros, respuesta_si_no)

        else:
            codigos_seleccionados = solicitar_opciones(
                definicion_parametro.pregunta,
                definicion_parametro.menu_opciones,
                codigo_todos=definicion_parametro.codigo_todos,
            )
            definicion_parametro._guardar_valor_parametro(
                parametros, codigos_seleccionados
            )


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

        # El dict del consumidor sigue siendo mutable después de la declaración.
        if isinstance(definicion_parametro, ParametroOpciones):
            _validar_menu_opciones(
                definicion_parametro.menu_opciones, definicion_parametro.codigo_todos
            )
        definiciones_comprobadas.append(definicion_parametro)

    return tuple(definiciones_comprobadas)
