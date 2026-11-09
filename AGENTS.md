# AGENTS.md — parametros_utils

## Alcance y contrato

- Paquete interno Python >=3.14, layout `src/`, backend `uv_build`, sin dependencias de ejecución.
- API aprobada: `Parametro`, `ParametroPeriodo`, `ParametroSiNo`, `ParametroOpciones`, `ParametrosResueltos`, `obtener_parametros`, `validar_periodo`, `validar_si_no`, `validar_opciones`, `solicitar_periodo`, `solicitar_si_no`, `solicitar_opciones`.
- `Parametro[T]` es base abstracta (`frozen`, `slots`, `kw_only`, `eq=False`) con `nombre`, `pregunta`, `ayuda = ""` y `predeterminado: str | None = None`. No se instancia ni se amplía con tipos extra o plugin.
- Variantes cerradas: `ParametroPeriodo(Parametro[date])`, `ParametroSiNo(Parametro[bool])` y `ParametroOpciones(Parametro[set[str]])`; solo la última lleva `menu_opciones: dict[str, str]` obligatorio y `codigo_todos: str | None = None`. Sin campo `tipo` ni opciones heredadas.
- `obtener_parametros(definiciones_parametros: Sequence[ParametroPeriodo | ParametroSiNo | ParametroOpciones], *, descripcion: str, argumentos: Sequence[str] | None = None) -> ParametrosResueltos`. Sin resultados parciales ante cancelación.
- Acceso solo con `parametros.obtener_valor_parametro(definicion_parametro)`: misma instancia por identidad; instancia ajena `ValueError`; no definición `TypeError`. Sin acceso por cadenas ni `assert`/`cast`/`Any`.
- Las definiciones nunca guardan estado de ejecución.
- Los predeterminados son texto que se interpreta solo al usarse; el automático nunca pregunta.
- El periodo se interpreta como YYYYMM, recorta espacios exteriores y retorna date(año, mes, 1); los límites de año son los de date.
- Si/no acepta si/sí/no sin distinguir mayúsculas, recortando espacios exteriores.
- Opciones separadas por coma: recortar cada código, eliminar vacíos y duplicados, sin garantía de orden; selección vacía, desconocidos o todos mezclado con otro código son errores.
- Todos es opcional y el consumidor elige su código; no imponer 0.
- Automático: argumento explícito > predeterminado textual > error. Un inválido explícito nunca activa el predeterminado.
- Interactivo: pedir todos los parámetros, sin predeterminados ni mezcla con argumentos explícitos. Reintentar únicamente contenido inválido.
- EOFError y KeyboardInterrupt se propagan incluso desde obtener_parametros.
- TypeError por tipo incorrecto y ValueError por contenido inválido; errores CLI se traducen con analizador.error. Ayuda antes de validar predeterminados o preguntar.
- Glosario de dominio en el README: definicion, entrada textual, valor resuelto, menu, codigo_opcion, etiqueta_opcion, codigos_seleccionados, codigos_desconocidos.

## Desarrollo

- Leer README y normativa Tigo vigente antes de modificar. No migrar consumidores ni operar producción.
- Los menús, las preguntas y los errores interactivos son la salida solicitada por el consumidor; no convertirlos en logging.
- La librería no lee `.env` ni variables de entorno, no configura logging, no crea archivos y no calcula predeterminados. NullHandler en __init__.
- Incluir el marcador vacío `src/parametros_utils/py.typed` en wheel y sdist. Comprobar la inferencia de tipos desde el paquete instalado en un entorno aislado, sin resolver imports desde el código fuente del repositorio.
- No añadir __main__.py: no se solicitó un comando independiente de la librería.
- Tests ejecutables en tests/test_*.py con main(), usando unittest de stdlib, sin .env. Un .bat por test en Ejecutables/tests.
- Verificación: `uv sync --locked`; `uv run python -m unittest discover -s tests -v`; tests por archivo; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run ty check`; compileall; `uv build`; import desde wheel aislado.
- Ruff 0.17.4 y ty 0.0.99 son dependencias de desarrollo fijadas, no de ejecución. Cada supresión de tipos en un test corresponde a datos inválidos intencionales.
- Estructura plana dentro de `src/parametros_utils/`: no introducir un subpaquete `_interno` ni otro nivel para esta organización. Mantener el prefijo `_` en los módulos privados y `__init__.py` limitado a API y NullHandler.
- `_modelos.py` reúne definiciones, variantes y `ParametrosResueltos`. Mantener interpretación pura y enlace tipado por variante; no añadir preguntas, análisis de consola ni selección de modos a los modelos.
- `_validacion.py` concentra interpretación y comprobaciones puras compartidas, incluida `_comprobar_tipo_textual`. No importa otros módulos del paquete ni produce interacción.
- `_argumentos.py` concentra argparse, ayuda, Namespace, entradas textuales y traducción de errores CLI. Su representación interna `_ArgumentosEjecucion` conserva el modo, los textos y cómo informar un error; no aplica predeterminados ni interpreta contenido.
- `_preguntas.py` presenta preguntas y menús y reintenta sobre validadores; no conoce modelos ni resultados. `_resolucion.py` comprueba la colección de definiciones, selecciona el recorrido, aplica la precedencia y coordina el guardado.
- Separar fases con líneas vacías y comentar decisiones no evidentes: identidad, almacenamiento por variante, prefijo de Namespace, omisión frente a texto vacío y propagación de cancelaciones. Los docstrings explican responsabilidad y alcance sin narrar cada instrucción.
- `tests/test_organizar_modulos.py` protege la estructura plana y las fronteras de importación aprobadas; conservar también las pruebas de comportamiento e inferencia desde el wheel instalado.
- Usar ciclos de prueba fallida → implementación mínima → prueba correcta antes de ampliar comportamiento.
- Desechables solo en el scratch autorizado del perfil, nunca en rutas de sistema ni carpetas de negocio.
- Git: repositorio público `https://github.com/SebaxFentex/parametros_utils`, con la rama `main` y los tags anotados `v0.1.0`, `v1.0.0` y `v1.1.0` publicados por autorización del usuario. Registrar los cambios verificados con commits en español y subirlos a `main` dentro del encargo autorizado. No modificar tags publicados ni crear nuevos tags o releases sin autorización expresa.

## Historial de rupturas

- `0.1.0`: implementación inicial, sin consumidores migrados.
- `1.0.0` — 2026-11-09: rediseño sin compatibilidad; `v0.1.0` publicado mantiene la API vieja.
  - `Parametro` único con campo `tipo` y retorno en diccionario por nombre → base abstracta `Parametro[T]` con `ParametroPeriodo`, `ParametroSiNo` y `ParametroOpciones`; `obtener_parametros` devuelve `ParametrosResueltos` y cada valor se lee con `obtener_valor_parametro` por identidad de instancia.
  - `opciones` y `codigo_todos` opcionales según el tipo → `menu_opciones` obligatorio solo en `ParametroOpciones` y `codigo_todos` solo allí; el consumidor elige su código.
  - Acceso por cadenas con comprobaciones en el consumidor → acceso por definición, sin `assert`/`cast`/`Any`.
  - Argumento `parametros` de `obtener_parametros` → `definiciones_parametros`; constructores de variantes solo por palabra clave, sin conservar el constructor anterior.
  - Keywords `texto` de `validar_periodo` y `validar_si_no` → `texto_periodo` y `respuesta_si_no`; en `validar_opciones`, `texto`/`opciones` → `texto_seleccion`/`menu_opciones`; en `solicitar_opciones`, `opciones` → `menu_opciones`.
  - Sin aliases ni aceptación del contrato viejo; sin migraciones incluidas.
