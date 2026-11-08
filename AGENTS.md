# AGENTS.md — parametros_utils

## Alcance y contrato

- Paquete interno Python >=3.14, layout `src/`, backend `uv_build`, sin dependencias de ejecución.
- API aprobada: `Parametro`, `obtener_parametros`, `validar_periodo`, `validar_si_no`, `validar_opciones`, `solicitar_periodo`, `solicitar_si_no`, `solicitar_opciones`.
- Declaraciones: nombre, tipo (`periodo`, `si_no`, `opciones`), pregunta, ayuda, predeterminado textual opcional, menú y código de todos opcionales según el tipo.
- Retorno final: diccionario nombre → date/bool/set[str]. No devolver origen, modo ni otros metadatos.
- El periodo se interpreta como YYYYMM, recorta espacios exteriores y retorna date(año, mes, 1); los límites de año son los de date.
- Si/no acepta si/sí/no sin distinguir mayúsculas, recortando espacios exteriores.
- Opciones separadas por coma: recortar cada código, eliminar vacíos y duplicados, sin garantía de orden; selección vacía, desconocidos o todos mezclado con otro código son errores.
- Todos es opcional y el consumidor elige su código; no imponer 0.
- Automático: argumento explícito > predeterminado textual > error. Un inválido explícito nunca activa el predeterminado.
- Interactivo: pedir todos los parámetros, sin predeterminados ni mezcla con argumentos explícitos. Reintentar únicamente contenido inválido.
- EOFError y KeyboardInterrupt se propagan incluso desde obtener_parametros.
- TypeError por tipo incorrecto y ValueError por contenido inválido; errores CLI se traducen con analizador.error. Ayuda antes de validar predeterminados o preguntar.

## Desarrollo

- Leer README y normativa Tigo vigente antes de modificar. No migrar consumidores ni operar producción.
- Los menús, las preguntas y los errores interactivos son la salida solicitada por el consumidor; no convertirlos en logging. La aclaración de las secciones 4 y 6 de la norma queda pendiente al final, por decisión del usuario.
- La librería no lee `.env` ni variables de entorno, no configura logging, no crea archivos y no calcula predeterminados. NullHandler en __init__.
- No añadir __main__.py: no se solicitó un comando independiente de la librería.
- Tests ejecutables en tests/test_*.py con main(), usando unittest de stdlib, sin .env. Un .bat por test en Ejecutables/tests.
- Verificación: uv sync --locked; uv run python -m unittest discover -s tests -v; tests por archivo; compileall; uv build; import desde wheel aislado.
- Usar ciclos de prueba fallida → implementación mínima → prueba correcta antes de ampliar comportamiento.
- Desechables solo en el scratch autorizado del perfil, nunca en rutas de sistema ni carpetas de negocio.
- Git local y commits en español autorizados. No crear remoto, hacer push, tag ni release en este encargo.

## Historial de rupturas

Sin rupturas: implementación inicial, sin consumidores migrados.
