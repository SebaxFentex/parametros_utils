"""Comprueba declaraciones de parámetros sin ejecutar tareas."""

import unittest

import parametros_utils


class PruebasParametro(unittest.TestCase):
    def test_declara_tres_tipos_y_predeterminado_textual(self):
        self.assertTrue(hasattr(parametros_utils, "Parametro"), "Falta Parametro")
        parametro = parametros_utils.Parametro(
            "periodo",
            "periodo",
            "Periodo: ",
            ayuda="Mes YYYYMM",
            predeterminado="202503",
        )
        self.assertEqual(parametro.nombre, "periodo")
        self.assertEqual(parametro.pregunta, "Periodo: ")
        self.assertEqual(parametro.predeterminado, "202503")
        parametros_utils.Parametro("confirmar", "si_no", "¿Continuar?: ")
        parametros_utils.Parametro(
            "archivos",
            "opciones",
            "Archivos: ",
            opciones={"1": "Uno"},
            codigo_todos="0",
        )

    def test_no_interpreta_predeterminado_al_declarar(self):
        parametro = parametros_utils.Parametro(
            "periodo", "periodo", "Periodo: ", predeterminado="invalido"
        )
        self.assertEqual(parametro.predeterminado, "invalido")

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
                parametros_utils.Parametro(nombre, "periodo", "Periodo: ")
        parametros_utils.Parametro("año_cierre", "periodo", "Periodo: ")

    def test_rechaza_tipo_generico_y_campos_inconsistentes(self):
        for campos in [
            dict(tipo="texto"),
            dict(tipo=" periodo "),
            dict(tipo="opciones"),
            dict(tipo="periodo", opciones={"1": "Uno"}),
            dict(tipo="si_no", codigo_todos="0"),
            dict(tipo="opciones", opciones={"0": "Cero"}, codigo_todos="0"),
        ]:
            with self.subTest(campos=campos), self.assertRaises(ValueError):
                parametros_utils.Parametro("valor", pregunta="Valor: ", **campos)  # ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]  # Configuración inválida intencional.

    def test_rechaza_textos_de_configuracion_invalidos(self):
        for campos, error in [
            (dict(pregunta=" "), ValueError),
            (dict(pregunta=None), TypeError),
            (dict(ayuda=None), TypeError),
            (dict(predeterminado=202503), TypeError),
            (dict(nombre=None), TypeError),
            (dict(tipo=None), TypeError),
        ]:
            opciones: dict[str, object] = dict(
                nombre="periodo", tipo="periodo", pregunta="Periodo: "
            )
            opciones.update(campos)
            with self.subTest(campos=campos), self.assertRaises(error):
                parametros_utils.Parametro(**opciones)  # ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]  # Tipos incorrectos intencionales.


def main() -> int:
    resultado = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PruebasParametro)
    )
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
