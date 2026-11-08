"""Comprueba selección, menús y código opcional de todos."""

import unittest

import parametros_utils

MENU = {"1": "Uno", "2": "Dos", "3": "Tres"}


class PruebasOpciones(unittest.TestCase):
    def test_devuelve_conjunto_sin_duplicados_ni_vacios(self):
        self.assertTrue(
            hasattr(parametros_utils, "validar_opciones"), "Falta validar_opciones"
        )
        self.assertEqual(
            parametros_utils.validar_opciones(
                texto_seleccion=" 3,2,,3, ", menu_opciones=MENU
            ),
            {"3", "2"},
        )

    def test_expande_codigo_todos_del_consumidor(self):
        self.assertEqual(
            parametros_utils.validar_opciones(" TODOS ", MENU, codigo_todos="TODOS"),
            set(MENU),
        )
        self.assertEqual(
            parametros_utils.validar_opciones("0,0", MENU, codigo_todos="0"), set(MENU)
        )

    def test_no_impone_codigo_cero(self):
        self.assertEqual(parametros_utils.validar_opciones("0", {"0": "Cero"}), {"0"})
        with self.assertRaises(ValueError):
            parametros_utils.validar_opciones("0", MENU)

    def test_rechaza_todos_mezclado(self):
        for texto in ["0,2", "2,0", "0,99", "0,2,99"]:
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                parametros_utils.validar_opciones(texto, MENU, codigo_todos="0")

    def test_rechaza_desconocidos_y_seleccion_vacia(self):
        for texto in ["", " ", ",,,", "99", "2,99", "1 2", "DOS"]:
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                parametros_utils.validar_opciones(texto, MENU)

    def test_rechaza_tipos_no_textuales(self):
        for valor in [None, 2, ["1"], {"1"}]:
            with self.subTest(tipo=type(valor).__name__), self.assertRaises(TypeError):
                parametros_utils.validar_opciones(valor, MENU)  # ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]  # Tipo incorrecto intencional.

    def test_rechaza_menu_mal_configurado(self):
        for menu, todos, error in [
            ({}, None, ValueError),
            ({"0": "Cero"}, "0", ValueError),
            ({" 1": "Uno"}, None, ValueError),
            ({"1,2": "Uno"}, None, ValueError),
            ({"": "Uno"}, None, ValueError),
            ({1: "Uno"}, None, TypeError),
            ({"1": 1}, None, TypeError),
            ({"1": " "}, None, ValueError),
            ([], None, TypeError),
            (MENU, " ", ValueError),
            (MENU, "0,9", ValueError),
            (MENU, 0, TypeError),
        ]:
            with self.subTest(menu=menu, todos=todos), self.assertRaises(error):
                parametros_utils.validar_opciones("1", menu, codigo_todos=todos)  # ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]  # Menú incorrecto intencional.

    def test_no_modifica_menu_del_consumidor(self):
        menu = dict(MENU)
        resultado = parametros_utils.validar_opciones("0", menu, codigo_todos="0")
        resultado.clear()
        self.assertEqual(menu, MENU)


def main() -> int:
    resultado = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PruebasOpciones)
    )
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
