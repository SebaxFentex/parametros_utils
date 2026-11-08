"""Comprueba las respuestas si/no y su retorno booleano."""

import unittest

import parametros_utils


class PruebasSiNo(unittest.TestCase):
    def test_devuelve_booleanos(self):
        self.assertTrue(
            hasattr(parametros_utils, "validar_si_no"), "Falta validar_si_no"
        )
        for texto, esperado in [
            ("si", True),
            ("sí", True),
            ("no", False),
            (" SÍ ", True),
            ("\tNO\n", False),
            ("Si", True),
        ]:
            with self.subTest(texto=texto):
                self.assertIs(
                    parametros_utils.validar_si_no(respuesta_si_no=texto), esperado
                )

    def test_rechaza_variantes_no_acordadas(self):
        for texto in [
            "",
            " ",
            "s",
            "n",
            "1",
            "0",
            "true",
            "false",
            "yes",
            "s i",
            "si no",
        ]:
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                parametros_utils.validar_si_no(texto)

    def test_rechaza_tipos_no_textuales(self):
        for valor in [None, True, False, 1, b"si"]:
            with self.subTest(tipo=type(valor).__name__), self.assertRaises(TypeError):
                parametros_utils.validar_si_no(valor)  # ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]  # Tipo incorrecto intencional.


def main() -> int:
    resultado = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PruebasSiNo)
    )
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
