# Fuentes de datos y limitaciones

## Qué
| Fuente | Uso | Datos |
|---|---|---|
| **yfinance** (principal) | Librería Python no oficial que lee Yahoo Finance | OHLCV, Adj Close, dividendos |
| **Stooq** (alternativa) | CSV público `stooq.com/q/d/l/` | OHLCV (ajustado), sin dividendos |

Se cambia con `PRICE_SOURCE=stooq`, sin tocar código (ver `extractors/factory.py`).

## Limitaciones (léelas)
- **Retraso**: datos de fin de día; pueden tardar en aparecer o corregirse días después (por eso el
  lookback de 7 días y el MERGE).
- **Rotura de la fuente**: yfinance no es una API oficial; Yahoo cambia su web y la librería se rompe
  o aplica rate-limit con frecuencia. Mitigación: reintentos, extractor alternativo, chequeo de
  frescura/volumen con alerta.
- **Términos de uso**: Yahoo y Stooq permiten uso personal; **no** redistribuyas los datos ni los uses
  comercialmente. Revisa sus términos antes de publicar un dashboard abierto. Este proyecto es
  educativo y personal.
- **Calidad**: precios ajustados se recalculan cuando hay dividendos/splits; Stooq y Yahoo pueden
  diferir ligeramente. No mezcles fuentes en la misma serie sin saberlo (columna `source`).
- **Sin garantía**: no uses estos datos para operar.

## Alternativas
APIs con plan gratuito y clave (Alpha Vantage, Tiingo, Polygon, Financial Modeling Prep), datos de
Nasdaq Data Link, Snowflake Marketplace (datasets financieros listos para consultar). Para producción
real: proveedor con licencia.

## Cuándo reutilizar
El patrón "fuente principal + alternativa detrás de una interfaz" aplica a cualquier API inestable.

## Versiones de yfinance (lección aprendida)
`yfinance==0.2.44` dejó de funcionar (Yahoo respondía vacío: "possibly delisted"). Se fijó
`yfinance==0.2.66` + `curl_cffi==0.13.0`: `curl_cffi>=0.14` exige `cffi>=2`, incompatible con
`snowflake-connector-python` 3.x (`cffi<2`). La ingesta ahora trata "0 filas" como error.
