# S23 · Taller 6 — Observatorio Financiero (Streamlit)

Aplicación web hecha con Python y Streamlit para comparar activos financieros con precios históricos reales.
Proyecto individual de **Lenguajes de Programación · Ingeniería Financiera · ITM**.

## ¿Qué hace?
- Permite elegir de 1 a 6 activos (mínimo 3 para el taller), el período (3 meses a 5 años), el capital inicial y la ventana de la media móvil.
- Muestra precios normalizados (base 100), valor de una cartera de pesos iguales, rendimientos diarios, indicadores por activo, medias móviles, estadística descriptiva, correlaciones y drawdown.
- Indica de forma visible cuando usa **datos simulados** (si Yahoo Finance no responde o si el usuario elige la fuente de práctica). Los datos simulados no son cotizaciones reales.

## ¿De dónde provienen los datos?
De **Yahoo Finance**, mediante la biblioteca `yfinance`, con precios de cierre ajustados por dividendos y splits (`auto_adjust=True`). Los datos se guardan en caché 30 minutos.

## ¿Cómo se ejecuta?
```bash
pip install -r requirements.txt
streamlit run app.py
```
La app abre en `http://localhost:8501`. La carpeta `assets/` debe estar junto a `app.py`.

En Google Colab: ejecuta `streamlit run app.py` en segundo plano y abre la URL de un túnel (Cloudflare). Ese enlace es temporal; la evidencia permanente es este repositorio.

## ¿Qué significan los indicadores?
| Indicador | Cómo se calcula | Cómo se lee |
|---|---|---|
| Rendimiento diario | `P_t / P_(t-1) − 1` (`pct_change`) | Cambio porcentual de un día al siguiente |
| Rendimiento acumulado (activo) | `P_final / P_inicial − 1` | Cuánto cambió el precio en todo el período |
| Rendimiento acumulado (cartera) | `∏(1 + r_t) − 1` con r_t = media de los rendimientos diarios | Cartera de pesos iguales con rebalanceo diario, sin comisiones ni impuestos |
| Precio normalizado (base 100) | `P_t / P_0 × 100` | Permite comparar activos de precios distintos desde un mismo punto de partida |
| Volatilidad anualizada | `desv. estándar diaria × √252` | Dispersión de los rendimientos; más volatilidad es más riesgo, no más rentabilidad |
| Media móvil | Promedio de las últimas *n* sesiones | Suaviza el ruido y muestra la tendencia reciente; llega con retraso y no predice |
| Correlación (Pearson) | Entre rendimientos diarios, de −1 a +1 | Relación lineal entre dos activos; no implica causalidad |
| Drawdown | `precio / máximo previo − 1` | Caída desde el último pico |

## Limitaciones
- Los resultados históricos no garantizan rentabilidades futuras.
- No se incluyen costos de transacción, impuestos ni dividendos fuera del ajuste de precios.
- Yahoo Finance puede fallar o limitar consultas; la app lo avisa y no oculta el uso de datos simulados.
- Uso académico: no constituye asesoría financiera.

## Contenido de la carpeta
`app.py` · `requirements.txt` · `README.md` · `assets/banner_financiero.png` · informe PDF · `generar_informe.py` (genera el informe con datos reales).

## Autor
Sebastián Giraldo · Ingeniería Financiera · ITM
