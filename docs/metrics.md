# Métricas: qué miden, cómo se calculan y qué NO te dicen

> Ninguna métrica predice el futuro. Son descripciones del pasado.

Todas se calculan sobre **precio ajustado** (`adj_close`, incluye dividendos y splits), salvo las
distancias a 52 semanas (precio de cierre vs máximos/mínimos intradía, ambos sin ajustar).

| Métrica | Qué mide | Cálculo | Qué NO te dice |
|---|---|---|---|
| Retorno diario | Cambio % de un día | `P_t / P_{t-1} - 1` | Si el movimiento continuará; un día es ruido. |
| Retorno acumulado | Ganancia desde el primer día disponible | `P_t / P_0 - 1` | Depende del día de inicio elegido; no es el retorno de un inversor real (aportes, impuestos). |
| SMA 50 / 200 | Tendencia suavizada | Promedio de las últimas 50/200 sesiones (NULL si faltan datos) | Va *detrás* del precio (retraso). Un cruce no es una señal confiable por sí sola. |
| RSI 14 | Fuerza de subidas vs bajadas recientes (0-100) | `100 - 100/(1+RS)`, `RS = media ganancias / media pérdidas` en 14 sesiones | ">70 sobrecompra" no significa que vaya a caer; en tendencias fuertes se queda alto semanas. Usamos medias **simples** (Cutler), no el suavizado de Wilder → valores distintos a TradingView. |
| Volatilidad 20d / 252d | Cuánto varían los retornos | `stddev(retornos) × √252` | No distingue subidas de bajadas; no mide el riesgo de eventos raros (colas). |
| Drawdown | Caída desde el máximo previo | `P_t / max(P_0..P_t) - 1` | Cuánto tardará en recuperarse. |
| Max drawdown | Peor caída histórica hasta la fecha | `min(drawdown)` | Que no pueda haber una caída peor en el futuro. Con poca historia subestima el riesgo. |
| Distancia a máx/mín 52s | Posición del precio en su rango anual | `close / high_52w - 1`, `close / low_52w - 1` (252 sesiones) | Si está "barato" o "caro"; un mínimo puede romperse. |
| Valor del portafolio simulado | Valor hipotético de posiciones fijas | `acciones × cierre`; P&L = `acciones × (cierre - costo)`; dividendos en efectivo | Ignora comisiones, impuestos, tipo de cambio, reinversión y aportes. |

## Por qué √252
Hay ~252 sesiones bursátiles al año. Si los retornos diarios fueran independientes, la varianza anual
es 252 × varianza diaria → desviación anual = diaria × √252. Es una aproximación convencional.

## Alternativas
EMA en vez de SMA (reacciona más rápido); RSI de Wilder (recursivo, mejor en Python o con
`MATCH_RECOGNIZE`/UDF); volatilidad EWMA; Sharpe/Sortino (requieren tasa libre de riesgo).

## Cuándo reutilizar
Medias móviles, volatilidad y drawdown aplican a cualquier serie temporal (ventas, latencias, KPIs).
