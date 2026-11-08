"""Declaración de los parámetros de ejecución del consumidor."""

from dataclasses import dataclass
from typing import Literal

from ._validacion import _texto_obligatorio, _validar_menu


@dataclass(frozen=True, slots=True)
class Parametro:
    """Declara el nombre, tipo, pregunta y predeterminado textual de una entrada.

    El predeterminado se interpreta solo cuando falta el argumento en automático.
    Las opciones y el código de todos pertenecen únicamente al tipo opciones.

    Raises:
        TypeError: Si un campo tiene un tipo incorrecto.
        ValueError: Si el nombre, tipo, pregunta o menú es inválido.
    """

    nombre: str
    tipo: Literal["periodo", "si_no", "opciones"]
    pregunta: str
    ayuda: str = ""
    predeterminado: str | None = None
    opciones: dict[str, str] | None = None
    codigo_todos: str | None = None

    def __post_init__(self) -> None:
        nombre = _texto_obligatorio(self.nombre, "nombre del parámetro")
        if (
            nombre != self.nombre
            or not nombre.isidentifier()
            or nombre in {"interactivo", "help", "h"}
        ):
            raise ValueError(
                "El nombre debe ser un identificador y no puede ser interactivo, help ni h."
            )
        tipo = _texto_obligatorio(self.tipo, "tipo de parámetro")
        if tipo != self.tipo or tipo not in {"periodo", "si_no", "opciones"}:
            raise ValueError("El tipo debe ser periodo, si_no u opciones.")
        _texto_obligatorio(self.pregunta, "pregunta")
        _comprobar_texto(self.ayuda, "ayuda")
        if self.predeterminado is not None:
            _comprobar_texto(self.predeterminado, "predeterminado")
        if self.tipo == "opciones":
            if self.opciones is None:
                raise ValueError("Un parámetro de opciones necesita su menú.")
            _validar_menu(self.opciones, self.codigo_todos)
        elif self.opciones is not None or self.codigo_todos is not None:
            raise ValueError(
                "El menú y el código de todos solo se usan en parámetros de opciones."
            )


def _comprobar_texto(valor: object, nombre: str) -> None:
    """Comprueba el tipo textual sin exigir contenido ni interpretarlo."""
    if not isinstance(valor, str):
        raise TypeError(
            f"El campo {nombre} debe ser texto; llegó {type(valor).__name__}."
        )
