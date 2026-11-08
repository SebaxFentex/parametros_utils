# parametros_utils

## Qué hace y qué no

Centraliza la definición y resolución de los parámetros de ejecución de una tarea. El consumidor declara sus entradas y conserva sus cálculos y reglas de negocio.

Cubre tres variantes: periodo `YYYYMM` que vuelve `date`, respuesta si/no que vuelve `bool` y selección de códigos que vuelve `set[str]`. Trae modo automático y modo `--interactivo`, validadores puros para usar sin preguntas y preguntas con reintento.

No lee `.env`, calcula predeterminados, configura logs, crea archivos ni sustituye parámetros SQL. Tampoco incluye entradas de texto libre ni tipos adicionales. El mes anterior y cualquier otro valor por omisión los calcula tu tarea y los entrega como texto.

## Estado de versión y cómo declararla

La última versión etiquetada es `v0.1.0`, con la API anterior: un solo `Parametro` con campo `tipo` y retorno en diccionario. `pyproject.toml` se mantiene en `0.1.0` hasta que se autorice una nueva versión.

El rediseño que describe este archivo (subclases por variante y `ParametrosResueltos`) vive en `main` y aún no tiene tag. Instalar `v0.1.0` no te da la API nueva. Cuando el rediseño se publique, usa el tag real donde abajo lees `vX.Y.Z`. No consumas por rama.

```toml
[project]
dependencies = ["parametros_utils"]

[tool.uv.sources]
parametros_utils = { git = "https://github.com/SebaxFentex/parametros_utils", tag = "vX.Y.Z" }
```

Tras declarar la dependencia corre `uv lock` y `uv sync`. La librería pide Python 3.14 o superior y no trae dependencias de ejecución. No la uses con `path` ni `editable`, no copies el paquete y no toques `sys.path`.

## Qué necesita tu proyecto

Calcula tus predeterminados y pásalos como texto. La librería no lee `.env` ni calcula periodos de negocio. Llama a `obtener_parametros` antes de cargar configuración obligatoria, configurar logs, crear salidas o abrir recursos de negocio.

Las automatizaciones llaman a `uv run` directamente, sin `--interactivo`. Para una tarea `src/tarea_<nombre>.py` los comandos se ven así, con tu módulo en lugar de `tarea_<nombre>`:

```powershell
uv run python -m src.tarea_<nombre> --help
uv run python -m src.tarea_<nombre>
uv run python -m src.tarea_<nombre> --periodo 202401 --confirmar no --archivos "2,3"
uv run python -m src.tarea_<nombre> --interactivo
```

El `.bat` humano de una tarea sin `.env` conserva la pausa y el código de salida:

```bat
@echo off
cd /d "%~dp0..\python_<nombre>"
uv run python -m src.tarea_<nombre> --interactivo
set EXIT_CODE=%ERRORLEVEL%
pause
exit /b %EXIT_CODE%
```

Si tu proyecto usa su propio `.env`, suma `--env-file .env` al `uv run`.

## Ejemplo mínimo

La tarea calcula el mes anterior, guarda cada definición y lee cada valor con su definición. Sin claves de texto y sin comprobaciones de tipo en tu código: no usa `assert`, `cast` ni `Any`.

```python
from datetime import date, timedelta

from parametros_utils import (
    ParametroOpciones,
    ParametroPeriodo,
    ParametroSiNo,
    obtener_parametros,
)


def main(argumentos: list[str] | None = None) -> int:
    mes_anterior = date.today().replace(day=1) - timedelta(days=1)
    definicion_periodo = ParametroPeriodo(
        nombre="periodo",
        pregunta="Periodo de cierre (YYYYMM): ",
        ayuda="Periodo YYYYMM; predeterminado: mes anterior.",
        predeterminado=f"{mes_anterior.year:04d}{mes_anterior.month:02d}",
    )
    definicion_confirmacion = ParametroSiNo(
        nombre="confirmar",
        pregunta="¿Continuar? (si/no): ",
        ayuda="Confirmación si/no; predeterminado: si.",
        predeterminado="si",
    )
    definicion_archivos = ParametroOpciones(
        nombre="archivos",
        pregunta="Archivos separados por coma: ",
        ayuda="2=Clientes, 3=Facturación, 0=Todos. Predeterminado: 0.",
        predeterminado="0",
        menu_opciones={"2": "Clientes", "3": "Facturación"},
        codigo_todos="0",
    )
    definiciones_parametros = [
        definicion_periodo, definicion_confirmacion, definicion_archivos
    ]
    try:
        parametros = obtener_parametros(
            definiciones_parametros,
            descripcion="Demostración de parámetros de cierre",
            argumentos=argumentos,
        )
    except (EOFError, KeyboardInterrupt):
        print("\nEntrada interactiva cancelada.")
        return 1

    periodo = parametros.obtener_valor_parametro(definicion_periodo)
    confirmar = parametros.obtener_valor_parametro(definicion_confirmacion)
    archivos = parametros.obtener_valor_parametro(definicion_archivos)
    print(periodo.strftime("%Y%m"), confirmar, sorted(archivos))
    # Aquí empieza el proceso de la tarea con los valores ya resueltos.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Con `--archivos "2,3"` tomas esos códigos y con `--archivos 0` tomas todo el menú. Con `--interactivo` la librería pregunta las tres entradas en orden, sin usar predeterminados.

## API pública

Todo se importa desde `parametros_utils`.

### Glosario

- definición: una instancia de `ParametroPeriodo`, `ParametroSiNo` o `ParametroOpciones`. La creas una vez y la guardas para leer su valor.
- entrada textual: representación recibida como argumento, predeterminado o respuesta, todavía sin interpretar como fecha, booleano o conjunto de códigos.
- valor resuelto: el dato ya interpretado, `date`, `bool` o `set[str]`.
- menú: el diccionario de tu tarea que asocia cada código con su etiqueta. Sigue siendo tuyo.
- código de opción: una clave del menú, por ejemplo `"2"`.
- etiqueta de opción: el texto visible de un código, por ejemplo `"Clientes"`.
- códigos seleccionados: el conjunto que vuelve la variante de opciones.
- códigos desconocidos: códigos fuera del menú que tampoco son el código de todos. Siempre dan error.

### Declaración

```python
ParametroPeriodo(*, nombre: str, pregunta: str, ayuda: str = "", predeterminado: str | None = None)
ParametroSiNo(*, nombre: str, pregunta: str, ayuda: str = "", predeterminado: str | None = None)
ParametroOpciones(*, nombre: str, pregunta: str, ayuda: str = "", predeterminado: str | None = None, menu_opciones: dict[str, str], codigo_todos: str | None = None)
```

`Parametro` es la base abstracta y no se instancia. Las tres variantes son `frozen`, con `slots`, solo palabra clave e `eq=False`: dos definiciones con los mismos campos no son iguales, cada una se distingue por identidad. Ninguna guarda el valor de una ejecución.

- `nombre` es un identificador Python y se vuelve `--nombre`. Vale `año_cierre`. No valen guiones ni espacios en los bordes. Los nombres `interactivo`, `help` y `h` están reservados.
- `pregunta` pide texto y guarda sus espacios finales. Si `ayuda` queda vacía, la ayuda muestra la pregunta.
- `predeterminado=None` exige el argumento explícito en automático. Una cadena vacía cuenta como presente pero inválida. El texto se interpreta solo cuando se usa: ni al declarar, ni al pedir ayuda, ni cuando un argumento explícito lo reemplaza.
- `menu_opciones` es obligatorio en opciones y no existe en las otras variantes. Exige códigos y etiquetas textuales no vacíos. Solo los códigos prohíben comas y espacios exteriores; las etiquetas conservan el texto recibido. `codigo_todos` no puede repetirse como clave del menú y su valor lo elige el consumidor: no se impone el `0`.
- Los campos no se reasignan. No toques el menú mientras la librería pregunta.

La definición lanza `TypeError` por tipos incorrectos y `ValueError` por contenido de configuración inválido. Construirla no pregunta ni interpreta el predeterminado.

### Resolución completa

```python
obtener_parametros(definiciones_parametros: Sequence[ParametroPeriodo | ParametroSiNo | ParametroOpciones], *, descripcion: str, argumentos: Sequence[str] | None = None) -> ParametrosResueltos
```

- `argumentos=None` lee la invocación real. `argumentos=[]` dice que no llegó ningún argumento. Valen listas y tuplas.
- Añade `--help` y `-h`, `--interactivo` y una opción por definición. No acepta abreviaturas, argumentos desconocidos ni nombres repetidos.
- En automático resuelve cada entrada por su cuenta: argumento explícito, si no el predeterminado, si no error. Nada pregunta. Un explícito inválido nunca cae al predeterminado.
- Con `--interactivo` pregunta todas las entradas en el orden declarado, sin predeterminados y sin mezclar valores explícitos.
- Devuelve solo lo declarado, completo. No hay `Namespace`, ni modo, ni origen, ni resultados a medias si cancelas.

Lanza `TypeError` por tipos mal pasados, `ValueError` por configuración mala, `SystemExit(0)` por ayuda y `SystemExit(2)` por errores de entrada en automático. `EOFError` y `KeyboardInterrupt` pasan tal cual a tu tarea. La ayuda sale antes de interpretar predeterminados o preguntar.

### Acceso tipado al resultado

```python
parametros.obtener_valor_parametro(definicion_parametro: Parametro[T]) -> T
```

Pasas la misma instancia que declaraste y recibes su tipo: `date`, `bool` o `set[str]`. Pasar el nombre en texto da `TypeError`. Pasar otra instancia, aunque tenga los mismos campos, da `ValueError`. No hay acceso por cadenas ni llaves de diccionario.

### Validación sin preguntas

```python
validar_periodo(texto_periodo: str) -> date
validar_si_no(respuesta_si_no: str) -> bool
validar_opciones(texto_seleccion: str, menu_opciones: dict[str, str], *, codigo_todos: str | None = None) -> set[str]
```

- Periodo: quita espacios de los bordes, pide seis dígitos ASCII (`0` a `9`) en forma `YYYYMM` y vuelve `date(año, mes, 1)`. Los límites de año los pone `date`, sin rango de negocio extra. Año `0000` y mes fuera de `01` a `12` no pasan.
- Si/no: quita espacios y compara sin mirar mayúsculas. `" SÍ "` da `True` y `"no"` da `False`. `"s"`, `"1"` y `"true"` no pasan.
- Opciones: parte por comas, recorta cada código, tira vacíos y duplicados y vuelve un conjunto sin orden prometido. `"3,2,,3,"` da `{"2", "3"}`. Vacío, solo comas o cualquier código desconocido dan error.
- El código de todos solo vale solo: con `codigo_todos="0"`, `"0"` se expande a todas las claves, `"0,0"` colapsa a lo mismo y `"0,2"` no pasa. Sin `codigo_todos`, `0` solo vale si es clave real. Los códigos distinguen mayúsculas.

No preguntan ni imprimen. `TypeError` por tipos mal pasados, `ValueError` por contenido o menú malo.

### Preguntas

```python
solicitar_periodo(pregunta: str) -> date
solicitar_si_no(pregunta: str) -> bool
solicitar_opciones(pregunta: str, menu_opciones: dict[str, str], *, codigo_todos: str | None = None) -> set[str]
```

Usan los mismos validadores, te dicen por qué falló tu respuesta y repiten la pregunta. Las opciones muestran el menú y la fila de todos si lo configuraste. Una respuesta vacía nunca dispara un predeterminado.

La configuración se revisa antes de leer: si está mal, fallan sin entrar en bucle. `EOFError` y `KeyboardInterrupt` pasan a tu tarea.

### Dónde vive cada cosa

- `_parametro.py`: configuración y polimorfismo de las variantes.
- `_resultados.py`: guardado tipado por definición.
- `_resolucion.py`: `argparse` y los dos modos.
- `_validacion.py`: funciones puras, sin preguntas ni pantalla.
- `_preguntas.py`: reintentos sobre los validadores.

`__init__.py` solo expone la API y el `NullHandler`.

## Códigos de salida

| Código | Significado |
|---|---|
| 0 | Ayuda pedida o tarea terminada bien. |
| 1 | Fallo genérico de tu tarea. El ejemplo lo usa al cancelar. La librería no asigna este código. |
| 2 | Error de argumentos que `obtener_parametros` resuelve por `argparse`. |

Sin excepciones propias ni atributo `codigo_salida`. Los validadores usan excepciones nativas y la resolución respeta el contrato de `argparse`.

## Desarrollo

Paquete `uv_build` con layout `src/`, entorno y lock propios. Ruff y ty son herramientas fijadas en `pyproject.toml`, no dependencias de quien usa la librería. Los tests usan `unittest` de la stdlib y no piden `.env`, red ni archivos.

El marcador vacío `src/parametros_utils/py.typed` distribuye las anotaciones del paquete. La verificación de empaquetado comprueba que esté presente en el wheel y el sdist; el tipado también se comprueba desde una instalación aislada del wheel.

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

Cada archivo corre también con `uv run python tests/<test>.py` y tiene un `.bat` del mismo nombre en `Ejecutables/tests/`. `Ejecutables/build.bat` construye y lista artefactos sin publicar en GitHub. `Ejecutables/abrir_vscode.bat` abre la raíz del paquete.

El detalle para agentes vive en `AGENTS.md`.
