# parametros_utils

Librería interna para declarar y resolver parámetros de ejecución de tareas.

## Contrato acordado

- La librería administra `argparse`, ayuda, modo interactivo y valores omitidos.
- El consumidor declara los parámetros y calcula sus predeterminados como texto.
- Periodo `YYYYMM`: `datetime.date` con día 1. Si/no: `bool`. Opciones: `set[str]` sin orden.
- Sin lectura de entorno, reglas de calendario del consumidor ni seguimiento del origen.
- Los contratos y ejemplos completos se documentan al terminar la implementación.

Estado: desarrollo local; no publicado, sin tag ni repositorio remoto.
