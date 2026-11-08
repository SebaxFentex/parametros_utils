"""Resultados de una ejecución con acceso por definición tipada."""

from dataclasses import dataclass, field
from datetime import date

from ._parametro import Parametro, ParametroOpciones, ParametroPeriodo, ParametroSiNo


@dataclass(slots=True)
class ParametrosResueltos:
    """Agrupa los resultados de una ejecución sin modificar sus definiciones.

    Se obtiene mediante obtener_parametros. Cada almacenamiento interno conserva
    el tipo concreto de su variante y usa la identidad de la definición como clave.
    """

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
            return definicion_parametro._leer_valor_parametro(self)
        except KeyError:
            raise ValueError(
                f"La definición {definicion_parametro.nombre!r} "
                "no pertenece a estos parámetros resueltos."
            ) from None
