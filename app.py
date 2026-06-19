import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf

from src.comparativa import comparativa_activos
from src.charts import grafico_xtb
from src.download_data import descargar_datos
from src.heatmaps import rentabilidades_anuales
from src.heatmaps import crear_heatmap
from src.heatmaps_gpt import heatmap_interactivo_empresa
from src.forex import analisis_bayesiano
from src.forex import analizar_noticias
from src.forex import grafico_divisas
from src.fundamentals import obtener_fundamentales
from src.stats import estadisticas
from src.mapa import crear_mapa_indices


def mostrar_bloque_noticias(noticias, impacto_bayesiano=None):
    st.markdown("### 📰 Noticias recientes")

    if not noticias["noticias"]:
        st.info("No hay noticias recientes disponibles para este ticker.")
        return

    impacto = impacto_bayesiano
    if impacto is None:
        signo = 1 if noticias["score"] >= 0 else -1
        impacto = signo * noticias["peso_bayesiano"] * 100

    col_sent, col_impacto, col_pos, col_neg = st.columns(4)
    col_sent.metric("Sentimiento agregado", f"{noticias['score']:+.0f}")
    col_impacto.metric("Impacto Bayesiano", f"{impacto:+.2f}%")
    col_pos.metric("Noticias positivas", noticias["positivas"])
    col_neg.metric("Noticias negativas", noticias["negativas"])

    tabla_noticias = [
        {
            "Fecha": noticia["fecha"],
            "Fuente": noticia["fuente"],
            "Sentimiento": noticia["sentimiento"],
            "Titulo original": noticia["titulo"],
            "Traduccion ES": noticia["titulo_es"],
            "Leer noticia": noticia["url"],
        }
        for noticia in noticias["noticias"]
    ]
    st.dataframe(
        tabla_noticias,
        use_container_width=True,
        column_config={
            "Leer noticia": st.column_config.LinkColumn(
                "Leer noticia",
                display_text="Abrir enlace",
            )
        },
        hide_index=True,
    )


# --------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------

st.set_page_config(page_title="Analizador Bursátil",page_icon="📈",layout="wide")

#st.title("📈 Analizador Bursátil")

st.markdown("""
<div style='text-align:center;padding:15px;border-radius:10px;background-color:#f5f5f5;'>

<h3>Dashboard Financiero Inversión - Gabriel Costa</h3>

Análisis de acciones mediante métodos financieros. Aplicamos estadística Bayesiana para actualizar
nuestro

📊 Gráfico Técnico • 🔥 Heatmap • 📈 Comparativa • 💰 Fundamentales • 📉 Estadísticas

</div>
""", unsafe_allow_html=True)

st.divider()

# --------------------------------------------------
# PESTAÑAS
# --------------------------------------------------

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📚Inversion","📈 Acciones","🧠 Bayes Investing","📉 Comparativa","🔥 Heatmap GPT","🌍 Mapa Mundial"])

# --------------------------------------------------
# Inversiones
# --------------------------------------------------

with tab1:

    st.markdown("""
    <h2 style='text-align:center;'>
     Filosofías de Inversión
    </h2>
    """, unsafe_allow_html=True)

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:

        with st.container(border=True):
            st.markdown("""
            ### 💎 Value Investing

            - Empresas infravaloradas
            - PER bajo
            - Margen de seguridad / Valor intrínseco

            **Graham • Buffett**
            """)

        with st.container(border=True):
            st.markdown("""
            ### 💵 Dividend Investing

            - Dividend Yield
            - Payout Ratio
            - Dividend Growth

            **Coca-Cola • J&J**
            """)

    with col2:

        with st.container(border=True):
            st.markdown("""
            ### 🚀 Growth Investing

            - Crecimiento EPS
            - Crecimiento ventas
            - Expansión del negocio

            **Nvidia • Amazon**
            """)

        with st.container(border=True):
            st.markdown("""
            ### 📈 Momentum Investing

            - Fuerza relativa
            - Nuevos máximos
            - Tendencias alcistas

            **Trend Following**
            """)

    with col3:

        with st.container(border=True):
            st.markdown("""
            ### 🏆 Quality Investing

            - ROE elevado
            - Baja deuda
            - Márgenes altos

            **Microsoft • Visa**
            """)

        with st.container(border=True):
            st.markdown("""
            ### 🌎 Index Investing

            - ETFs globales
            - Diversificación
            - Bajo coste

            **SPY • VWCE • URTH**
            """)
    st.divider()

    st.markdown("""
    <h2 style='text-align:center;'>
    🧠 Estadística Bayesiana
    </h2>
    """, unsafe_allow_html=True)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("### 📖 Teorema de Bayes")

            st.latex(r"P(\text{Compra}\mid E)=\frac{P(E\mid\text{Compra})P(\text{Compra})}{P(E)}")

            st.write("""
            - Hipótesis: la acción es una buena compra
            - E = evidencias observadas de la empresa
            - No predice precios: actualiza una probabilidad de compra
            """)

        with st.container(border=True):
            st.markdown("### 🎯 Actualización Bayesiana")

            st.latex(r"\text{Odds posteriores}=\text{Odds previos}\times LR(E)")

            st.write("""
            - Prior inicial: 50%
            - Cada evidencia positiva aumenta las odds
            - Cada evidencia negativa reduce las odds
            """)

    with col2:
        with st.container(border=True):
            st.markdown("### 📈 Evidencias utilizadas")

            st.latex(r"E=\{Value,Dividend,Growth,Momentum,Quality,News\}")

            st.write("""
            - Fundamentales y valoración
            - Calidad, crecimiento y momentum
            - Noticias recientes con peso máximo limitado
            """)

        with st.container(border=True):
            st.markdown("### 🤖 Aplicación al Proyecto")

            st.latex(
                r"P(\text{Compra}\mid\text{Value,Quality,Growth,Momentum,News})"
            )

            st.write("""
            El resultado final clasifica la acción como
            Venta, Evitar, Neutral, Compra o Compra Fuerte.
            """)

# --------------------------------------------------
# ACCIONES
# --------------------------------------------------

with tab2:
    st.subheader("Análisis de Acciones")
    ticker = st.text_input("Ticker",value="MSFT").upper()
    if st.button("Analizar"):
        # ----------------------------------
        # DESCARGA DE DATOS
        # ----------------------------------
        datos = descargar_datos(ticker)
        rent = rentabilidades_anuales(datos)
        # ----------------------------------
        # INFO EMPRESA
        # ----------------------------------
        try:
            info = yf.Ticker(ticker).info

            st.markdown(
                f"""
                ### {info.get('longName', ticker)}

                **Sector:** {info.get('sector', 'N/A')}
                """
            )
        except:
            pass
        # ----------------------------------
        # MÉTRICAS
        # ----------------------------------
        # ----------------------------------
        precio_actual = float(datos["Close"].iloc[-1].iloc[0])
        maximo = float(datos["Close"].max().iloc[0])
        rentabilidad_total = ((datos["Close"].iloc[-1].iloc[0]/datos["Close"].iloc[0].iloc[0]) - 1) * 100
        # ----------------------------------
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Precio Actual",f"${precio_actual:.2f}")
        col2.metric("📈 Máximo Histórico",f"${maximo:.2f}")
        col3.metric("🚀 Rentabilidad Total",f"{rentabilidad_total:.1f}%")
        # ----------------------------------
        st.divider()
        # ----------------------------------
        # ----------------------------------
        # HEATMAP + GRÁFICO TÉCNICO
        # ----------------------------------
        # ----------------------------------
        col_heatmap, col_chart = st.columns([1, 1.7])
        with col_heatmap:
            st.subheader("🔥 Heatmap")
            fig_heatmap = crear_heatmap(rent,ticker)
            st.pyplot(fig_heatmap,use_container_width=True)
        with col_chart:
            st.subheader("📊 Gráfico Técnico")
            fig_xtb = grafico_xtb(datos,ticker)
            st.pyplot(fig_xtb,use_container_width=True)
        # ----------------------------------
        st.divider()
        # ----------------------------------
        with st.container(border=True):
            with st.spinner("Analizando noticias recientes..."):
                noticias_accion = analizar_noticias(ticker)
            mostrar_bloque_noticias(noticias_accion)
        # ----------------------------------
        st.divider()
        # ----------------------------------
        # ----------------------------------
        # ----------------------------------
        # ----------------------------------
        # estadistiacs y fundamentales
        # ----------------------------------
        col_fund, col_stats = st.columns([1, 1])

        with col_fund:

            st.subheader("💰 Fundamentales")

            fund = obtener_fundamentales(ticker)

            c1, c2 = st.columns(2)

            c1.metric("PER", f"{fund.iloc[1, 1]:.1f}")
            c2.metric("Forward PER", f"{fund.iloc[2, 1]:.1f}")

            c3, c4 = st.columns(2)

            c3.metric("Beta", f"{fund.iloc[4, 1]:.2f}")
            c4.metric("ROE", f"{fund.iloc[5, 1]:.1f}%")

            c5, c6 = st.columns(2)

            c5.metric("Dividend", f"{fund.iloc[3, 1]:.1f}%")
            c6.metric("Margen", f"{fund.iloc[6, 1]:.1f}%")

        with col_stats:

            st.subheader("📈 Estadísticas")

            stats = estadisticas(rent)
            c1, c2 = st.columns(2)

            c1.metric("Media", f"{stats['Rentabilidad media']:.1f}%")
            c2.metric("Mejor Año", f"{stats['Mejor año']:.1f}%")

            c3, c4 = st.columns(2)

            c3.metric("Peor Año", f"{stats['Peor año']:.1f}%")
            c4.metric("Años +", int(stats["Años positivos"]))

            st.metric("Años -", int(stats["Años negativos"]))
        # ----------------------------------
        # TABLA
        # ----------------------------------
        with st.expander(
            "📋 Ver rentabilidades anuales"):
            st.dataframe(rent,use_container_width=True)

# --------------------------------------------------
# DIVISAS
# --------------------------------------------------

with tab3:

    st.subheader("🧠 Bayes Investing")

    st.markdown("""
    Este analisis no predice el precio futuro. Estima la probabilidad de compra
    actualizando un prior inicial con evidencias fundamentales, tecnicas y de calidad.
    """)

    col_ticker_bayes, col_boton_bayes = st.columns([1, 3])

    with col_ticker_bayes:
        ticker_bayes = st.text_input(
            "Ticker",
            value="MSFT",
            key="ticker_bayes",
        ).upper()

    with col_boton_bayes:
        st.write("")
        st.write("")
        ejecutar_bayes = st.button("Analizar con Bayes", key="boton_bayes")

    st.latex(r"P(H|E)=\frac{P(E|H)P(H)}{P(E)}")
    st.latex(r"\text{Odds posteriores}=\text{Odds previos}\times LR")

    if ejecutar_bayes:
        try:
            with st.spinner("Calculando evidencias bayesianas..."):
                resultado_bayes = analisis_bayesiano(ticker_bayes)

            st.divider()
            st.markdown(f"### {resultado_bayes['nombre']}")

            col_prior, col_post, col_clasif = st.columns(3)
            col_prior.metric("Prior inicial", f"{resultado_bayes['prior']:.0f}%")
            col_post.metric("Probabilidad de Compra", f"{resultado_bayes['posterior']:.0f}%")
            col_clasif.metric("Clasificacion", resultado_bayes["clasificacion"])

            st.progress(int(resultado_bayes["posterior"]))

            st.divider()
            st.markdown("### Scores por filosofia")

            score_cols = st.columns(5)
            for columna, (nombre_score, valor_score) in zip(
                score_cols,
                resultado_bayes["scores"].items(),
            ):
                columna.metric(nombre_score.replace(" Investing", ""), f"{valor_score:.0f}/100")

            st.markdown(
                f"""
                ### 🏆 Filosofia dominante de inversion:
                **{resultado_bayes['filosofia_dominante'].upper()}**
                """
            )

            st.divider()
            st.markdown("### Evidencias y actualizacion posterior")

            evidencias_tabla = [
                {
                    "Evidencia": evidencia["evidencia"],
                    "Resultado": evidencia["resultado"],
                    "Cambio": f"{evidencia['cambio']:+.2f}%",
                    "Posterior": f"{evidencia['posterior']:.2f}%",
                }
                for evidencia in resultado_bayes["evidencias"]
            ]
            st.dataframe(evidencias_tabla, use_container_width=True)

            st.divider()
            st.markdown("### Comparacion frente a indices")

            comparacion = [
                {
                    "Indice": fila["indice"],
                    "Accion": f"{fila['rentabilidad_accion']:.2f}%",
                    "Indice rent.": f"{fila['rentabilidad_indice']:.2f}%",
                    "Bate indice": "Si" if fila["bate_indice"] else "No",
                }
                for fila in resultado_bayes["comparacion_indices"]
            ]

            if comparacion:
                st.dataframe(comparacion, use_container_width=True)
            else:
                st.info("No hay datos suficientes para comparar contra indices.")

            st.divider()
            mostrar_bloque_noticias(
                resultado_bayes["noticias"],
                resultado_bayes["impacto_noticias"],
            )

        except Exception as exc:
            st.error(f"No se pudo completar el analisis bayesiano: {exc}")
with tab4:
    #----------------------------------
    # comparativa sp, btc y msci world
    # ----------------------------------
    st.divider()
    st.subheader("📈 Comparativa frente al Mercado")
    col_accion, col_periodo, col_boton = st.columns([1, 1, 2])

    with col_accion:
        ticker_comp = st.text_input(
            "Accion",
            value="MSFT",
            key="ticker_comparativa",
        ).upper()

    with col_periodo:
        periodo_comp = st.selectbox(
            "Periodo",
            ["1y", "3y", "5y", "10y"],
            index=2,
            key="periodo_comparativa",
        )

    with col_boton:
        st.write("")
        st.write("")
        ejecutar_comparativa = st.button(
            "Comparar con mercados",
            key="boton_comparativa",
        )

    if ejecutar_comparativa:
        comparativa_activos(ticker_comp, periodo_comp)

with tab5:
    st.subheader("Heatmap interactivo de rentabilidades")

    col_ticker, col_boton = st.columns([1, 3])

    with col_ticker:
        ticker_gpt = st.text_input(
            "Ticker",
            value="MSFT",
            key="ticker_heatmap_gpt",
        ).upper()

    with col_boton:
        st.write("")
        st.write("")
        ejecutar_heatmap = st.button("Consultar empresa", key="boton_heatmap_gpt")

    if ejecutar_heatmap:
        with st.container(border=True):
            heatmap_interactivo_empresa(ticker_gpt)

with tab6:
    st.subheader("Mapa mundial de indices bursatiles")

    periodo_mapa = st.selectbox(
        "Temporalidad",
        ["Día", "Mes", "Año", "5 años"],
        index=1,
        key="periodo_mapa_mundial",
    )

    try:
        with st.spinner("Cargando datos de indices mundiales..."):
            mapa_indices = crear_mapa_indices(periodo_mapa)

        components.html(
            mapa_indices._repr_html_(),
            height=680,
            scrolling=False,
        )
    except ModuleNotFoundError as exc:
        st.error(f"Falta instalar la dependencia requerida: {exc.name}")
