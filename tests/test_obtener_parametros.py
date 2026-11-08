"""Comprueba resolución completa y separación entre ambos modos."""

import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from io import StringIO
from typing import assert_type
from unittest.mock import patch

import parametros_utils


def crear_definiciones_parametros() -> tuple[
    parametros_utils.ParametroPeriodo,
    parametros_utils.ParametroSiNo,
    parametros_utils.ParametroOpciones,
]:
    """Crea las tres definiciones reutilizadas dentro de cada prueba."""
    return (
        parametros_utils.ParametroPeriodo(
            nombre="periodo",
            pregunta="Periodo: ",
            ayuda="Mes YYYYMM",
            predeterminado="202503",
        ),
        parametros_utils.ParametroSiNo(
            nombre="confirmar", pregunta="¿Continuar?: ", predeterminado="sí"
        ),
        parametros_utils.ParametroOpciones(
            nombre="opciones",
            pregunta="Archivos: ",
            predeterminado="0",
            menu_opciones={"2": "Clientes", "3": "Facturación"},
            codigo_todos="0",
        ),
    )


class PruebasResolucion(unittest.TestCase):
    def setUp(self):
        self.definiciones_parametros = crear_definiciones_parametros()
        (
            self.definicion_periodo,
            self.definicion_confirmacion,
            self.definicion_opciones,
        ) = self.definiciones_parametros

    def resolver_parametros(
        self, argumentos, definiciones_parametros=None
    ) -> parametros_utils.ParametrosResueltos:
        """Resuelve las definiciones de la prueba con argumentos explícitos."""
        return parametros_utils.obtener_parametros(
            self.definiciones_parametros
            if definiciones_parametros is None
            else definiciones_parametros,
            descripcion="Tarea de prueba",
            argumentos=argumentos,
        )

    def comprobar_valores_parametros(
        self,
        parametros: parametros_utils.ParametrosResueltos,
        periodo: date,
        confirmar: bool,
        codigos_seleccionados: set[str],
    ) -> None:
        """Comprueba los tres resultados mediante sus definiciones originales."""
        self.assertEqual(
            parametros.obtener_valor_parametro(self.definicion_periodo), periodo
        )
        self.assertIs(
            parametros.obtener_valor_parametro(self.definicion_confirmacion), confirmar
        )
        self.assertEqual(
            parametros.obtener_valor_parametro(self.definicion_opciones),
            codigos_seleccionados,
        )

    def comprobar_error_parametros(
        self, argumentos, definiciones_parametros=None, mensaje_esperado=None
    ):
        """Comprueba un error CLI y que no se haya solicitado entrada."""
        errores = StringIO()
        with (
            patch(
                "builtins.input",
                side_effect=AssertionError("Automático no puede preguntar"),
            ) as entrada,
            redirect_stderr(errores),
            self.assertRaises(SystemExit) as salida,
        ):
            self.resolver_parametros(argumentos, definiciones_parametros)
        self.assertEqual(salida.exception.code, 2)
        entrada.assert_not_called()
        if mensaje_esperado:
            self.assertIn(mensaje_esperado, errores.getvalue())

    def test_resuelve_predeterminados_sin_preguntar(self):
        self.assertTrue(
            hasattr(parametros_utils, "obtener_parametros"), "Falta obtener_parametros"
        )
        with patch("builtins.input", side_effect=AssertionError("No preguntar")):
            parametros = self.resolver_parametros([])
        self.comprobar_valores_parametros(
            parametros, date(2025, 3, 1), True, {"2", "3"}
        )

    def test_argumentos_explicitos_prevalecen_independientemente(self):
        for argumentos, periodo, confirmar, opciones in [
            (["--periodo", "202401"], date(2024, 1, 1), True, {"2", "3"}),
            (["--confirmar", "no"], date(2025, 3, 1), False, {"2", "3"}),
            (["--opciones", "3"], date(2025, 3, 1), True, {"3"}),
        ]:
            with self.subTest(argumentos=argumentos):
                self.comprobar_valores_parametros(
                    self.resolver_parametros(argumentos), periodo, confirmar, opciones
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
                self.comprobar_error_parametros(argumentos)

    def test_omitido_sin_predeterminado_falla_sin_preguntar(self):
        definiciones_parametros = [
            parametros_utils.ParametroPeriodo(nombre="periodo", pregunta="Periodo: ")
        ]
        self.comprobar_error_parametros([], definiciones_parametros, "--periodo")

    def test_predeterminado_invalido_solo_falla_si_se_utiliza(self):
        for predeterminado in ["", "202513"]:
            definicion_periodo = parametros_utils.ParametroPeriodo(
                nombre="periodo", pregunta="Periodo: ", predeterminado=predeterminado
            )
            definiciones_parametros = [definicion_periodo]
            with self.subTest(predeterminado=predeterminado):
                self.comprobar_error_parametros(
                    [], definiciones_parametros, "--periodo"
                )
                self.assertEqual(
                    self.resolver_parametros(
                        ["--periodo", "202401"], definiciones_parametros
                    ).obtener_valor_parametro(definicion_periodo),
                    date(2024, 1, 1),
                )

    def test_interactivo_pregunta_todo_sin_usar_predeterminados(self):
        salida = StringIO()
        with patch("sys.stdin", StringIO("\n202401\nno\n3\n")), redirect_stdout(salida):
            parametros = self.resolver_parametros(["--interactivo"])
        self.comprobar_valores_parametros(parametros, date(2024, 1, 1), False, {"3"})
        self.assertEqual(salida.getvalue().count("Periodo: "), 2)

    def test_ambas_vias_entregan_los_mismos_tipos_y_valores(self):
        parametros_automaticos = self.resolver_parametros(
            ["--periodo", "202401", "--confirmar", "no", "--opciones", "3,2"]
        )
        with (
            patch("sys.stdin", StringIO("202401\nno\n3,2\n")),
            redirect_stdout(StringIO()),
        ):
            parametros_interactivos = self.resolver_parametros(["--interactivo"])
        for parametros in (parametros_automaticos, parametros_interactivos):
            self.comprobar_valores_parametros(
                parametros, date(2024, 1, 1), False, {"2", "3"}
            )
            self.assertIs(
                type(parametros.obtener_valor_parametro(self.definicion_periodo)), date
            )
            self.assertIs(
                type(parametros.obtener_valor_parametro(self.definicion_confirmacion)),
                bool,
            )
            self.assertIs(
                type(parametros.obtener_valor_parametro(self.definicion_opciones)), set
            )

    def test_rechaza_mezcla_de_modos_antes_de_preguntar(self):
        for nombre, valor in [
            ("periodo", "202503"),
            ("confirmar", "no"),
            ("opciones", ""),
        ]:
            with self.subTest(nombre=nombre):
                self.comprobar_error_parametros(
                    ["--interactivo", f"--{nombre}", valor],
                    mensaje_esperado="--interactivo",
                )

    def test_ayuda_no_pregunta_ni_valida_predeterminados(self):
        definiciones_parametros = [
            parametros_utils.ParametroPeriodo(
                nombre="periodo",
                pregunta="Periodo: ",
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
                self.resolver_parametros(argumentos, definiciones_parametros)
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
                self.comprobar_error_parametros(argumentos)

    def test_propaga_cancelacion_sin_devolver_resultado_parcial(self):
        for error in (EOFError, KeyboardInterrupt):
            with (
                self.subTest(error=error.__name__),
                patch("builtins.input", side_effect=["202401", error]),
                redirect_stdout(StringIO()),
                self.assertRaises(error),
            ):
                self.resolver_parametros(["--interactivo"])

    def test_usa_sys_argv_si_no_se_proporcionan_argumentos(self):
        with patch("sys.argv", ["tarea", "--confirmar", "no"]):
            parametros = parametros_utils.obtener_parametros(
                self.definiciones_parametros, descripcion="Tarea"
            )
        self.assertIs(
            parametros.obtener_valor_parametro(self.definicion_confirmacion), False
        )

    def test_rechaza_declaraciones_duplicadas_y_tipos_incorrectos(self):
        definicion_periodo = self.definicion_periodo
        for definiciones_parametros, error in [
            ([definicion_periodo, definicion_periodo], ValueError),
            (["periodo"], TypeError),
            ("periodo", TypeError),
            (None, TypeError),
        ]:
            with (
                self.subTest(definiciones=definiciones_parametros),
                self.assertRaises(error),
            ):
                if definiciones_parametros is not None:
                    self.resolver_parametros([], definiciones_parametros)
                else:
                    parametros_utils.obtener_parametros(
                        None,  # ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]  # Secuencia incorrecta intencional.
                        descripcion="Tarea",
                        argumentos=[],
                    )
        for argumentos in ["--help", [1], 1]:
            with self.subTest(argumentos=argumentos), self.assertRaises(TypeError):
                self.resolver_parametros(argumentos)

    def test_admite_identificadores_que_coinciden_con_atributos_de_namespace(self):
        for nombre_parametro in ("__dict__", "__class__", "_get_kwargs", "año_cierre"):
            definicion_periodo = parametros_utils.ParametroPeriodo(
                nombre=nombre_parametro, pregunta="Periodo: "
            )
            with self.subTest(nombre=nombre_parametro):
                parametros = self.resolver_parametros(
                    [f"--{nombre_parametro}", "202401"], [definicion_periodo]
                )
                self.assertEqual(
                    parametros.obtener_valor_parametro(definicion_periodo),
                    date(2024, 1, 1),
                )

    def test_rechaza_definiciones_ajenas_aunque_tengan_los_mismos_campos(self):
        parametros = self.resolver_parametros([])
        periodo_ajeno, confirmacion_ajena, opciones_ajenas = (
            crear_definiciones_parametros()
        )
        consultas_ajenas = (
            lambda: parametros.obtener_valor_parametro(periodo_ajeno),
            lambda: parametros.obtener_valor_parametro(confirmacion_ajena),
            lambda: parametros.obtener_valor_parametro(opciones_ajenas),
        )
        for consultar_definicion_ajena in consultas_ajenas:
            with self.subTest(consulta=consultar_definicion_ajena):
                with self.assertRaisesRegex(ValueError, "no pertenece"):
                    consultar_definicion_ajena()

    def test_rechaza_nombres_y_tipos_ajenos_en_el_acceso_tipado(self):
        parametros = self.resolver_parametros([])
        for definicion_invalida in ("periodo", None, 42):
            with self.subTest(definicion=definicion_invalida):
                with self.assertRaisesRegex(TypeError, "definición"):
                    parametros.obtener_valor_parametro(definicion_invalida)  # ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]  # Tipos incorrectos intencionales.

    def test_conserva_tipos_estaticos_por_definicion(self):
        parametros = parametros_utils.obtener_parametros(
            self.definiciones_parametros, descripcion="Tipos", argumentos=[]
        )
        periodo = assert_type(
            parametros.obtener_valor_parametro(self.definicion_periodo), date
        )
        confirmar = assert_type(
            parametros.obtener_valor_parametro(self.definicion_confirmacion), bool
        )
        codigos_seleccionados = assert_type(
            parametros.obtener_valor_parametro(self.definicion_opciones), set[str]
        )
        self.assertEqual(periodo.strftime("%Y%m"), "202503")
        self.assertIs(confirmar, True)
        self.assertEqual(codigos_seleccionados, {"2", "3"})

    def test_reutiliza_definiciones_sin_mezclar_ejecuciones(self):
        primeros_parametros = self.resolver_parametros(
            ["--periodo", "202401", "--opciones", "2"]
        )
        siguientes_parametros = self.resolver_parametros(
            ["--periodo", "202402", "--opciones", "3"]
        )
        with (
            patch("builtins.input", side_effect=["202403", EOFError]),
            redirect_stdout(StringIO()),
            self.assertRaises(EOFError),
        ):
            self.resolver_parametros(["--interactivo"])
        self.comprobar_valores_parametros(
            primeros_parametros, date(2024, 1, 1), True, {"2"}
        )
        self.comprobar_valores_parametros(
            siguientes_parametros, date(2024, 2, 1), True, {"3"}
        )
        self.comprobar_valores_parametros(
            self.resolver_parametros([]), date(2025, 3, 1), True, {"2", "3"}
        )

    def test_resuelve_dos_periodos_con_nombres_distintos(self):
        definicion_inicio = parametros_utils.ParametroPeriodo(
            nombre="periodo_inicio", pregunta="Desde: "
        )
        definicion_fin = parametros_utils.ParametroPeriodo(
            nombre="periodo_fin", pregunta="Hasta: "
        )
        parametros = self.resolver_parametros(
            ["--periodo_inicio", "202401", "--periodo_fin", "202412"],
            (definicion_inicio, definicion_fin),
        )
        self.assertEqual(
            parametros.obtener_valor_parametro(definicion_inicio), date(2024, 1, 1)
        )
        self.assertEqual(
            parametros.obtener_valor_parametro(definicion_fin), date(2024, 12, 1)
        )

    def test_valida_menu_mutado_antes_de_preguntar(self):
        self.definicion_opciones.menu_opciones.clear()
        with (
            patch(
                "builtins.input", side_effect=AssertionError("No debe preguntar")
            ) as entrada,
            self.assertRaises(ValueError),
        ):
            self.resolver_parametros(["--interactivo"])
        entrada.assert_not_called()

    def test_no_expone_acceso_de_diccionario_por_nombre(self):
        parametros = self.resolver_parametros([])
        self.assertFalse(hasattr(parametros, "__getitem__"))
        self.assertFalse(hasattr(parametros, "keys"))
        self.assertFalse(hasattr(parametros, "origen"))
        self.assertFalse(hasattr(parametros, "modo"))

    def test_no_emite_salida_en_automatico_correcto(self):
        salida, errores = StringIO(), StringIO()
        with redirect_stdout(salida), redirect_stderr(errores):
            self.resolver_parametros([])
        self.assertEqual(salida.getvalue(), "")
        self.assertEqual(errores.getvalue(), "")


def main() -> int:
    resultado = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PruebasResolucion)
    )
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
