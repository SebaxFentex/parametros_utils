"""Comprueba preguntas, reintentos y cancelación sin requerir un humano."""

import unittest
from contextlib import redirect_stdout
from datetime import date
from io import StringIO
from unittest.mock import patch

import parametros_utils


class PruebasPreguntas(unittest.TestCase):
    def test_solicita_periodo_y_reintenta(self):
        self.assertTrue(
            hasattr(parametros_utils, "solicitar_periodo"), "Falta solicitar_periodo"
        )
        salida = StringIO()
        with (
            patch("sys.stdin", StringIO("\n202513\n202503\n")),
            redirect_stdout(salida),
        ):
            resultado = parametros_utils.solicitar_periodo("Mes de facturación: ")
        self.assertEqual(resultado, date(2025, 3, 1))
        self.assertEqual(salida.getvalue().count("Mes de facturación: "), 3)
        self.assertEqual(salida.getvalue().count("Error:"), 2)

    def test_solicita_si_no_y_reintenta(self):
        salida = StringIO()
        with patch("sys.stdin", StringIO("quizás\n SÍ \n")), redirect_stdout(salida):
            self.assertIs(parametros_utils.solicitar_si_no("¿Actualizar?: "), True)
        self.assertIn("Error:", salida.getvalue())
        self.assertEqual(salida.getvalue().count("¿Actualizar?: "), 2)

    def test_muestra_menu_recibido_y_reintenta(self):
        salida = StringIO()
        menu = {"2": "Clientes", "3": "Facturación"}
        with patch("sys.stdin", StringIO("0,2\n99\n3,2\n")), redirect_stdout(salida):
            resultado = parametros_utils.solicitar_opciones(
                "Archivos del cierre: ", menu, codigo_todos="0"
            )
        self.assertEqual(resultado, {"2", "3"})
        self.assertIn("2 = Clientes", salida.getvalue())
        self.assertIn("3 = Facturación", salida.getvalue())
        self.assertIn("0 = Todos", salida.getvalue())
        self.assertEqual(salida.getvalue().count("Error:"), 2)

    def test_menu_sin_todos_no_muestra_codigo_inventado(self):
        salida = StringIO()
        with patch("sys.stdin", StringIO("1\n")), redirect_stdout(salida):
            parametros_utils.solicitar_opciones("Escoge: ", {"1": "Uno"})
        self.assertNotIn("Todos", salida.getvalue())

    def test_propaga_cancelaciones(self):
        llamadas = [
            ("periodo", lambda: parametros_utils.solicitar_periodo("Periodo: ")),
            ("si_no", lambda: parametros_utils.solicitar_si_no("¿Continuar?: ")),
            (
                "opciones",
                lambda: parametros_utils.solicitar_opciones("Opciones: ", {"1": "Uno"}),
            ),
        ]
        for nombre, funcion in llamadas:
            for error in (EOFError, KeyboardInterrupt):
                with (
                    self.subTest(funcion=nombre, error=error.__name__),
                    patch("builtins.input", side_effect=error),
                    redirect_stdout(StringIO()),
                    self.assertRaises(error),
                ):
                    funcion()

    def test_configuracion_invalida_no_inicia_lectura(self):
        with patch(
            "builtins.input", side_effect=AssertionError("No debe preguntar")
        ) as entrada:
            with self.assertRaises(ValueError):
                parametros_utils.solicitar_opciones("Opciones: ", {}, codigo_todos="0")
            with self.assertRaises(ValueError):
                parametros_utils.solicitar_periodo(" ")
            with self.assertRaises(TypeError):
                parametros_utils.solicitar_si_no(None)  # ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]  # Tipo incorrecto intencional.
        entrada.assert_not_called()


def main() -> int:
    resultado = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PruebasPreguntas)
    )
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
