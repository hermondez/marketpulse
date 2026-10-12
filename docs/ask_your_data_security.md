# Pregunta a tus datos: seguridad (Módulo 4)

## Qué
Página de chat en Streamlit: escribes en español, un LLM genera SQL sobre `MARTS`, se valida, se
**muestra** y solo se ejecuta si pulsas "Ejecutar".

## Opciones de LLM (`LLM_PROVIDER`)
| Opción | Pros | Contras |
|---|---|---|
| `cortex` (Snowflake Cortex `COMPLETE`) | Los datos no salen de Snowflake; sin API key extra | Disponibilidad por región/edición; consume créditos |
| `openai` (cualquier API compatible: OpenAI, Groq, Azure, Ollama local) | Modelos fuertes, fácil | El esquema viaja a un tercero; requiere `LLM_API_KEY` |
| `anthropic` | Modelos fuertes | Igual que arriba |

Solo se envía el **esquema** (de `manifest.json`/`catalog.json`), nunca filas, al generar SQL.

## Defensa en profundidad
1. **Validador sqlglot** (`ask/sql_guard.py`):
   - exactamente **una** sentencia (bloquea `SELECT 1; DROP ...`);
   - raíz `SELECT`/`UNION`/`INTERSECT`/`EXCEPT`;
   - recorre todo el árbol y rechaza nodos DML/DDL (`Insert`, `Update`, `Delete`, `Merge`, `Drop`,
     `Create`, `Alter`, `Command`, `Grant`, `Into`...) — incluso dentro de CTEs o subconsultas;
   - **allowlist** de tablas y esquema `MARTS`; prohíbe otra base de datos, `INFORMATION_SCHEMA`,
     funciones `SYSTEM$` y funciones de tabla;
   - **LIMIT forzado** (añade o reduce a 200);
   - regenera el SQL **sin comentarios** (nada oculto llega a Snowflake);
   - si no parsea → se rechaza (fail closed).
2. **Rol `MARKETPULSE_READER`** (`infra/snowflake/02_readonly_role.sql`): solo `SELECT` en `MARTS`.
3. **Timeout**: `STATEMENT_TIMEOUT_IN_SECONDS=30` en usuario y sesión.
4. **Humano en el bucle**: el SQL se muestra antes de ejecutar.
5. **Contraseña `APP_ASK_PASSWORD`** (sin ella la página se desactiva) y **límite de preguntas por
   sesión** (`APP_ASK_MAX_QUESTIONS`), en `ask/access.py`.

Tests: `tests/test_sql_guard.py` (DROP, UPDATE, DELETE, INSERT, MERGE, TRUNCATE, GRANT, CALL, USE,
multi-sentencia, trucos con comentarios, tablas/esquemas fuera de allowlist, CTE con DML, `SELECT INTO`,
`SYSTEM$`, LIMIT forzado/reducido).

## Por qué no basta con el prompt
Un prompt ("solo genera SELECT") se puede saltar con *prompt injection*. Las garantías reales son el
validador y, sobre todo, los permisos de Snowflake.

## Límites honestos
- El LLM puede generar SQL **válido pero incorrecto** (respuesta equivocada). Revisa el SQL.
- Un SELECT costoso (cross join) puede consumir créditos hasta el timeout.
- La allowlist debe mantenerse al añadir marts.

## Alternativas
Snowflake Cortex Analyst (modelo semántico YAML), capas semánticas (dbt Semantic Layer), consultas
predefinidas parametrizadas (más seguro, menos flexible).

## Cuándo reutilizar
Cualquier "texto a SQL" interno: siempre validador + rol de solo lectura + timeout.

## Notas de la prueba real (oct-2026)
- **Cortex en cuentas trial**: `SNOWFLAKE.CORTEX.COMPLETE` devuelve *"AI function COMPLETE is not
  available for trial accounts"*. En trial usa `LLM_PROVIDER=openai` o `anthropic`.
- **Roles secundarios**: las cuentas nuevas tienen `DEFAULT_SECONDARY_ROLES=('ALL')`. La conexión de
  solo lectura ejecuta `USE SECONDARY ROLES NONE`; sin eso heredaría privilegios de otros roles.
- **Dev**: el rol lector solo ve `MARTS` (prod). El permiso temporal sobre `DEV_MARTS` usado en la
  prueba se revocó.
