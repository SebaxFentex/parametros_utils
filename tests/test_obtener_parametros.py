"""Comprueba resolución completa y separación entre ambos modos."""

import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from io import StringIO
from unittest.mock import patch

import parametros_utils


def declaraciones():
    return [
        parametros_utils.Parametro(
            "periodo",
            "periodo",
            "Periodo: ",
            ayuda="Mes YYYYMM",
            predeterminado="202503",
        ),
        parametros_utils.Parametro(
            "confirmar", "si_no", "¿Continuar?: ", predeterminado="sí"
        ),
        parametros_utils.Parametro(
            "opciones",
            "opciones",
            "Archivos: ",
            predeterminado="0",
            opciones={"2": "Clientes", "3": "Facturación"},
            codigo_todos="0",
        ),
    ]


class PruebasResolucion(unittest.TestCase):
    def resolver(self, argumentos, parametros=None):
        return parametros_utils.obtener_parametros(
            declaraciones() if parametros is None else parametros,
            descripcion="Tarea de prueba",
            argumentos=argumentos,
        )

    def comprobar_error(self, argumentos, parametros=None, texto=None):
        errores = StringIO()
        with (
            patch(
                "builtins.input",
                side_effect=AssertionError("Automático no puede preguntar"),
            ) as entrada,
            redirect_stderr(errores),
            self.assertRaises(SystemExit) as salida,
        ):
            self.resolver(argumentos, parametros)
        self.assertEqual(salida.exception.code, 2)
        entrada.assert_not_called()
        if texto:
            self.assertIn(texto, errores.getvalue())

    def test_resuelve_predeterminados_sin_preguntar(self):
        self.assertTrue(
            hasattr(parametros_utils, "obtener_parametros"), "Falta obtener_parametros"
        )
        with patch("builtins.input", side_effect=AssertionError("No preguntar")):
            resultado = self.resolver([])
        self.assertEqual(
            resultado,
            {"periodo": date(2025, 3, 1), "confirmar": True, "opciones": {"2", "3"}},
        )

    def test_argumentos_explicitos_prevalecen_independientemente(self):
        for argumentos, periodo, confirmar, opciones in [
            (["--periodo", "202401"], date(2024, 1, 1), True, {"2", "3"}),
            (["--confirmar", "no"], date(2025, 3, 1), False, {"2", "3"}),
            (["--opciones", "3"], date(2025, 3, 1), True, {"3"}),
        ]:
            with self.subTest(argumentos=argumentos):
                self.assertEqual(
                    self.resolver(argumentos),
                    dict(periodo=periodo, confirmar=confirmar, opciones=opciones),
                )

    def test_invalido_explicito_no_activa_predeterminado(self):
        for argumentos in [
            ["--periodo", ""],
            ["--periodo", "202513"],
            ["--confirmar", "quizás"],
            ["--opciones", "0,99"],
            ["--opciones", "0,2"],
        ]:
            with self.subTest(argumentos=argumentos):
                self.comprobar_error(argumentos)

    def test_omitido_sin_predeterminado_falla_sin_preguntar(self):
        parametros = [parametros_utils.Parametro("periodo", "periodo", "Periodo: ")]
        self.comprobar_error([], parametros, "--periodo")

    def test_predeterminado_invalido_solo_falla_si_se_utiliza(self):
        for valor in ["", "202513"]:
            parametros = [
                parametros_utils.Parametro(
                    "periodo", "periodo", "Periodo: ", predeterminado=valor
                )
            ]
            with self.subTest(valor=valor):
                self.comprobar_error([], parametros, "--periodo")
                self.assertEqual(
                    self.resolver(["--periodo", "202401"], parametros),
                    {"periodo": date(2024, 1, 1)},
                )

    def test_interactivo_pregunta_todo_sin_usar_predeterminados(self):
        salida = StringIO()
        with patch("sys.stdin", StringIO("\n202401\nno\n3\n")), redirect_stdout(salida):
            resultado = self.resolver(["--interactivo"])
        self.assertEqual(
            resultado, dict(periodo=date(2024, 1, 1), confirmar=False, opciones={"3"})
        )
        self.assertEqual(salida.getvalue().count("Periodo: "), 2)

    def test_ambas_vias_entregan_los_mismos_tipos_y_valores(self):
        automatico = self.resolver(
            ["--periodo", "202401", "--confirmar", "no", "--opciones", "3,2"]
        )
        with (
            patch("sys.stdin", StringIO("202401\nno\n3,2\n")),
            redirect_stdout(StringIO()),
        ):
            interactivo = self.resolver(["--interactivo"])
        self.assertEqual(automatico, interactivo)
        self.assertEqual(set(automatico), {"periodo", "confirmar", "opciones"})
        self.assertIs(type(automatico["periodo"]), date)
        self.assertIs(type(automatico["confirmar"]), bool)
        self.assertIs(type(automatico["opciones"]), set)

    def test_rechaza_mezcla_de_modos_antes_de_preguntar(self):
        for nombre, valor in [
            ("periodo", "202503"),
            ("confirmar", "no"),
            ("opciones", ""),
        ]:
            with self.subTest(nombre=nombre):
                self.comprobar_error(
                    ["--interactivo", f"--{nombre}", valor], texto="--interactivo"
                )

    def test_ayuda_no_pregunta_ni_valida_predeterminados(self):
        parametros = [
            parametros_utils.Parametro(
                "periodo",
                "periodo",
                "Periodo: ",
                ayuda="Mes histórico",
                predeterminado="incorrecto",
            )
        ]
        for argumentos in [["--help"], ["-h"], ["--interactivo", "--help"]]:
            salida = StringIO()
            with (
                self.subTest(argumentos=argumentos),
                patch("builtins.input", side_effect=AssertionError("No preguntar")),
                redirect_stdout(salida),
                self.assertRaises(SystemExit) as fin,
            ):
                self.resolver(argumentos, parametros)
            self.assertEqual(fin.exception.code, 0)
            self.assertIn("--periodo", salida.getvalue())
            self.assertIn("Mes histórico", salida.getvalue())

    def test_rechaza_argumentos_desconocidos_incompletos_y_abreviados(self):
        for argumentos in [
            ["--desconocido"],
            ["--periodo"],
            ["--per", "202503"],
            ["--interact"],
        ]:
            with self.subTest(argumentos=argumentos):
                self.comprobar_error(argumentos)

    def test_propaga_cancelacion_sin_devolver_resultado_parcial(self):
        for error in (EOFError, KeyboardInterrupt):
            with (
                self.subTest(error=error.__name__),
                patch("builtins.input", side_effect=["202401", error]),
                redirect_stdout(StringIO()),
                self.assertRaises(error),
            ):
                self.resolver(["--interactivo"])

    def test_usa_sys_argv_si_no_se_proporcionan_argumentos(self):
        with patch("sys.argv", ["tarea", "--confirmar", "no"]):
            resultado = parametros_utils.obtener_parametros(
                declaraciones(), descripcion="Tarea"
            )
        self.assertIs(resultado["confirmar"], False)

    def test_rechaza_declaraciones_duplicadas_y_tipos_incorrectos(self):
        parametro = declaraciones()[0]
        for parametros, error in [
            ([parametro, parametro], ValueError),
            (["periodo"], TypeError),
            ("periodo", TypeError),
            (None, TypeError),
        ]:
            with self.subTest(parametros=parametros), self.assertRaises(error):
                if parametros is not None:
                    self.resolver([], parametros)
                else:
                    parametros_utils.obtener_parametros(
                        None,  # ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]  # Secuencia incorrecta intencional.
                        descripcion="Tarea",
                        argumentos=[],
                    )
        for argumentos in ["--help", [1], 1]:
            with self.subTest(argumentos=argumentos), self.assertRaises(TypeError):
                self.resolver(argumentos)

    def test_no_emite_salida_en_automatico_correcto(self):
        salida, errores = StringIO(), StringIO()
        with redirect_stdout(salida), redirect_stderr(errores):
            self.resolver([])
        self.assertEqual(salida.getvalue(), "")
        self.assertEqual(errores.getvalue(), "")


def main() -> int:
    resultado = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PruebasResolucion)
    )
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
