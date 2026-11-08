"""Definiciones de parámetros y operaciones propias de cada variante."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from ._preguntas import solicitar_opciones, solicitar_periodo, solicitar_si_no
from ._validacion import (
    _recortar_texto_obligatorio,
    _validar_menu_opciones,
    validar_opciones,
    validar_periodo,
    validar_si_no,
)

if TYPE_CHECKING:
    from ._resultados import ParametrosResueltos


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
        Las definiciones se distinguen por identidad, no por igualdad de campos.
        No contienen el valor resuelto de ninguna ejecución.
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
        if self.predeterminado is not None:
            _comprobar_tipo_textual(self.predeterminado, "predeterminado")

    def _resolver_valor_automatico(
        self, parametros: ParametrosResueltos, entrada_textual: str
    ) -> None:
        """Interpreta y guarda el argumento o predeterminado de esta definición."""
        valor_parametro = self._interpretar_valor_parametro(entrada_textual)
        self._guardar_valor_parametro(parametros, valor_parametro)

    def _resolver_valor_interactivo(self, parametros: ParametrosResueltos) -> None:
        """Solicita y guarda la respuesta validada para esta definición."""
        valor_parametro = self._solicitar_valor_parametro()
        self._guardar_valor_parametro(parametros, valor_parametro)

    @abstractmethod
    def _interpretar_valor_parametro(self, entrada_textual: str) -> T:
        """Interpreta una entrada textual según el contrato de la variante."""
        raise NotImplementedError

    @abstractmethod
    def _solicitar_valor_parametro(self) -> T:
        """Solicita y valida una respuesta con la configuración de la variante."""
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

    def _solicitar_valor_parametro(self) -> date:
        """Solicita un periodo válido con la pregunta del consumidor."""
        return solicitar_periodo(self.pregunta)

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

    def _solicitar_valor_parametro(self) -> bool:
        """Solicita una respuesta si/no con la pregunta del consumidor."""
        return solicitar_si_no(self.pregunta)

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

    def _solicitar_valor_parametro(self) -> set[str]:
        """Muestra el menú y solicita una selección de códigos válida."""
        return solicitar_opciones(
            self.pregunta, self.menu_opciones, codigo_todos=self.codigo_todos
        )

    def _guardar_valor_parametro(
        self, parametros: ParametrosResueltos, valor_parametro: set[str]
    ) -> None:
        """Guarda los códigos de esta definición en el resultado de la ejecución."""
        parametros._selecciones_opciones[self] = valor_parametro

    def _leer_valor_parametro(self, parametros: ParametrosResueltos) -> set[str]:
        """Recupera los códigos resueltos para esta definición."""
        return parametros._selecciones_opciones[self]


def _comprobar_tipo_textual(entrada_textual: object, nombre_campo: str) -> None:
    """Comprueba el tipo textual sin exigir contenido ni interpretarlo."""
    if not isinstance(entrada_textual, str):
        raise TypeError(
            f"El campo {nombre_campo} debe ser texto; "
            f"llegó {type(entrada_textual).__name__}."
        )
