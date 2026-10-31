"""Observatorio Financiero · S23 Taller 6 (Streamlit + yfinance + pandas).

Compara activos con precios históricos de Yahoo Finance: precios normalizados,
rendimientos, volatilidad anualizada, medias móviles, drawdown y correlaciones.
Si Yahoo Finance no responde, la app lo dice y muestra datos SIMULADOS rotulados.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf

DIAS_ANIO = 252
UNIVERSO = ["NFLX", "V", "TSLA", "JPM", "AAPL", "MSFT", "NVDA", "GOOGL", "CVX", "JNJ", "PG", "SPY", "GLD"]
PERIODOS = {"3mo": "3 meses", "6mo": "6 meses", "1y": "1 año", "2y": "2 años", "5y": "5 años"}

st.set_page_config(page_title="Observatorio Financiero · ITM", page_icon="📈", layout="wide")
st.markdown(
    """<style>
[data-testid="stApp"]{background:linear-gradient(145deg,#0b1425,#101f33);color:#edf4ff}
[data-testid="stSidebar"]{background:#0d1c30}
[data-testid="stMetric"]{background:#172b43;padding:15px;border-radius:14px;border:1px solid #29415b}
h1,h2,h3{letter-spacing:-.03em}
</style>""",
    unsafe_allow_html=True,
)
banner = Path(__file__).parent / "assets" / "banner_financiero.png"
if banner.exists():
    st.image(str(banner), width="stretch")
st.title("FinanceLab · Observatorio Financiero")
st.caption("ITM · Lenguajes de Programación · Python · Streamlit · Yahoo Finance")

# ---------------------------------------------------------------- controles
st.sidebar.header("⚙️ Configura tu análisis")
tickers = st.sidebar.multiselect("Activos (mínimo 3 para el taller)", UNIVERSO,
                                 default=["NFLX", "V", "JPM"], max_selections=6)
periodo = st.sidebar.selectbox("Período histórico", list(PERIODOS), index=2,
                               format_func=lambda x: PERIODOS[x])
capital = st.sidebar.number_input("Capital inicial (USD)", min_value=100.0, value=10000.0, step=500.0)
ventana = st.sidebar.slider("Ventana de media móvil (sesiones)", 5, 60, 20)
fuente = st.sidebar.radio("Fuente de datos", ["Yahoo Finance", "Simulados (práctica)"], index=0)


# ------------------------------------------------------------------- datos
@st.cache_data(ttl=1800, show_spinner=False)
def descargar_precios(simbolos, periodo):
    datos = yf.download(list(simbolos), period=periodo, auto_adjust=True, progress=False, threads=False)
    if datos is None or datos.empty:
        raise ValueError("Yahoo Finance no devolvió datos")
    if isinstance(datos.columns, pd.MultiIndex):
        cierre = datos["Close"]
    else:
        cierre = datos[["Close"]].rename(columns={"Close": simbolos[0]})
    if isinstance(cierre, pd.Series):
        cierre = cierre.to_frame(name=simbolos[0])
    faltantes = [t for t in simbolos if t not in cierre.columns or cierre[t].dropna().empty]
    if faltantes:
        raise ValueError("Sin datos para: " + ", ".join(faltantes))
    return cierre.reindex(columns=list(simbolos)).sort_index().ffill().dropna()


def simular_precios(simbolos):
    rng = np.random.default_rng(23)
    fechas = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=180)
    return pd.DataFrame({t: 100 * np.cumprod(1 + rng.normal(0.0004, 0.014, len(fechas))) for t in simbolos},
                        index=fechas)


if not tickers:
    st.info("Selecciona al menos un ticker en la barra lateral.")
    st.stop()

simulados = fuente == "Simulados (práctica)"
if simulados:
    precios = simular_precios(tickers)
else:
    try:
        with st.spinner("Consultando Yahoo Finance..."):
            precios = descargar_precios(tuple(tickers), periodo)
        if len(precios) < 30:
            raise ValueError("No hay suficientes precios comunes (menos de 30 sesiones)")
    except Exception as error:
        st.warning("Yahoo Finance no está disponible. Se muestran DATOS SIMULADOS para continuar la práctica.")
        st.caption(f"Detalle técnico: {error}")
        precios = simular_precios(tickers)
        simulados = True

if simulados:
    st.error("MODO DEMOSTRACIÓN: los resultados NO corresponden a cotizaciones reales.")
else:
    st.success(f"Datos históricos de Yahoo Finance · {precios.index[0].date()} a {precios.index[-1].date()} "
               f"· {len(precios)} sesiones")

# ---------------------------------------------------------------- cálculos
rendimientos = precios.pct_change().dropna()                      # r_t = P_t / P_{t-1} - 1
cartera = rendimientos.mean(axis=1)                                # pesos iguales, rebalanceo diario
acumulado = (1 + cartera).cumprod()
valor_inversion = capital * acumulado
base_100 = precios.div(precios.iloc[0]) * 100                      # base común = 100
rend_acum = precios.iloc[-1] / precios.iloc[0] - 1                 # rendimiento acumulado por activo
vol_anual = rendimientos.std(ddof=1) * np.sqrt(DIAS_ANIO)          # volatilidad anualizada
drawdown_activos = precios / precios.cummax() - 1
drawdown_cartera = acumulado / acumulado.cummax() - 1

tabla = pd.DataFrame({
    "Rendimiento acumulado": rend_acum,
    "Volatilidad anualizada": vol_anual,
    "Máximo drawdown": drawdown_activos.min(),
})

c1, c2, c3, c4 = st.columns(4)
c1.metric("Rendimiento acumulado (cartera)", f"{acumulado.iloc[-1] - 1:+.2%}")
c2.metric("Volatilidad anualizada (cartera)", f"{cartera.std(ddof=1) * np.sqrt(DIAS_ANIO):.2%}")
c3.metric("Valor final teórico", f"USD {valor_inversion.iloc[-1]:,.2f}")
c4.metric("Mayor rendimiento", f"{rend_acum.idxmax()} ({rend_acum.max():+.2%})")
st.caption("Cartera con pesos iguales y rebalanceo diario; sin costos, impuestos ni dividendos adicionales.")

p1, p2, p3, p4, p5, p6 = st.tabs(["📈 Comparación", "🧮 Indicadores", "〰️ Medias móviles",
                                  "📊 Estadística y correlación", "🛡️ Riesgo", "ℹ️ Proyecto"])

with p1:
    st.subheader("Precios normalizados · base 100")
    st.line_chart(base_100)
    izq, der = st.columns(2)
    with izq:
        st.subheader("Valor de la inversión (cartera)")
        st.line_chart(valor_inversion.rename("USD"))
    with der:
        st.subheader("Rendimiento diario de la cartera (%)")
        st.bar_chart(cartera.mul(100).rename("%"))
    st.info("La escala base 100 permite comparar trayectorias aunque los activos tengan precios distintos.")

with p2:
    st.subheader("Indicadores por activo")
    st.dataframe(tabla.style.format("{:.2%}"), width="stretch")
    a, b = st.columns(2)
    with a:
        fig = px.bar(rend_acum.mul(100).rename("Rendimiento acumulado (%)"), title="Rendimiento acumulado (%)",
                     labels={"value": "%", "index": "Activo"})
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width="stretch")
    with b:
        fig = px.bar(vol_anual.mul(100).rename("Volatilidad anualizada (%)"), title="Volatilidad anualizada (%)",
                     labels={"value": "%", "index": "Activo"})
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width="stretch")
    st.info(f"Volatilidad anualizada = desviación estándar diaria × √{DIAS_ANIO}. "
            "Mayor volatilidad significa más dispersión de resultados, no mayor rentabilidad.")

with p3:
    activo = st.selectbox("Activo", list(precios.columns))
    sma = precios[activo].rolling(ventana).mean()
    sma_larga = precios[activo].rolling(ventana * 2).mean()
    graf = pd.DataFrame({f"{activo} (precio)": precios[activo], f"Media móvil {ventana}": sma,
                         f"Media móvil {ventana * 2}": sma_larga})
    st.line_chart(graf)
    st.info("La media móvil suaviza el ruido y muestra la tendencia reciente; es un indicador rezagado: "
            "no predice precios futuros ni asegura que la tendencia continúe.")

with p4:
    st.subheader("Estadística descriptiva de rendimientos diarios")
    resumen = pd.DataFrame({
        "Media (%)": rendimientos.mean() * 100,
        "Mediana (%)": rendimientos.median() * 100,
        "Desv. estándar (%)": rendimientos.std() * 100,
        "Mínimo (%)": rendimientos.min() * 100,
        "Máximo (%)": rendimientos.max() * 100,
    })
    st.dataframe(resumen.round(3), width="stretch")
    x, y = st.columns(2)
    with x:
        fig = px.histogram(x=cartera * 100, nbins=30, title="Distribución de rendimientos diarios (cartera)",
                           labels={"x": "Rendimiento (%)", "y": "Frecuencia"})
        st.plotly_chart(fig, width="stretch")
    with y:
        if len(tickers) >= 2:
            fig = px.imshow(rendimientos.corr(), text_auto=".2f", zmin=-1, zmax=1,
                            color_continuous_scale="RdBu_r", title="Correlación de rendimientos diarios")
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Selecciona al menos dos activos para ver la correlación.")
    st.info("Correlación cercana a +1: se mueven juntos; cercana a −1: en sentido contrario; cercana a 0: "
            "sin relación lineal. Una correlación alta no implica causalidad.")

with p5:
    st.subheader("Drawdown: caída desde el máximo previo")
    st.line_chart(drawdown_activos.rename(columns=lambda t: f"{t}"))
    st.line_chart(drawdown_cartera.rename("Cartera"))
    peor = drawdown_activos.min()
    st.info(f"Mayor caída desde máximo en el período: {peor.idxmin()} ({peor.min():.2%}). "
            "Un drawdown mide la pérdida desde el pico, no la pérdida respecto de la compra.")

with p6:
    st.subheader("Cómo se construyó")
    st.write("**Layout:** sidebar, columns, tabs. **Widgets:** multiselect, selectbox, slider, number_input, radio.")
    st.write("**Datos:** yfinance (Yahoo Finance) y pandas. **Gráficos:** Streamlit y Plotly.")
    st.write("**Fórmulas:** r_t = P_t/P_(t−1) − 1; acumulado = ∏(1+r_t) − 1; volatilidad = σ_diaria·√252.")
    st.write("**Autor:** Sebastián Giraldo · Ingeniería Financiera · ITM")

with st.expander("🔎 Ver datos y descargar CSV"):
    st.dataframe(precios.tail(30), width="stretch")
    st.download_button("Descargar precios CSV", precios.to_csv().encode("utf-8"), "precios_financelab.csv", "text/csv")
st.caption("Uso académico. Los resultados históricos no garantizan rentabilidades futuras.")
