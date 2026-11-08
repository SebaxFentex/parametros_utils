"""Comprueba la interpretación de periodos sin configuración externa."""

import unittest
from datetime import date

import parametros_utils


class PruebasPeriodo(unittest.TestCase):
    def test_convierte_periodo_en_primer_dia(self):
        self.assertTrue(
            hasattr(parametros_utils, "validar_periodo"), "Falta validar_periodo"
        )
        self.assertEqual(parametros_utils.validar_periodo("202503"), date(2025, 3, 1))

    def test_recorta_solo_espacios_exteriores(self):
        self.assertEqual(
            parametros_utils.validar_periodo(" \t202502\n"), date(2025, 2, 1)
        )
        with self.assertRaises(ValueError):
            parametros_utils.validar_periodo("2025 03")

    def test_admite_limites_del_tipo_date(self):
        for texto, esperado in [("000101", date.min), ("999912", date(9999, 12, 1))]:
            with self.subTest(texto=texto):
                self.assertEqual(parametros_utils.validar_periodo(texto), esperado)

    def test_rechaza_contenido_invalido(self):
        for texto in [
            "",
            "  ",
            "20250",
            "2025031",
            "202500",
            "202513",
            "000001",
            "2025-03",
            "２０２５０３",
            "²02503",
            "2025\n03",
        ]:
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                parametros_utils.validar_periodo(texto)

    def test_rechaza_tipos_no_textuales(self):
        for valor in [None, 202503, True, date(2025, 3, 1), b"202503"]:
            with self.subTest(tipo=type(valor).__name__), self.assertRaises(TypeError):
                parametros_utils.validar_periodo(valor)  # ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]  # Tipo incorrecto intencional.

    def test_validador_no_escribe_en_consola(self):
        from contextlib import redirect_stderr, redirect_stdout
        from io import StringIO

        salida, errores = StringIO(), StringIO()
        with redirect_stdout(salida), redirect_stderr(errores):
            parametros_utils.validar_periodo("202503")
            with self.assertRaises(ValueError):
                parametros_utils.validar_periodo("invalido")
        self.assertEqual(salida.getvalue(), "")
        self.assertEqual(errores.getvalue(), "")


def main() -> int:
    resultado = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PruebasPeriodo)
    )
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
