"""Genera el informe PDF del Taller 6 con DATOS REALES de Yahoo Finance.

Uso (Colab o local, con internet):
    pip install yfinance reportlab pandas numpy
    1) Ejecuta la app y toma las capturas reales; guárdalas en la carpeta `capturas/`.
    2) Completa la sección CONFIGURACIÓN.
    3) python generar_informe.py   ->  Informe_S23_Taller_6.pdf

El script NO inventa capturas: si faltan imágenes o Yahoo no responde, se detiene con un mensaje.
Todas las cifras y las interpretaciones numéricas se calculan con los datos descargados.
"""
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from PIL import Image as PILImage

# ============================ CONFIGURACIÓN (COMPLETAR) ============================
NOMBRE = "Sebastián Giraldo"
GRUPO = "COMPLETAR GRUPO"
REPO_URL = "https://github.com/sgiraldo0232-lang/LenguajesdeProgramacionITM/tree/main/S23_Taller_6_Streamlit"
APP_URL = ""                      # URL de Streamlit Community Cloud, si la desplegaste; si no, déjala vacía
TICKERS = ["NFLX", "V", "JPM"]    # los mismos que seleccionaste al tomar las capturas
PERIODO = "1y"                    # el mismo período de las capturas: 3mo, 6mo, 1y, 2y, 5y
CARPETA_CAPTURAS = Path("capturas")
# (archivo, título, qué demuestra) — ajusta nombres y explicaciones a lo que realmente muestra cada captura
CAPTURAS = [
    ("01_interfaz.png", "Interfaz general", "La aplicación abre con banner, título, barra lateral de configuración y las pestañas; indica que los datos provienen de Yahoo Finance."),
    ("02_controles.png", "Controles con tres activos", "Los controles (activos, período, capital, media móvil, fuente) con tres activos seleccionados; demuestra la interactividad."),
    ("03_indicadores.png", "Indicadores", "Rendimiento acumulado, volatilidad anualizada y máximo drawdown por activo, calculados a partir de los datos descargados."),
    ("04_comparacion.png", "Gráfico de comparación", "Precios normalizados en base 100: permite comparar la trayectoria de los tres activos desde un punto común."),
    ("05_correlacion.png", "Correlación", "Matriz de correlación de rendimientos diarios entre los activos seleccionados."),
]
SALIDA = "Informe_S23_Taller_6.pdf"
# ===================================================================================
NOMBRE_PERIODO = {"3mo": "3 meses", "6mo": "6 meses", "1y": "1 año", "2y": "2 años", "5y": "5 años"}
DIAS = 252


def descargar(tickers, periodo):
    d = yf.download(list(tickers), period=periodo, auto_adjust=True, progress=False, threads=False)
    if d is None or d.empty:
        sys.exit("Yahoo Finance no devolvió datos. Reintenta más tarde; el informe no usa datos simulados.")
    c = d["Close"] if isinstance(d.columns, pd.MultiIndex) else d[["Close"]].rename(columns={"Close": tickers[0]})
    if isinstance(c, pd.Series):
        c = c.to_frame(tickers[0])
    c = c.reindex(columns=list(tickers)).sort_index().ffill().dropna()
    if len(c) < 30:
        sys.exit("Menos de 30 sesiones comunes: no hay datos suficientes.")
    return c


def indicadores(p):
    r = p.pct_change().dropna()
    cart = (1 + r.mean(axis=1)).cumprod()
    return pd.DataFrame({
        "rend": p.iloc[-1] / p.iloc[0] - 1,
        "vol": r.std(ddof=1) * np.sqrt(DIAS),
        "dd": (p / p.cummax() - 1).min(),
    }), r, cart


faltan = [a for a, _, _ in CAPTURAS if not (CARPETA_CAPTURAS / a).exists()]
if len(CAPTURAS) - len(faltan) < 4:
    sys.exit(f"Se necesitan al menos 4 capturas reales en '{CARPETA_CAPTURAS}/'. Faltan: {faltan}")
CAPTURAS = [c for c in CAPTURAS if c[0] not in faltan]

precios = descargar(TICKERS, PERIODO)
ind, rend, cart = indicadores(precios)
corr = rend.corr()
ini, fin = precios.index[0].date(), precios.index[-1].date()
mejor, peor = ind["rend"].idxmax(), ind["rend"].idxmin()
mas_vol, menos_vol = ind["vol"].idxmax(), ind["vol"].idxmin()
pares = {(a, b): corr.loc[a, b] for i, a in enumerate(corr.columns) for b in corr.columns[i + 1:]}
par_alto = max(pares, key=pares.get)
par_bajo = min(pares, key=pares.get)
mov_dd = ind["dd"].idxmin()

# período: cómo cambia el análisis
filas_per = []
for per in ["3mo", "6mo", "1y", "2y"]:
    try:
        pp = descargar(TICKERS, per)
        ii, rr, _ = indicadores(pp)
        filas_per.append((per, ii["rend"].idxmax(), ii["rend"].max(), ii["vol"].idxmax(), ii["vol"].max(),
                          rr.corr().where(~np.eye(len(TICKERS), dtype=bool)).stack().mean()))
    except SystemExit:
        pass

# ------------------------------------------------------------------ estilos
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=15, spaceBefore=10, spaceAfter=6, textColor=colors.HexColor("#10243a"))
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=11.5, spaceBefore=6, spaceAfter=3)
P = ParagraphStyle("P", parent=ss["BodyText"], fontSize=10, leading=14, alignment=TA_JUSTIFY, spaceAfter=5)
PC = ParagraphStyle("PC", parent=P, fontSize=9, leading=12, textColor=colors.HexColor("#333333"))
TIT = ParagraphStyle("TIT", parent=ss["Title"], fontSize=24, leading=28, textColor=colors.HexColor("#10243a"))
pc = lambda x: f"{x * 100:+.2f} %"
pu = lambda x: f"{x * 100:.2f} %"


def tabla(datos, anchos=None, cab=True):
    t = Table(datos, colWidths=anchos, repeatRows=1 if cab else 0)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#10243a")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9), ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef3f8")]),
    ]))
    return t


S = []
# Portada
S += [Spacer(1, 4 * cm), Paragraph("S23 · Taller 6", TIT), Paragraph("Observatorio Financiero con Streamlit", ss["Heading2"]),
      Spacer(1, 1 * cm), Paragraph(f"<b>Nombre:</b> {NOMBRE}", P), Paragraph(f"<b>Grupo:</b> {GRUPO}", P),
      Paragraph(f"<b>Fecha:</b> {date.today():%d/%m/%Y}", P), Paragraph("<b>Asignatura:</b> Lenguajes de Programación · Ingeniería Financiera · ITM", P),
      Paragraph(f"<b>Repositorio:</b> {REPO_URL}", P), PageBreak()]

# 1 Objetivo
S += [Paragraph("1. Objetivo", H1), Paragraph(
    "El observatorio financiero resuelve un problema práctico: comparar el comportamiento histórico de varios activos de forma "
    "rápida, homogénea y reproducible. Un analista que mire solo precios en dólares no puede saber cuál activo rindió más ni cuál fue "
    "más riesgoso, porque cada activo tiene un nivel de precio distinto. La aplicación normaliza los precios, calcula rendimientos, "
    "volatilidad, medias móviles, drawdown y correlaciones, y deja que el usuario cambie los activos y el período para ver cómo "
    "cambian las conclusiones.", P)]

# 2 Desarrollo
S += [Paragraph("2. Desarrollo", H1),
      Paragraph("<b>Herramientas.</b> <b>Streamlit</b> convierte un script de Python en una aplicación web: cada instrucción (por ejemplo "
                "<i>st.multiselect</i>, <i>st.line_chart</i>) se vuelve un componente visible y, cuando el usuario cambia un control, el script se "
                "ejecuta de nuevo con los nuevos valores. <b>yfinance</b> descarga precios históricos de Yahoo Finance; se usan precios de cierre "
                "ajustados por dividendos y splits. <b>Pandas</b> organiza los precios en un DataFrame con fechas como índice y calcula "
                "rendimientos (<i>pct_change</i>), estadísticas (<i>describe</i>, <i>std</i>, <i>corr</i>) y promedios móviles (<i>rolling</i>).", P),
      Paragraph("<b>Controles.</b> Barra lateral con: activos (de 1 a 6), período histórico, capital inicial, ventana de la media móvil y fuente de datos "
                "(Yahoo Finance o simulados de práctica; si se usan datos simulados la app lo advierte en rojo). Seis pestañas: comparación, "
                "indicadores, medias móviles, estadística y correlación, riesgo y proyecto.", P),
      Paragraph("<b>Cálculos.</b> Rendimiento diario r<sub>t</sub> = P<sub>t</sub>/P<sub>t-1</sub> − 1. Rendimiento acumulado de un activo = "
                "P<sub>final</sub>/P<sub>inicial</sub> − 1. Precio normalizado = P<sub>t</sub>/P<sub>0</sub> × 100. Volatilidad anualizada = "
                "desviación estándar diaria × √252. Drawdown = precio / máximo previo − 1. Correlación de Pearson entre rendimientos diarios. "
                "La cartera de pesos iguales usa la media de los rendimientos diarios (rebalanceo diario, sin costos).", P)]

# 3 Evidencias
S += [PageBreak(), Paragraph("3. Evidencias", H1),
      Paragraph(f"Capturas reales de la aplicación funcionando (activos: {', '.join(TICKERS)}; período: {NOMBRE_PERIODO[PERIODO]}).", P)]
for i, (arch, titulo, expl) in enumerate(CAPTURAS, 1):
    ruta = CARPETA_CAPTURAS / arch
    w, h = PILImage.open(ruta).size
    ancho = min(16.5 * cm, 16.5 * cm); alto = ancho * h / w
    if alto > 10 * cm:
        alto = 10 * cm; ancho = alto * w / h
    S += [Paragraph(f"Captura {i}. {titulo}", H2), Image(str(ruta), width=ancho, height=alto), Paragraph(expl, PC), Spacer(1, 0.3 * cm)]

# 4 Resultados
S += [PageBreak(), Paragraph("4. Resultados", H1),
      Paragraph(f"Comparación de {', '.join(TICKERS)} con precios de Yahoo Finance entre {ini} y {fin} ({len(precios)} sesiones).", P)]
datos = [["Activo", "Rendimiento acumulado", "Volatilidad anualizada", "Máximo drawdown"]]
for t in TICKERS:
    datos.append([t, pc(ind.loc[t, "rend"]), pu(ind.loc[t, "vol"]), pu(ind.loc[t, "dd"])])
S += [tabla(datos, [3 * cm, 4.5 * cm, 4.5 * cm, 4 * cm]), Spacer(1, 0.3 * cm)]
cdat = [[""] + TICKERS] + [[a] + [f"{corr.loc[a, b]:.2f}" for b in TICKERS] for a in TICKERS]
S += [Paragraph("Matriz de correlación de rendimientos diarios:", P), tabla(cdat, [3 * cm] + [3 * cm] * len(TICKERS)), Spacer(1, 0.3 * cm)]
S += [Paragraph(
    f"<b>Rendimiento.</b> {mejor} obtuvo el mayor rendimiento acumulado ({pc(ind.loc[mejor, 'rend'])}) y {peor} el menor ({pc(ind.loc[peor, 'rend'])}). "
    f"<b>Volatilidad.</b> {mas_vol} fue el más volátil ({pu(ind.loc[mas_vol, 'vol'])} anualizada) y {menos_vol} el menos volátil ({pu(ind.loc[menos_vol, 'vol'])}). "
    + ("Un mayor rendimiento coincidió con la mayor volatilidad, pero eso no es una regla. " if mejor == mas_vol else
       f"El activo de mayor rendimiento ({mejor}) no fue el más volátil: más riesgo no implicó más rentabilidad en este período. ")
    + f"<b>Comportamiento temporal.</b> La mayor caída desde un máximo previo fue la de {mov_dd} ({pu(ind.loc[mov_dd, 'dd'])}). "
    f"<b>Correlación.</b> El par más correlacionado fue {par_alto[0]}–{par_alto[1]} ({pares[par_alto]:.2f}) y el menos correlacionado {par_bajo[0]}–{par_bajo[1]} ({pares[par_bajo]:.2f}). "
    "Una correlación positiva significa que los rendimientos tienden a moverse en el mismo sentido; cuanto más cercana a 0, menos relación lineal hay, y por eso combinar "
    "activos poco correlacionados reduce el riesgo de la cartera. La correlación no implica causalidad y puede cambiar con el período.", P)]

# 5 Conclusiones
S += [Paragraph("5. Conclusiones", H1), Paragraph(
    f"El análisis muestra que comparar precios nominales engaña y que la base 100 revela el rendimiento relativo: en este período {mejor} lideró y {peor} quedó rezagado. "
    "También se aprende que rendimiento y riesgo se miden por separado: la volatilidad describe dispersión, no ganancia, y el drawdown muestra la pérdida desde el pico, "
    "que es lo que un inversionista sentiría. La app permite probar rápidamente cómo cambian los resultados al cambiar activos y período.", P),
      Paragraph("<b>Limitaciones de los datos históricos.</b> Describen el pasado y no garantizan el futuro; dependen del período elegido; los precios ajustados "
                "no incluyen costos de transacción ni impuestos; la cartera supone pesos iguales con rebalanceo diario, difícil de replicar; Yahoo Finance es una fuente gratuita "
                "que puede fallar o corregir datos; y una muestra corta puede dar correlaciones y volatilidades poco estables. Es un ejercicio académico, no asesoría financiera.", P)]

# 6 Enlaces
S += [Paragraph("6. Enlaces", H1), Paragraph(f"<b>Repositorio GitHub:</b> {REPO_URL}", P),
      Paragraph(f"<b>Aplicación desplegada:</b> {APP_URL if APP_URL else 'no desplegada (el enlace temporal de Colab no se usa como evidencia permanente)'}", P)]

# Anexo preguntas
S += [PageBreak(), Paragraph("Anexo. Preguntas de interpretación", H1)]
preg = [
    ("1. ¿Cuál de los activos obtuvo mayor rendimiento en el período seleccionado?",
     f"{mejor}, con {pc(ind.loc[mejor, 'rend'])} entre {ini} y {fin}. El menor fue {peor} ({pc(ind.loc[peor, 'rend'])})."),
    ("2. ¿Qué activo presentó mayor volatilidad? ¿Cómo lo calculaste?",
     f"{mas_vol}, con {pu(ind.loc[mas_vol, 'vol'])} anualizada. Se calcula la desviación estándar de los rendimientos diarios (pct_change, std con ddof=1) y se multiplica por √252, el número aproximado de sesiones de un año."),
    ("3. ¿Por qué normalizar los precios a una base común permite compararlos?",
     "Porque cada activo cotiza en un nivel distinto y una línea alta no significa mejor desempeño. Al dividir por el precio inicial y multiplicar por 100, todos parten del mismo punto y se lee el cambio relativo."),
    ("4. ¿Qué información aportan las medias móviles y qué no permiten asegurar?",
     "Suavizan el ruido diario y muestran la tendencia reciente; cuando el precio cruza la media se interpreta un cambio de tendencia. Son indicadores rezagados: no predicen precios futuros ni aseguran que la tendencia continúe."),
    ("5. ¿Qué significa una correlación positiva o negativa entre dos activos?",
     f"Positiva: los rendimientos tienden a subir y bajar juntos. Negativa: tienden a moverse en sentido contrario. Cerca de 0: sin relación lineal. En estos datos el rango fue de {pares[par_bajo]:.2f} ({par_bajo[0]}–{par_bajo[1]}) a {pares[par_alto]:.2f} ({par_alto[0]}–{par_alto[1]})."),
]
for q, a in preg:
    S += [Paragraph(f"<b>{q}</b>", P), Paragraph(a, P)]
tp = [["Período", "Mayor rendimiento", "Mayor volatilidad", "Correlación media entre pares"]]
for per, mj, vr, mv, vv, cm_ in filas_per:
    tp.append([NOMBRE_PERIODO[per], f"{mj} ({pc(vr)})", f"{mv} ({pu(vv)})", f"{cm_:.2f}"])
S += [Paragraph("<b>6. ¿Qué cambia en el análisis cuando se modifica el período?</b>", P), tabla(tp, [3 * cm, 4.5 * cm, 4.5 * cm, 4.5 * cm]), Spacer(1, 0.2 * cm)]
if len(filas_per) > 1:
    lideres = {f[1] for f in filas_per}
    S += [Paragraph(
        ("El activo con mayor rendimiento cambia según el período (" + ", ".join(f"{NOMBRE_PERIODO[f[0]]}: {f[1]}" for f in filas_per) + "). "
         if len(lideres) > 1 else f"En todos los períodos probados el activo de mayor rendimiento fue {next(iter(lideres))}, aunque sus cifras cambian. ")
        + "El rendimiento acumulado, la volatilidad y las correlaciones dependen de la ventana elegida: un período corto refleja eventos recientes, y uno largo "
        "promedia distintos regímenes de mercado. Por eso no se debe generalizar una conclusión de un solo período.", P)]

doc = SimpleDocTemplate(SALIDA, pagesize=A4, leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
                        title="S23 Taller 6 - Observatorio Financiero", author=NOMBRE)
doc.build(S)
print("Informe generado:", SALIDA)
