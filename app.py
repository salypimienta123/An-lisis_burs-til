import streamlit as st
import yfinance as yf

from src.comparativa import comparativa_activos
from src.charts import grafico_xtb
from src.download_data import descargar_datos
from src.heatmaps import rentabilidades_anuales
from src.heatmaps import crear_heatmap
from src.forex import grafico_divisas
from src.fundamentals import obtener_fundamentales
from src.stats import estadisticas

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

tab1, tab2, tab3, tab4 = st.tabs(["📚Inversion","📈 Acciones","💱 Divisas","📈 Comparativa"])

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

            st.latex(r"P(H|D)=\frac{P(D|H)P(H)}{P(D)}")

            st.write("""
            - H = hipótesis
            - D = datos observados
            - Base de la inferencia bayesiana
            """)

        with st.container(border=True):
            st.markdown("### 🎯 Actualización Bayesiana")

            st.latex(r"P(\theta|X)\propto P(X|\theta)P(\theta)")

            st.write("""
            - Prior
            - Likelihood
            - Posterior
            """)

    with col2:
        with st.container(border=True):
            st.markdown("### 📈 Modelo de Rentabilidades")

            st.latex(r"r_t \sim N(\mu,\sigma^2)")
            st.latex(r"\mu \sim N(\mu_0,\tau^2)")

            st.write("""
            Modelo básico para retornos financieros.
            """)

        with st.container(border=True):
            st.markdown("### 🤖 Aplicación al Proyecto")

            st.latex(
                r"P(\text{Batir SP500}\mid\text{Fundamentales, Momentum, Calidad})"
            )

            st.write("""
            Probabilidad posterior de que una acción
            supere al mercado.
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

    st.subheader("Análisis de Divisas")

    fig = grafico_divisas()

    st.pyplot(
        fig,
        use_container_width=True
    )
with tab4:
    #----------------------------------
    # comparativa sp, btc y msci world
    # ----------------------------------
    st.divider()
    st.subheader("📈 Comparativa frente al Mercado")
    fig_comp = comparativa_activos(ticker)
    st.pyplot(fig_comp, use_container_width=True)
    col_fund, col_stats = st.columns(2)