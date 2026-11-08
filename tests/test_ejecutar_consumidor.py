"""Comprueba consumidores reales en procesos separados sin recursos de negocio."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

CODIGO_CONSUMIDOR = """
import json
import sys
from parametros_utils import Parametro, obtener_parametros

parametros = [
    Parametro("periodo", "periodo", "Periodo: ", ayuda="Mes YYYYMM", predeterminado="202503"),
    Parametro("confirmar", "si_no", "Continuar: ", predeterminado="si"),
    Parametro("opciones", "opciones", "Archivos: ", predeterminado="0", opciones={"2": "Clientes", "3": "Facturacion"}, codigo_todos="0"),
]
try:
    valores = obtener_parametros(parametros, descripcion="Consumidor de prueba")
except (EOFError, KeyboardInterrupt):
    print("Cancelado por el consumidor.", file=sys.stderr)
    raise SystemExit(1)
print("RESULTADO=" + json.dumps({
    "periodo": valores["periodo"].isoformat(),
    "confirmar": valores["confirmar"],
    "opciones": sorted(valores["opciones"]),
}))
"""


class PruebasProcesos(unittest.TestCase):
    def ejecutar(self, argumentos, entrada="", codigo=CODIGO_CONSUMIDOR):
        return subprocess.run(
            [sys.executable, "-X", "utf8", "-c", codigo, *argumentos],
            input=entrada,
            capture_output=True,
            encoding="utf-8",
            timeout=15,
            cwd=Path(sys.executable).parent,
            check=False,
        )

    def resultado(self, proceso):
        self.assertEqual(proceso.returncode, 0, proceso.stderr)
        return json.loads(proceso.stdout.rsplit("RESULTADO=", 1)[1])

    def test_automatico_funciona_con_entrada_cerrada_y_desde_otra_carpeta(self):
        proceso = self.ejecutar([])
        self.assertEqual(
            self.resultado(proceso),
            {"periodo": "2025-03-01", "confirmar": True, "opciones": ["2", "3"]},
        )
        self.assertNotIn("Periodo: ", proceso.stdout)
        self.assertEqual(proceso.stderr, "")

    def test_argumentos_historicos_y_omisiones_parciales(self):
        for argumentos, esperado in [
            (
                ["--periodo", "202401"],
                {"periodo": "2024-01-01", "confirmar": True, "opciones": ["2", "3"]},
            ),
            (
                ["--opciones", "3", "--confirmar", "NO"],
                {"periodo": "2025-03-01", "confirmar": False, "opciones": ["3"]},
            ),
        ]:
            with self.subTest(argumentos=argumentos):
                self.assertEqual(self.resultado(self.ejecutar(argumentos)), esperado)

    def test_ayuda_termina_sin_preguntar_ni_resolver_default_invalido(self):
        codigo = CODIGO_CONSUMIDOR.replace(
            'predeterminado="202503"', 'predeterminado="incorrecto"'
        )
        proceso = self.ejecutar(["--help"], codigo=codigo)
        self.assertEqual(proceso.returncode, 0)
        self.assertIn("--interactivo", proceso.stdout)
        self.assertIn("Mes YYYYMM", proceso.stdout)
        self.assertNotIn("RESULTADO=", proceso.stdout)
        self.assertEqual(proceso.stderr, "")

    def test_errores_cli_salen_con_dos_sin_preguntar(self):
        for argumentos in [
            ["--periodo", ""],
            ["--periodo", "202513"],
            ["--confirmar", "1"],
            ["--opciones", "0,99"],
            ["--opciones", "0,2"],
            ["--periodo"],
            ["--desconocido"],
            ["--per", "202503"],
            ["--interactivo", "--confirmar", "si"],
        ]:
            with self.subTest(argumentos=argumentos):
                proceso = self.ejecutar(argumentos)
                self.assertEqual(proceso.returncode, 2, proceso.stderr)
                self.assertNotIn("RESULTADO=", proceso.stdout)
                self.assertNotIn("Periodo: ", proceso.stdout)
                self.assertNotIn("Traceback", proceso.stderr)

    def test_interactivo_reintenta_y_entrega_valores_equivalentes(self):
        proceso = self.ejecutar(
            ["--interactivo"], "\n202513\n202401\nquizas\n NO \n0,2\n3,2,3\n"
        )
        esperado = self.resultado(
            self.ejecutar(
                ["--periodo", "202401", "--confirmar", "no", "--opciones", "3,2"]
            )
        )
        self.assertEqual(self.resultado(proceso), esperado)
        self.assertEqual(proceso.stdout.count("Error:"), 4)

    def test_cancelacion_la_traduce_el_consumidor(self):
        proceso = self.ejecutar(["--interactivo"], "202401\n")
        self.assertEqual(proceso.returncode, 1)
        self.assertIn("Cancelado por el consumidor", proceso.stderr)
        self.assertNotIn("RESULTADO=", proceso.stdout)
        self.assertNotIn("Traceback", proceso.stderr)

    def test_importar_no_configura_logging_ni_escribe_en_consola(self):
        codigo = """
import logging
raiz = logging.getLogger()
antes = list(raiz.handlers)
import parametros_utils
assert raiz.handlers == antes
assert len(parametros_utils.__all__) == 8
assert any(isinstance(h, logging.NullHandler) for h in logging.getLogger("parametros_utils").handlers)
"""
        proceso = self.ejecutar([], codigo=codigo)
        self.assertEqual(proceso.returncode, 0, proceso.stderr)
        self.assertEqual(proceso.stdout, "")
        self.assertEqual(proceso.stderr, "")


def main() -> int:
    resultado = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PruebasProcesos)
    )
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
