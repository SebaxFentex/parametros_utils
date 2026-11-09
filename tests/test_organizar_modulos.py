"""Comprueba las fronteras de responsabilidad del paquete plano."""

import ast
import inspect
import unittest
from pathlib import Path

import parametros_utils


def leer_importaciones(arbol_modulo: ast.Module) -> set[str]:
    """Obtiene los módulos importados sin ejecutar el código analizado."""
    importaciones: set[str] = set()
    for nodo in ast.walk(arbol_modulo):
        if isinstance(nodo, ast.Import):
            importaciones.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module is not None:
            importaciones.add(nodo.module)
    return importaciones


def leer_dependencias_paquete(arbol_modulo: ast.Module) -> set[str]:
    """Reconoce dependencias internas con imports relativos o absolutos."""
    dependencias = {
        nodo.module or ""
        for nodo in ast.walk(arbol_modulo)
        if isinstance(nodo, ast.ImportFrom) and nodo.level
    }
    for modulo in leer_importaciones(arbol_modulo):
        if modulo == "parametros_utils" or modulo.startswith("parametros_utils."):
            dependencias.add(modulo.removeprefix("parametros_utils."))
    return dependencias


class PruebasOrganizacion(unittest.TestCase):
    def test_modelos_no_dependen_de_consola_ni_resolucion(self):
        ruta_modelos = Path(inspect.getfile(parametros_utils.Parametro))
        arbol_modelos = ast.parse(ruta_modelos.read_text(encoding="utf-8"))
        dependencias_ajenas = leer_importaciones(arbol_modelos) & {
            "argparse",
            "_argumentos",
            "_preguntas",
            "_resolucion",
        }
        self.assertEqual(
            dependencias_ajenas,
            set(),
            "Los modelos no deben dirigir preguntas ni modos de ejecución.",
        )

    def test_argparse_se_limita_al_modulo_de_argumentos(self):
        carpeta_paquete = Path(inspect.getfile(parametros_utils)).parent
        for ruta_modulo in carpeta_paquete.glob("*.py"):
            if ruta_modulo.stem == "_argumentos":
                continue

            arbol_modulo = ast.parse(ruta_modulo.read_text(encoding="utf-8"))
            with self.subTest(modulo=ruta_modulo.name):
                self.assertNotIn("argparse", leer_importaciones(arbol_modulo))

    def test_mantiene_los_modulos_en_un_solo_nivel(self):
        carpeta_paquete = Path(inspect.getfile(parametros_utils)).parent
        for ruta_modulo in carpeta_paquete.rglob("*.py"):
            with self.subTest(modulo=ruta_modulo.relative_to(carpeta_paquete)):
                self.assertEqual(ruta_modulo.parent, carpeta_paquete)

    def test_validacion_no_depende_de_otras_capas(self):
        carpeta_paquete = Path(inspect.getfile(parametros_utils)).parent
        ruta_validacion = carpeta_paquete / "_validacion.py"
        arbol_validacion = ast.parse(ruta_validacion.read_text(encoding="utf-8"))
        self.assertEqual(leer_dependencias_paquete(arbol_validacion), set())

    def test_preguntas_solo_depende_de_validacion(self):
        carpeta_paquete = Path(inspect.getfile(parametros_utils)).parent
        ruta_preguntas = carpeta_paquete / "_preguntas.py"
        arbol_preguntas = ast.parse(ruta_preguntas.read_text(encoding="utf-8"))
        self.assertEqual(leer_dependencias_paquete(arbol_preguntas), {"_validacion"})


def main() -> int:
    resultado = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PruebasOrganizacion)
    )
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
