# parametros_utils

Librería interna para declarar y resolver parámetros de ejecución de tareas.

## Instalación y requisitos

Versión local `0.1.0`, **sin repositorio remoto ni tag publicado**. Todavía no hay una URL de instalación verificada. Después de publicar y comprobar el tag, el consumidor usará esta plantilla sustituyendo ambos marcadores por valores reales:

```toml
[project]
dependencies = ["parametros_utils"]

[tool.uv.sources]
parametros_utils = { git = "<URL_DEL_REPOSITORIO>", tag = "<TAG_PUBLICADO>" }
```

- Ejecutar `uv lock` y `uv sync` después de declarar la dependencia.
- Requiere Python 3.14 o superior, sin dependencias de ejecución adicionales, configuración externa ni autenticación.
- No usar `path`/`editable`, copiar el paquete ni modificar `sys.path`.
- El consumidor calcula sus predeterminados y los entrega como texto. La librería no lee `.env`, no calcula periodos ni registra el origen de los valores.
- Llamar a `obtener_parametros` antes de cargar configuración obligatoria, configurar logs, crear salidas o adquirir recursos de negocio.
- No incluye sustitución de parámetros SQL ni un tipo genérico de texto.

## Ejemplo mínimo

Ejemplo de resolución para una tarea; no exporta archivos ni modifica consumidores existentes. El cálculo del mes anterior pertenece al consumidor.

```python
from datetime import date, timedelta

from parametros_utils import Parametro, obtener_parametros


def main(argumentos: list[str] | None = None) -> int:
    mes_anterior = date.today().replace(day=1) - timedelta(days=1)
    try:
        valores = obtener_parametros(
            [
                Parametro(
                    nombre="periodo",
                    tipo="periodo",
                    pregunta="Periodo de cierre (YYYYMM): ",
                    ayuda="Periodo YYYYMM; predeterminado: mes anterior.",
                    predeterminado=f"{mes_anterior.year:04d}{mes_anterior.month:02d}",
                ),
                Parametro(
                    nombre="confirmar",
                    tipo="si_no",
                    pregunta="¿Continuar? (si/no): ",
                    ayuda="Confirmación si/no; predeterminado: si.",
                    predeterminado="si",
                ),
                Parametro(
                    nombre="opciones",
                    tipo="opciones",
                    pregunta="Archivos separados por coma: ",
                    ayuda="2=Clientes, 3=Facturación, 0=Todos. Predeterminado: 0.",
                    predeterminado="0",
                    opciones={"2": "Clientes", "3": "Facturación"},
                    codigo_todos="0",
                ),
            ],
            descripcion="Demostración de parámetros de cierre",
            argumentos=argumentos,
        )
    except (EOFError, KeyboardInterrupt):
        print("\nEntrada interactiva cancelada.")
        return 1

    periodo = valores["periodo"]
    opciones = valores["opciones"]
    assert isinstance(periodo, date)
    assert isinstance(opciones, set)
    print(periodo.strftime("%Y%m"), valores["confirmar"], sorted(opciones))
    # Aquí comenzaría el procesamiento de la tarea con los valores resueltos.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Para una tarea que use este patrón, sustituir `tarea_<nombre>` por su módulo real:

```powershell
uv run python -m src.tarea_<nombre> --help
uv run python -m src.tarea_<nombre>
uv run python -m src.tarea_<nombre> --periodo 202401 --confirmar no --opciones "2,3"
uv run python -m src.tarea_<nombre> --interactivo
```

Las automatizaciones llaman directamente a `uv run` sin `--interactivo`. El `.bat` humano de una tarea sin `.env` conserva siempre la pausa y el código de salida:

```bat
@echo off
cd /d "%~dp0..\python_<nombre>"
uv run python -m src.tarea_<nombre> --interactivo
set EXIT_CODE=%ERRORLEVEL%
pause
exit /b %EXIT_CODE%
```

Si el consumidor usa su propio `.env`, añade `--env-file .env` a `uv run`.

## API pública

Importar desde `parametros_utils`.

### Declaración

```python
Parametro(
    nombre: str,
    tipo: Literal["periodo", "si_no", "opciones"],
    pregunta: str,
    ayuda: str = "",
    predeterminado: str | None = None,
    opciones: dict[str, str] | None = None,
    codigo_todos: str | None = None,
)
```

- `nombre` es un identificador Python y se convierte exactamente en `--nombre`. Admite `año_cierre`; no admite guiones, espacios exteriores ni los nombres reservados `interactivo`, `help` y `h`.
- `pregunta` debe contener texto y conserva sus espacios finales. Si `ayuda` está vacía, la ayuda utiliza la pregunta.
- `predeterminado=None` significa que, en automático, se exige el argumento explícito. Una cadena vacía está presente, pero es inválida.
- El contenido del predeterminado se interpreta solo cuando se utiliza; no al declarar, pedir ayuda ni recibir un argumento explícito que lo sustituya.
- `opciones` es obligatorio para el tipo `opciones`. El menú y `codigo_todos` no se permiten en los otros tipos.
- El menú exige códigos y etiquetas textuales no vacíos. Los códigos no admiten comas ni espacios exteriores; `codigo_todos` no puede coincidir con una opción real.
- Los campos no se pueden reasignar. El consumidor conserva la propiedad del menú y no debe modificarlo durante las preguntas.

Lanza `TypeError` por tipos incorrectos y `ValueError` por declaraciones inconsistentes. No pregunta ni interpreta el predeterminado.

### Resolución completa

```python
obtener_parametros(
    parametros: Sequence[Parametro],
    *,
    descripcion: str,
    argumentos: Sequence[str] | None = None,
) -> dict[str, date | bool | set[str]]
```

- `argumentos=None` lee la invocación real; `argumentos=[]` indica una invocación sin argumentos. Se admiten listas y tuplas.
- Añade `--help`/`-h`, `--interactivo` y una opción por declaración. Rechaza abreviaturas, argumentos desconocidos y nombres duplicados.
- En automático, resuelve cada entrada por separado: argumento explícito → predeterminado textual → error si faltan ambos. Nunca reemplaza un explícito inválido por el predeterminado.
- Con `--interactivo`, pregunta todas las entradas en el orden declarado, sin predeterminados y sin permitir valores explícitos mezclados.
- Devuelve exclusivamente los nombres declarados y sus valores finales. No devuelve `Namespace`, modo, procedencia ni resultados parciales.

Lanza `TypeError` por tipos incorrectos de declaraciones/argumentos, `ValueError` por configuración inválida, `SystemExit(0)` por ayuda y `SystemExit(2)` por errores de entrada automática. Propaga `EOFError` y `KeyboardInterrupt` desde las preguntas.

### Validación sin preguntas

```python
validar_periodo(texto: str) -> date
validar_si_no(texto: str) -> bool
validar_opciones(
    texto: str,
    opciones: dict[str, str],
    *,
    codigo_todos: str | None = None,
) -> set[str]
```

- Periodo: recorta espacios exteriores, exige seis dígitos ASCII de `0` a `9` en formato `YYYYMM` y retorna `date(año, mes, 1)`. Se aplican los límites del propio `date`, sin un rango de negocio adicional. `0000` como año y meses fuera de `01`–`12` son inválidos.
- Si/no: recorta espacios exteriores y compara sin distinguir mayúsculas. `" SÍ "` devuelve `True` y `"no"` devuelve `False`. Rechaza `"s"`, `"1"` y `"true"`.
- Opciones: separa por comas, recorta cada código, ignora fragmentos vacíos y elimina duplicados. `"3,2,,3,"` devuelve `{"2", "3"}` sin garantía de orden. Rechaza una selección vacía, solo comas o cualquier código desconocido.
- Todos es opcional y su código lo elige el consumidor. Se expande al conjunto de claves únicamente cuando aparece solo. Si `0` significa todos, `"0,2"` y `"0,99"` se rechazan; `"0,0"` se deduplica y equivale a `"0"`.
- Sin `codigo_todos`, `0` solo es válido si es una clave real del menú. Los códigos distinguen mayúsculas.

Los validadores no preguntan ni imprimen. Lanzan `TypeError` por tipos incorrectos y `ValueError` por contenido o menús inválidos.

### Preguntas

```python
solicitar_periodo(pregunta: str) -> date
solicitar_si_no(pregunta: str) -> bool
solicitar_opciones(
    pregunta: str,
    opciones: dict[str, str],
    *,
    codigo_todos: str | None = None,
) -> set[str]
```

Utilizan los mismos validadores, muestran el motivo de una respuesta inválida y repiten la pregunta. Las opciones muestran el menú recibido y `Todos` si se configuró su código. Una respuesta vacía nunca activa un predeterminado.

Las preguntas y los menús se comprueban antes de leer: la configuración inválida lanza `TypeError` o `ValueError` sin iniciar un bucle. El cierre de entrada (`EOFError`) y la interrupción (`KeyboardInterrupt`) se propagan al consumidor.

## Códigos de salida

- `0`: ayuda solicitada o ejecución correcta del consumidor.
- `1`: fallo genérico del consumidor; el ejemplo lo utiliza para cancelar. La librería no asigna este código a las cancelaciones.
- `2`: error de argumentos gestionado por `obtener_parametros` mediante `argparse`.

No hay excepciones propias ni atributo `codigo_salida`: los validadores usan excepciones nativas y la resolución CLI conserva el contrato de `argparse`.

## Desarrollo

Paquete `uv_build` con layout `src/`, entorno y lock propios. Ruff y ty son herramientas de desarrollo fijadas en `pyproject.toml`, no dependencias del consumidor. Los tests usan `unittest` de stdlib y no necesitan `.env`, red, archivos de prueba ni un operador.

```powershell
uv sync --locked
uv run python -m unittest discover -s tests -v
uv run ruff check src tests
uv run ruff format --check src tests
uv run ty check
uv run python -m compileall -q src tests
uv build
```

- `tests/test_declarar_parametro.py`: declaración y configuración.
- `tests/test_validar_periodo.py`: periodos y límites de `date`.
- `tests/test_validar_si_no.py`: respuestas admitidas y rechazadas.
- `tests/test_validar_opciones.py`: selección, menús y todos.
- `tests/test_solicitar_parametros.py`: preguntas, reintentos y cancelación.
- `tests/test_obtener_parametros.py`: precedencia, ayuda y separación de modos.
- `tests/test_ejecutar_consumidor.py`: CLI real en procesos separados, desde otra carpeta y con entrada cerrada.

Cada archivo se ejecuta también con `uv run python tests/<test>.py` y tiene un `.bat` del mismo nombre en `Ejecutables/tests/`. `Ejecutables/build.bat` construye y lista artefactos; no publica en GitHub. `Ejecutables/abrir_vscode.bat` abre la raíz del paquete.

La guía para agentes está en `AGENTS.md`. La modificación de normativa compartida y la migración de consumidores quedan pendientes; no forman parte de esta implementación local.
