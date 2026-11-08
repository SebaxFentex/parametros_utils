"""Comprueba declaraciones de parámetros sin ejecutar tareas."""

import unittest
from datetime import date

import parametros_utils


class PruebasParametro(unittest.TestCase):
    def test_define_variantes_con_atributos_exclusivos(self):
        for nombre_clase in ("ParametroPeriodo", "ParametroSiNo", "ParametroOpciones"):
            self.assertTrue(hasattr(parametros_utils, nombre_clase), nombre_clase)
        definicion_periodo = parametros_utils.ParametroPeriodo(
            nombre="periodo", pregunta="Periodo: ", predeterminado="202503"
        )
        definicion_confirmacion = parametros_utils.ParametroSiNo(
            nombre="confirmar", pregunta="¿Continuar?: "
        )
        definicion_archivos = parametros_utils.ParametroOpciones(
            nombre="archivos",
            pregunta="Archivos: ",
            menu_opciones={"2": "Clientes"},
            codigo_todos="0",
        )
        self.assertIsInstance(definicion_periodo, parametros_utils.Parametro)
        self.assertEqual(definicion_periodo.predeterminado, "202503")
        for definicion in (definicion_periodo, definicion_confirmacion):
            self.assertFalse(hasattr(definicion, "menu_opciones"))
            self.assertFalse(hasattr(definicion, "codigo_todos"))
            self.assertFalse(hasattr(definicion, "tipo"))
        self.assertEqual(definicion_archivos.menu_opciones, {"2": "Clientes"})
        self.assertEqual(definicion_archivos.codigo_todos, "0")
        with self.assertRaises(TypeError):
            parametros_utils.Parametro(nombre="periodo", pregunta="Periodo: ")  # ty: ignore[call-non-callable]  # pyright: ignore[reportAbstractUsage]  # Instanciación inválida intencional de la base abstracta.
        parametros = parametros_utils.obtener_parametros(
            [definicion_periodo, definicion_confirmacion, definicion_archivos],
            descripcion="Variantes tipadas",
            argumentos=["--confirmar", "no", "--archivos", "0"],
        )
        self.assertIsInstance(parametros, parametros_utils.ParametrosResueltos)
        self.assertEqual(
            parametros.obtener_valor_parametro(definicion_periodo), date(2025, 3, 1)
        )
        self.assertIs(
            parametros.obtener_valor_parametro(definicion_confirmacion), False
        )
        self.assertEqual(parametros.obtener_valor_parametro(definicion_archivos), {"2"})

    def test_declara_tres_tipos_y_predeterminado_textual(self):
        self.assertTrue(hasattr(parametros_utils, "Parametro"), "Falta Parametro")
        definicion_periodo = parametros_utils.ParametroPeriodo(
            nombre="periodo",
            pregunta="Periodo: ",
            ayuda="Mes YYYYMM",
            predeterminado="202503",
        )
        self.assertEqual(definicion_periodo.nombre, "periodo")
        self.assertEqual(definicion_periodo.pregunta, "Periodo: ")
        self.assertEqual(definicion_periodo.predeterminado, "202503")
        parametros_utils.ParametroSiNo(nombre="confirmar", pregunta="¿Continuar?: ")
        parametros_utils.ParametroOpciones(
            nombre="archivos",
            pregunta="Archivos: ",
            menu_opciones={"1": "Uno"},
            codigo_todos="0",
        )

    def test_no_interpreta_predeterminado_al_declarar(self):
        definicion_periodo = parametros_utils.ParametroPeriodo(
            nombre="periodo", pregunta="Periodo: ", predeterminado="invalido"
        )
        self.assertEqual(definicion_periodo.predeterminado, "invalido")

    def test_rechaza_nombres_reservados_o_invalidos(self):
        for nombre in [
            "",
            " ",
            "--periodo",
            "1periodo",
            "con espacio",
            "con-guion",
            "interactivo",
            "help",
            "h",
        ]:
            with self.subTest(nombre=nombre), self.assertRaises(ValueError):
                parametros_utils.ParametroPeriodo(nombre=nombre, pregunta="Periodo: ")
        parametros_utils.ParametroPeriodo(nombre="año_cierre", pregunta="Periodo: ")

    def test_rechaza_campos_retirados_y_configuracion_ajena(self):
        for campos_adicionales in (
            {"tipo": "periodo"},
            {"opciones": {"1": "Uno"}},
            {"menu_opciones": {"1": "Uno"}},
            {"codigo_todos": "0"},
        ):
            campos_definicion: dict[str, object] = {
                "nombre": "periodo",
                "pregunta": "Periodo: ",
                **campos_adicionales,
            }
            with self.subTest(campos=campos_definicion), self.assertRaises(TypeError):
                parametros_utils.ParametroPeriodo(**campos_definicion)  # ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]  # Configuración ajena intencional.
        with self.assertRaises(ValueError):
            parametros_utils.ParametroOpciones(
                nombre="archivos",
                pregunta="Archivos: ",
                menu_opciones={"0": "Cero"},
                codigo_todos="0",
            )

    def test_rechaza_textos_de_configuracion_invalidos(self):
        for campos, error in [
            (dict(pregunta=" "), ValueError),
            (dict(pregunta=None), TypeError),
            (dict(ayuda=None), TypeError),
            (dict(predeterminado=202503), TypeError),
            (dict(nombre=None), TypeError),
        ]:
            campos_definicion: dict[str, object] = dict(
                nombre="periodo", pregunta="Periodo: "
            )
            campos_definicion.update(campos)
            with self.subTest(campos=campos), self.assertRaises(error):
                parametros_utils.ParametroPeriodo(**campos_definicion)  # ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]  # Tipos incorrectos intencionales.


def main() -> int:
    resultado = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PruebasParametro)
    )
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
