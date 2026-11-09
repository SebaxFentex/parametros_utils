"""Define los parámetros y el acceso tipado a los resultados de una ejecución.

Las definiciones conservan configuración reutilizable; ParametrosResueltos guarda
los valores de una sola ejecución. Ambos lados del enlace tipado viven aquí para
que su colaboración sea visible. Este módulo depende de validación pura y no
selecciona modos, analiza argumentos ni solicita respuestas al operador.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date

from ._validacion import (
    _comprobar_tipo_textual,
    _recortar_texto_obligatorio,
    _validar_menu_opciones,
    validar_opciones,
    validar_periodo,
    validar_si_no,
)


# La identidad, no la igualdad de campos, vincula una definición con su resultado.
@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class Parametro[T](ABC):
    """Define la configuración común de una entrada cuyo resultado es de tipo T.

    Args:
        nombre: Identificador utilizado como opción de consola, sin guiones.
        pregunta: Pregunta del consumidor, incluidos sus espacios finales.
        ayuda: Descripción para la ayuda; si está vacía se usa la pregunta.
        predeterminado: Texto que se interpreta solo si falta el argumento
            automático. None exige un argumento explícito en ese modo.

    Raises:
        TypeError: Si se instancia la base abstracta o un campo tiene otro tipo.
        ValueError: Si el nombre o la pregunta son inválidos.

    Notes:
        Las definiciones no contienen el valor resuelto de ninguna ejecución.
        Cada variante interpreta su entrada y enlaza su tipo concreto con el
        almacenamiento de ParametrosResueltos, sin realizar interacción.
    """

    nombre: str
    pregunta: str
    ayuda: str = ""
    predeterminado: str | None = None

    def __post_init__(self) -> None:
        """Comprueba la configuración común sin interpretar el predeterminado."""
        nombre_parametro = _recortar_texto_obligatorio(
            self.nombre, "nombre del parámetro"
        )
        if (
            nombre_parametro != self.nombre
            or not nombre_parametro.isidentifier()
            or nombre_parametro in {"interactivo", "help", "h"}
        ):
            raise ValueError(
                "El nombre debe ser un identificador y no puede ser interactivo, help ni h."
            )

        _recortar_texto_obligatorio(self.pregunta, "pregunta")
        _comprobar_tipo_textual(self.ayuda, "ayuda")

        # Se comprueba el tipo ahora; el contenido solo se interpreta si se usa.
        if self.predeterminado is not None:
            _comprobar_tipo_textual(self.predeterminado, "predeterminado")

    @abstractmethod
    def _interpretar_valor_parametro(self, entrada_textual: str) -> T:
        """Interpreta una entrada textual según el contrato de la variante."""
        raise NotImplementedError

    @abstractmethod
    def _guardar_valor_parametro(
        self, parametros: ParametrosResueltos, valor_parametro: T
    ) -> None:
        """Guarda el resultado en el almacenamiento de su tipo concreto."""
        raise NotImplementedError

    @abstractmethod
    def _leer_valor_parametro(self, parametros: ParametrosResueltos) -> T:
        """Recupera el resultado asociado a esta definición concreta."""
        raise NotImplementedError


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class ParametroPeriodo(Parametro[date]):
    """Define un periodo YYYYMM cuyo resultado es una fecha con día 1."""

    def _interpretar_valor_parametro(self, entrada_textual: str) -> date:
        """Convierte el texto del periodo en el primer día del mes."""
        return validar_periodo(entrada_textual)

    def _guardar_valor_parametro(
        self, parametros: ParametrosResueltos, valor_parametro: date
    ) -> None:
        """Guarda la fecha de esta definición en el resultado de la ejecución."""
        parametros._periodos[self] = valor_parametro

    def _leer_valor_parametro(self, parametros: ParametrosResueltos) -> date:
        """Recupera la fecha resuelta para esta definición."""
        return parametros._periodos[self]


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class ParametroSiNo(Parametro[bool]):
    """Define una respuesta si/sí/no cuyo resultado es un booleano."""

    def _interpretar_valor_parametro(self, entrada_textual: str) -> bool:
        """Convierte una respuesta si/sí/no en su booleano correspondiente."""
        return validar_si_no(entrada_textual)

    def _guardar_valor_parametro(
        self, parametros: ParametrosResueltos, valor_parametro: bool
    ) -> None:
        """Guarda el booleano de esta definición en el resultado de la ejecución."""
        parametros._respuestas_si_no[self] = valor_parametro

    def _leer_valor_parametro(self, parametros: ParametrosResueltos) -> bool:
        """Recupera el booleano resuelto para esta definición."""
        return parametros._respuestas_si_no[self]


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class ParametroOpciones(Parametro[set[str]]):
    """Define una selección de códigos a partir del menú del consumidor.

    Args:
        menu_opciones: Diccionario obligatorio de código a etiqueta visible.
        codigo_todos: Código opcional para seleccionar todos los códigos del menú.

    Raises:
        TypeError: Si los campos comunes o el menú tienen tipos incorrectos.
        ValueError: Si los campos comunes o el menú son inválidos.
    """

    menu_opciones: dict[str, str]
    codigo_todos: str | None = None

    def __post_init__(self) -> None:
        """Comprueba los campos comunes y el menú exclusivo de esta variante."""
        super(ParametroOpciones, self).__post_init__()
        _validar_menu_opciones(self.menu_opciones, self.codigo_todos)

    def _interpretar_valor_parametro(self, entrada_textual: str) -> set[str]:
        """Interpreta y valida los códigos seleccionados contra el menú."""
        return validar_opciones(
            entrada_textual, self.menu_opciones, codigo_todos=self.codigo_todos
        )

    def _guardar_valor_parametro(
        self, parametros: ParametrosResueltos, valor_parametro: set[str]
    ) -> None:
        """Guarda los códigos de esta definición en el resultado de la ejecución."""
        parametros._selecciones_opciones[self] = valor_parametro

    def _leer_valor_parametro(self, parametros: ParametrosResueltos) -> set[str]:
        """Recupera los códigos resueltos para esta definición."""
        return parametros._selecciones_opciones[self]


@dataclass(slots=True)
class ParametrosResueltos:
    """Agrupa los resultados de una ejecución sin modificar sus definiciones.

    Se obtiene mediante obtener_parametros. Cada almacenamiento interno conserva
    el tipo concreto de su variante y usa la identidad de la definición como clave.
    """

    # Un diccionario heterogéneo perdería la relación entre definición y retorno.
    _periodos: dict[ParametroPeriodo, date] = field(
        default_factory=dict, init=False, repr=False
    )
    _respuestas_si_no: dict[ParametroSiNo, bool] = field(
        default_factory=dict, init=False, repr=False
    )
    _selecciones_opciones: dict[ParametroOpciones, set[str]] = field(
        default_factory=dict, init=False, repr=False
    )

    def obtener_valor_parametro[T](self, definicion_parametro: Parametro[T]) -> T:
        """Devuelve el valor resuelto para la definición original.

        Args:
            definicion_parametro: La misma instancia entregada a obtener_parametros,
                no una definición nueva con campos iguales ni el nombre textual.

        Returns:
            Fecha, booleano o conjunto de códigos, según el tipo de la definición.

        Raises:
            TypeError: Si no se recibe una definición de parámetro.
            ValueError: Si esa definición no pertenece al resultado de la ejecución.
        """
        if not isinstance(definicion_parametro, Parametro):
            raise TypeError("Se necesita una definición de parámetro, no su nombre.")

        try:
            # La variante recupera su tipo concreto sin convertir ni afirmar tipos.
            return definicion_parametro._leer_valor_parametro(self)
        except KeyError:
            raise ValueError(
                f"La definición {definicion_parametro.nombre!r} "
                "no pertenece a estos parámetros resueltos."
            ) from None
