# Desplegar el dashboard en Streamlit Community Cloud

## Qué
Publicar las 4 páginas (Mercado, Portafolio simulado, Salud del pipeline, Pregunta a tus datos) como
app web gratuita, leyendo Snowflake con el rol de **solo lectura**.

## Por qué así
- **Punto de entrada `streamlit_app.py`** en la raíz: usa `st.navigation` para cargar las páginas que
  viven dentro del paquete (`src/marketpulse/dashboard/`).
- **`requirements.txt` = `-e .[dashboard]`**: instala el paquete (layout `src/`) con solo lo necesario
  para el dashboard. dbt, yfinance y el calendario quedan fuera (`requirements-pipeline.txt`, usado por
  CI, GitHub Actions y Docker).
- **Secrets**: `config.env()` busca primero variables de entorno y después `st.secrets`. La CLI y CI
  siguen igual (no importan Streamlit).
- **Solo `MARKETPULSE_READER`**: el dashboard nunca usa las credenciales del loader ni del transformer.
  Ese rol ve `MARTS` y, para la página de salud, solo `OPS.DBT_RUNS` y `OPS.DBT_NODE_RESULTS`.
- **Esquema `MARTS`**: es lo que construye el workflow diario (`daily.yml` usa `DBT_TARGET: prod`).
  `DEV_MARTS` es tu entorno de pruebas y el rol lector no tiene acceso.

## Paso a paso
1. **Usuario dedicado en Snowflake** (no uses tu usuario admin en la nube). En una hoja SQL, como
   SECURITYADMIN/ACCOUNTADMIN, ejecuta el bloque `CREATE USER MARKETPULSE_ASK ...` de
   `infra/snowflake/02_readonly_role.sql` con una contraseña larga y aleatoria.
2. Asegúrate de que `MARTS` tenga datos (corrida de `daily.yml` o `dbt build --target prod`).
3. Entra a **https://share.streamlit.io** y pulsa **Continue with GitHub**. Autoriza el acceso al repo
   `marketpulse` (si es privado, Streamlit pide permiso adicional).
4. **Create app** → **Deploy a public app from GitHub** (o "Yup, I have an app").
5. Rellena:
   - Repository: `hermondez/marketpulse`
   - Branch: `main`
   - Main file path: `streamlit_app.py`
   - App URL: el subdominio que quieras.
6. **Advanced settings**:
   - Python version: **3.11** (el paquete exige `>=3.11,<3.12`; otra versión falla al instalar).
   - Secrets: pega el contenido de `.streamlit/secrets.toml.example` con tus valores reales.
7. **Deploy**. La primera instalación tarda unos minutos. Revisa los logs ("Manage app") si falla.
8. Prueba cada página. "Pregunta a tus datos" pide la contraseña `APP_ASK_PASSWORD`; sin ese secret
   aparece desactivada.
9. Para cambiar secrets después: app → **Settings → Secrets** (la app se reinicia).

## Seguridad y costos
- **Contraseña + límite por sesión** en "Pregunta a tus datos" (`APP_ASK_MAX_QUESTIONS`, 10 por
  defecto). El límite es por sesión del navegador: recargar la página lo reinicia. Es un freno, no una
  barrera fuerte; el control de gasto real es el resource monitor de Snowflake y el límite de gasto en
  tu proveedor LLM.
- **Caché de 10 min** en las consultas del dashboard: menos arranques del warehouse.
- **App pública = datos públicos**: cualquiera con la URL ve Mercado/Portafolio/Salud. Recuerda los
  términos de uso de Yahoo (no redistribuir). Puedes hacer la app privada en Settings → Sharing.
- **Network policies de Snowflake**: Streamlit Cloud no tiene IPs de salida fijas (cambian). Si
  restringes Snowflake por IP, la app dejará de conectar. Opciones: no aplicar network policy a
  `MARKETPULSE_ASK` (y compensar con rol mínimo + contraseña fuerte o key-pair), o hospedar el
  dashboard donde tengas IP fija.
- **Contraseñas en Snowflake**: Snowflake está retirando el login solo con contraseña. Para
  usuarios de servicio, migra a key-pair cuando puedas.

## Alternativas
Snowflake Streamlit (Streamlit in Snowflake: sin credenciales externas, se paga en créditos),
Hugging Face Spaces, Docker en Cloud Run/Fly.io.

## Cuándo reutilizar
Cualquier dashboard Streamlit con layout `src/` y secretos: mismo patrón entrypoint + `-e .` + `st.secrets`.
