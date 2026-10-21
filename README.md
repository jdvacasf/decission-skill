# Decisions for Coding

Skill para que Codex o Claude Code clasifique tareas de ingeniería mediante la Decisions API de OpenAI (`gpt-6-luna`) o la API local de decisiones de Ollama (`tev1:0.8b`). La respuesta no sustituye la revisión del código ni autoriza cambios fuera de la petición del usuario.

Este proyecto se distribuye bajo la licencia [MIT](LICENSE).

## Contenido

```text
.agents/skills/decisions-for-coding/
├── SKILL.md
├── requirements.txt
└── scripts/
    └── decisions_classifier.py
```

El clasificador y sus dependencias viajan dentro de la skill; no dependen del directorio de trabajo del proyecto que Codex esté editando.

El directorio `.claude/skills/decisions-for-coding/` contiene un espejo de instrucciones para Claude Code cuando se trabaja desde este repositorio; el paquete autónomo que se instala es el de `.agents/skills/`.

## Requisitos

- Python 3.9 o superior.
- Para OpenAI: una API key con acceso a la Decisions API/modelo `gpt-6-luna` y la librería oficial `openai` 3.26.0 o superior.
- Para Ollama: Ollama 0.35 o superior, en ejecución, y un modelo de decisiones descargado. Este ejemplo usa `tev1:0.8b`.
- El backend Ollama usa la librería estándar de Python; no necesita instalar `openai` ni crear un entorno virtual.

## Instalar la skill en Codex

En Linux o macOS, clona el repositorio y copia la skill al directorio personal de Codex:

```bash
git clone https://github.com/jdvacasf/decission-skill.git
mkdir -p "$HOME/.codex/skills/decisions-for-coding"
cp -R decission-skill/.agents/skills/decisions-for-coding/. "$HOME/.codex/skills/decisions-for-coding/"
```

Para instalarla solo en un proyecto, copia esa carpeta a `<proyecto>/.agents/skills/decisions-for-coding/`.

Reinicia Codex o abre una sesión nueva para que descubra la skill.

## Preparar el entorno

Solo necesitas este paso para usar el backend OpenAI. Desde el directorio instalado de la skill, crea un entorno virtual e instala sus dependencias:

Linux o macOS:

```bash
cd "$HOME/.codex/skills/decisions-for-coding"
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
cd "$HOME/.codex/skills/decisions-for-coding"
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

En Debian/Ubuntu, si `venv` falla porque no encuentra `ensurepip`, instala el paquete de venv que corresponda a tu Python. Por ejemplo, para Python 3.13:

```bash
sudo apt install python3.13-venv
```

Después vuelve a ejecutar `python3 -m venv .venv`.

## Configurar OpenAI

Configura `OPENAI_API_KEY` en el entorno del proceso que inicia Codex. No la guardes en el repositorio ni la incluyas en los textos de decisión.

En Bash, para la sesión actual:

```bash
read -rsp "OpenAI API key: " OPENAI_API_KEY
printf '\n'
export OPENAI_API_KEY
```

Cada invocación con este backend hace una llamada remota y puede generar coste. Solo se envía el texto incluido en `input` y las instrucciones/opciones de la pregunta.

## Usar Ollama local

Actualiza Ollama a la versión 0.35 o superior, inicia su servicio y descarga el modelo:

```bash
ollama pull tev1:0.8b
```

Indica `"backend":"ollama"` en la petición. El modelo predeterminado de este backend es `tev1:0.8b`; la dirección por defecto es `http://localhost:11434`. Puedes cambiarla con `OLLAMA_BASE_URL`.

```bash
printf '%s' '{
  "backend": "ollama",
  "input": "El endpoint devuelve un error 500 cuando falta email",
  "question": "¿Qué tipo de tarea es?",
  "type": "choice",
  "choices": ["feature", "bugfix", "refactor"]
}' | python3 scripts/decisions_classifier.py
```

Ejecuta la prueba desde el directorio instalado (`~/.codex/skills/decisions-for-coding`). Si devuelve un JSON con `"choice"`, Ollama y el clasificador están conectados; en una sesión nueva de Codex puedes invocar el skill con `$decisions-for-coding`.

Ollama recibe la solicitud en `/v1/systemone`; el texto se envía como `state` y la pregunta como una decisión con nombre. El tipo `predicate` se traduce al tipo Ollama `noul`. El texto se procesa en el servidor Ollama configurado, no en OpenAI.

## Prueba manual

Desde la carpeta instalada de la skill:

```bash
printf '%s' '{
  "backend": "openai",
  "input": "La exportación falla al generar el informe",
  "question": "¿Qué tipo de trabajo requiere esta tarea?",
  "type": "choice",
  "choices": [
    {"value": "feature", "description": "Añadir comportamiento"},
    {"value": "bugfix", "description": "Corregir un fallo"},
    {"value": "refactor", "description": "Cambiar internos sin cambiar comportamiento"}
  ]
}' | .venv/bin/python scripts/decisions_classifier.py
```

Salida de ejemplo:

```json
{"backend":"openai","model":"gpt-6-luna","answer":{"type":"choice","name":"decision","choice":"bugfix","confidence":0.97}}
```

El protocolo lee un objeto JSON desde `stdin` y escribe un objeto JSON en `stdout`. Acepta `choice`, `predicate` y `score`; `choice` requiere `choices` y `score` requiere `levels`. Los errores también se devuelven como JSON y el proceso termina con código distinto de cero.

## Usar la skill

Pídele a Codex que la invoque explícitamente:

```text
$decisions-for-coding
Clasifica esta tarea y usa el resultado para orientar el trabajo:
"El endpoint devuelve un error 500 cuando falta el campo email."
```

También puede seleccionarla automáticamente por la descripción de la skill. Las categorías habituales son `feature`, `bugfix`, `refactor`, `test`, `security` y `docs`.

Si falta la clave o falla la llamada, la skill debe continuar con criterio local e indicar que no obtuvo una clasificación de la API. La API devuelve una recomendación; Codex debe comprobar los requisitos y el código antes de decidir cómo actuar.
