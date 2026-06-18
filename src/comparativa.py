import html
import json

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf


MERCADOS = {
    "SPY": {"nombre": "S&P 500", "color": "#4f5d75", "stroke": 2.2},
    "URTH": {"nombre": "MSCI World", "color": "#7a869a", "stroke": 2.2},
    "BTC-USD": {"nombre": "Bitcoin", "color": "#d9902f", "stroke": 2.4},
    "GLD": {"nombre": "Oro", "color": "#b88a1e", "stroke": 2.2},
    "SLV": {"nombre": "Plata", "color": "#8b95a5", "stroke": 2.2},
    "QQQ": {"nombre": "Nasdaq 100", "color": "#2f7a43", "stroke": 2.2},
}


@st.cache_data(ttl=1800, show_spinner=False)
def _datos_comparativa(ticker: str, periodo: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    ticker = ticker.upper().strip()
    simbolos = [ticker] + [simbolo for simbolo in MERCADOS if simbolo != ticker]

    descarga = yf.download(
        simbolos,
        period=periodo,
        auto_adjust=True,
        progress=False,
    )

    if descarga.empty:
        return pd.DataFrame(), pd.DataFrame()

    precios = descarga["Close"] if isinstance(descarga.columns, pd.MultiIndex) else descarga
    precios = precios.dropna(axis=1, how="all").ffill().dropna()

    if ticker not in precios.columns:
        return pd.DataFrame(), pd.DataFrame()

    base = precios / precios.iloc[0] * 100
    base = base.reset_index()
    fecha_col = base.columns[0]
    base = base.rename(columns={fecha_col: "Fecha"})

    columnas = [col for col in base.columns if col != "Fecha"]
    nombres = {ticker: ticker, **{k: v["nombre"] for k, v in MERCADOS.items()}}

    serie_larga = base.melt(
        id_vars="Fecha",
        value_vars=columnas,
        var_name="Simbolo",
        value_name="Base100",
    )
    serie_larga["Nombre"] = serie_larga["Simbolo"].map(nombres).fillna(serie_larga["Simbolo"])

    resumen = []
    for simbolo in columnas:
        valores = base[simbolo].dropna()
        if valores.empty:
            continue

        actual = float(valores.iloc[-1])
        maximo = float(valores.max())
        minimo = float(valores.min())
        retorno = actual - 100
        volatilidad = float(valores.pct_change().std() * np.sqrt(252) * 100)

        resumen.append(
            {
                "Simbolo": simbolo,
                "Nombre": nombres.get(simbolo, simbolo),
                "Actual": actual,
                "Retorno": retorno,
                "Maximo": maximo,
                "Minimo": minimo,
                "Volatilidad": volatilidad,
            }
        )

    return serie_larga, pd.DataFrame(resumen).sort_values("Retorno", ascending=False)


def comparativa_activos(ticker: str, periodo: str = "5y") -> None:
    ticker = ticker.upper().strip()

    with st.spinner("Descargando accion y mercados de referencia..."):
        serie_larga, resumen = _datos_comparativa(ticker, periodo)

    if serie_larga.empty or resumen.empty:
        st.warning("No se han encontrado datos suficientes para hacer la comparativa.")
        return

    datos = _preparar_payload(serie_larga, ticker)
    resumen_payload = _preparar_resumen(resumen, ticker)
    components.html(
        _html_comparativa(datos, resumen_payload, ticker, periodo),
        height=760,
        scrolling=False,
    )

    with st.expander("Ver ranking de rentabilidad"):
        st.dataframe(resumen, use_container_width=True, hide_index=True)


def _preparar_payload(serie_larga: pd.DataFrame, ticker: str) -> list[dict]:
    estilos = {
        ticker: {"nombre": ticker, "color": "#111827", "stroke": 3.3},
        **MERCADOS,
    }

    payload = []
    for _, fila in serie_larga.iterrows():
        simbolo = fila["Simbolo"]
        estilo = estilos.get(
            simbolo,
            {"nombre": simbolo, "color": "#111827", "stroke": 2.2},
        )
        payload.append(
            {
                "date": pd.to_datetime(fila["Fecha"]).strftime("%Y-%m-%d"),
                "symbol": simbolo,
                "name": estilo["nombre"],
                "value": round(float(fila["Base100"]), 4),
                "color": estilo["color"],
                "stroke": estilo["stroke"],
                "main": simbolo == ticker,
            }
        )

    return payload


def _preparar_resumen(resumen: pd.DataFrame, ticker: str) -> list[dict]:
    registros = []
    for _, fila in resumen.iterrows():
        color = "#111827" if fila["Simbolo"] == ticker else MERCADOS.get(
            fila["Simbolo"], {}
        ).get("color", "#4f5d75")
        registros.append(
            {
                "symbol": fila["Simbolo"],
                "name": fila["Nombre"],
                "actual": round(float(fila["Actual"]), 3),
                "return": round(float(fila["Retorno"]), 3),
                "max": round(float(fila["Maximo"]), 3),
                "min": round(float(fila["Minimo"]), 3),
                "volatility": round(float(fila["Volatilidad"]), 3),
                "color": color,
                "main": fila["Simbolo"] == ticker,
            }
        )
    return registros


def _html_comparativa(datos: list[dict], resumen: list[dict], ticker: str, periodo: str) -> str:
    datos_json = json.dumps(datos, ensure_ascii=False)
    resumen_json = json.dumps(resumen, ensure_ascii=False)
    ticker_seguro = html.escape(ticker)
    periodo_seguro = html.escape(periodo)

    return f"""
    <div class="market-wrap">
      <section class="chart-panel">
        <div class="panel-head">
          <div>
            <div class="eyebrow">Market outlook</div>
            <h3>{ticker_seguro} vs mercados globales</h3>
            <p>Base 100 desde el inicio del periodo seleccionado ({periodo_seguro}).</p>
          </div>
          <div class="badge">Puntero interactivo</div>
        </div>
        <div id="legend" class="legend"></div>
        <div class="chart-box">
          <svg id="chart" viewBox="0 0 980 430" preserveAspectRatio="none"></svg>
          <div id="tooltip" class="tooltip"></div>
        </div>
      </section>

      <aside class="side-panel">
        <div class="panel-head compact">
          <div>
            <div class="eyebrow">Ranking</div>
            <h3>Quien crece mas</h3>
          </div>
        </div>
        <div id="winner" class="winner"></div>
        <div id="cards" class="cards"></div>
      </aside>
    </div>

    <script>
      const rows = {datos_json};
      const summary = {resumen_json};
      const svg = document.getElementById("chart");
      const tooltip = document.getElementById("tooltip");
      const legend = document.getElementById("legend");
      const cards = document.getElementById("cards");
      const winner = document.getElementById("winner");

      const width = 980;
      const height = 430;
      const margin = {{ top: 24, right: 120, bottom: 44, left: 58 }};
      const innerW = width - margin.left - margin.right;
      const innerH = height - margin.top - margin.bottom;

      const parseDate = value => new Date(value + "T00:00:00");
      rows.forEach(row => row.d = parseDate(row.date));

      const dates = [...new Set(rows.map(row => row.date))].sort();
      const series = [...new Map(rows.map(row => [row.symbol, {{
        symbol: row.symbol,
        name: row.name,
        color: row.color,
        stroke: row.stroke,
        main: row.main,
      }}])).values()];

      const minDate = parseDate(dates[0]);
      const maxDate = parseDate(dates[dates.length - 1]);
      const values = rows.map(row => row.value);
      const minValue = Math.min(80, Math.floor(Math.min(...values) / 10) * 10);
      const maxValue = Math.ceil(Math.max(...values) / 10) * 10;

      function xScale(date) {{
        return margin.left + ((date - minDate) / (maxDate - minDate || 1)) * innerW;
      }}

      function yScale(value) {{
        return margin.top + (1 - ((value - minValue) / (maxValue - minValue || 1))) * innerH;
      }}

      function svgEl(name, attrs = {{}}) {{
        const el = document.createElementNS("http://www.w3.org/2000/svg", name);
        Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, value));
        return el;
      }}

      function fmtDate(date) {{
        return date.toLocaleDateString("es-ES", {{ month: "short", year: "numeric" }});
      }}

      function fmtPct(value) {{
        const sign = value > 0 ? "+" : "";
        return sign + value.toFixed(1) + "%";
      }}

      function fmtBase(value) {{
        return value.toFixed(1);
      }}

      function drawGrid() {{
        for (let i = 0; i <= 5; i++) {{
          const value = minValue + ((maxValue - minValue) / 5) * i;
          const y = yScale(value);
          svg.appendChild(svgEl("line", {{
            x1: margin.left,
            x2: width - margin.right,
            y1: y,
            y2: y,
            stroke: "#e6e9ef",
            "stroke-width": 1,
          }}));
          const label = svgEl("text", {{
            x: margin.left - 12,
            y: y + 4,
            "text-anchor": "end",
            fill: "#667085",
            "font-size": 12,
          }});
          label.textContent = Math.round(value);
          svg.appendChild(label);
        }}

        const ticks = 5;
        for (let i = 0; i <= ticks; i++) {{
          const date = new Date(minDate.getTime() + ((maxDate - minDate) / ticks) * i);
          const x = xScale(date);
          const label = svgEl("text", {{
            x: x,
            y: height - 14,
            "text-anchor": "middle",
            fill: "#667085",
            "font-size": 12,
          }});
          label.textContent = fmtDate(date);
          svg.appendChild(label);
        }}

        svg.appendChild(svgEl("line", {{
          x1: margin.left,
          x2: width - margin.right,
          y1: yScale(100),
          y2: yScale(100),
          stroke: "#111827",
          "stroke-width": 1,
          "stroke-dasharray": "4 4",
          opacity: 0.45,
        }}));
      }}

      function drawLines() {{
        series.forEach(meta => {{
          const points = rows
            .filter(row => row.symbol === meta.symbol)
            .sort((a, b) => a.d - b.d);
          const d = points.map((point, index) => {{
            const command = index === 0 ? "M" : "L";
            return `${{command}} ${{xScale(point.d).toFixed(2)}} ${{yScale(point.value).toFixed(2)}}`;
          }}).join(" ");

          svg.appendChild(svgEl("path", {{
            d,
            fill: "none",
            stroke: meta.color,
            "stroke-width": meta.stroke,
            "stroke-linejoin": "round",
            "stroke-linecap": "round",
            opacity: meta.main ? 1 : 0.82,
          }}));

          const last = points[points.length - 1];
          const label = svgEl("text", {{
            x: width - margin.right + 10,
            y: yScale(last.value) + 4,
            fill: meta.color,
            "font-size": meta.main ? 13 : 12,
            "font-weight": meta.main ? 800 : 700,
          }});
          label.textContent = `${{meta.name}} ${{fmtPct(last.value - 100)}}`;
          svg.appendChild(label);
        }});
      }}

      function drawLegend() {{
        series.forEach(meta => {{
          const item = document.createElement("div");
          item.className = "legend-item";
          item.innerHTML = `<span style="background:${{meta.color}}"></span>${{meta.name}}`;
          legend.appendChild(item);
        }});
      }}

      function drawCards() {{
        const best = summary[0];
        winner.innerHTML = `
          <span>Mejor comportamiento</span>
          <strong>${{best.name}}</strong>
          <em>${{fmtPct(best.return)}}</em>
        `;

        summary.forEach(item => {{
          const card = document.createElement("div");
          card.className = "rank-card" + (item.main ? " main" : "");
          card.innerHTML = `
            <div class="rank-title">
              <span style="background:${{item.color}}"></span>
              <strong>${{item.name}}</strong>
              <em>${{fmtPct(item.return)}}</em>
            </div>
            <div class="rank-grid">
              <div><span>Base actual</span><b>${{fmtBase(item.actual)}}</b></div>
              <div><span>Maximo</span><b>${{fmtBase(item.max)}}</b></div>
              <div><span>Minimo</span><b>${{fmtBase(item.min)}}</b></div>
              <div><span>Volatilidad</span><b>${{fmtPct(item.volatility)}}</b></div>
            </div>
          `;
          cards.appendChild(card);
        }});
      }}

      function nearestDate(clientX) {{
        const box = svg.getBoundingClientRect();
        const x = ((clientX - box.left) / box.width) * width;
        const ratio = Math.max(0, Math.min(1, (x - margin.left) / innerW));
        const target = new Date(minDate.getTime() + ratio * (maxDate - minDate));
        return dates.reduce((best, current) => {{
          const deltaBest = Math.abs(parseDate(best) - target);
          const deltaCurrent = Math.abs(parseDate(current) - target);
          return deltaCurrent < deltaBest ? current : best;
        }}, dates[0]);
      }}

      function drawHover() {{
        const hoverLine = svgEl("line", {{
          y1: margin.top,
          y2: height - margin.bottom,
          stroke: "#111827",
          "stroke-width": 1,
          "stroke-dasharray": "3 3",
          opacity: 0,
        }});
        svg.appendChild(hoverLine);

        const dots = new Map();
        series.forEach(meta => {{
          const dot = svgEl("circle", {{
            r: meta.main ? 4.5 : 3.5,
            fill: meta.color,
            stroke: "#ffffff",
            "stroke-width": 1.5,
            opacity: 0,
          }});
          dots.set(meta.symbol, dot);
          svg.appendChild(dot);
        }});

        svg.addEventListener("mousemove", event => {{
          const dateKey = nearestDate(event.clientX);
          const dateRows = rows.filter(row => row.date === dateKey);
          const x = xScale(parseDate(dateKey));

          hoverLine.setAttribute("x1", x);
          hoverLine.setAttribute("x2", x);
          hoverLine.setAttribute("opacity", 1);

          dateRows.forEach(row => {{
            const dot = dots.get(row.symbol);
            if (!dot) return;
            dot.setAttribute("cx", x);
            dot.setAttribute("cy", yScale(row.value));
            dot.setAttribute("opacity", 1);
          }});

          const ordered = [...dateRows].sort((a, b) => b.value - a.value);
          tooltip.innerHTML = `
            <b>${{fmtDate(parseDate(dateKey))}}</b>
            ${{ordered.map(row => `
              <div>
                <span><i style="background:${{row.color}}"></i>${{row.name}}</span>
                <strong>${{fmtPct(row.value - 100)}}</strong>
              </div>
            `).join("")}}
          `;

          const box = svg.getBoundingClientRect();
          const localX = event.clientX - box.left;
          tooltip.style.left = Math.min(localX + 18, box.width - 245) + "px";
          tooltip.style.top = "42px";
          tooltip.classList.add("show");
        }});

        svg.addEventListener("mouseleave", () => {{
          hoverLine.setAttribute("opacity", 0);
          dots.forEach(dot => dot.setAttribute("opacity", 0));
          tooltip.classList.remove("show");
        }});
      }}

      drawGrid();
      drawLines();
      drawLegend();
      drawCards();
      drawHover();
    </script>

    <style>
      * {{
        box-sizing: border-box;
      }}

      body {{
        margin: 0;
        font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
        color: #172033;
      }}

      .market-wrap {{
        display: grid;
        grid-template-columns: minmax(0, 1.7fr) minmax(330px, 0.8fr);
        gap: 18px;
        padding: 2px;
      }}

      .chart-panel,
      .side-panel {{
        border: 1px solid #d9dee8;
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
      }}

      .chart-panel {{
        padding: 18px 18px 12px;
      }}

      .side-panel {{
        padding: 16px;
      }}

      .panel-head {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 14px;
        margin-bottom: 12px;
      }}

      .panel-head.compact {{
        margin-bottom: 14px;
      }}

      .eyebrow {{
        color: #667085;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0;
        text-transform: uppercase;
      }}

      h3 {{
        margin: 2px 0 0;
        font-size: 24px;
        line-height: 1.15;
      }}

      p {{
        margin: 7px 0 0;
        color: #667085;
        font-size: 13px;
      }}

      .badge {{
        border-radius: 6px;
        background: #111827;
        color: #ffffff;
        font-size: 12px;
        font-weight: 800;
        padding: 7px 10px;
        white-space: nowrap;
      }}

      .legend {{
        display: flex;
        flex-wrap: wrap;
        gap: 8px 14px;
        margin: 8px 0 12px;
      }}

      .legend-item {{
        display: inline-flex;
        align-items: center;
        gap: 7px;
        color: #475467;
        font-size: 12px;
        font-weight: 700;
      }}

      .legend-item span,
      .rank-title span {{
        width: 11px;
        height: 11px;
        border-radius: 999px;
        display: inline-block;
      }}

      .chart-box {{
        position: relative;
        height: 500px;
        border-top: 1px solid #edf0f5;
      }}

      svg {{
        display: block;
        width: 100%;
        height: 100%;
      }}

      .tooltip {{
        position: absolute;
        display: none;
        min-width: 225px;
        border: 1px solid #d0d5dd;
        border-radius: 8px;
        background: #ffffff;
        padding: 10px 12px;
        box-shadow: 0 16px 32px rgba(15, 23, 42, 0.18);
        pointer-events: none;
        z-index: 10;
      }}

      .tooltip.show {{
        display: block;
      }}

      .tooltip b {{
        display: block;
        margin-bottom: 7px;
        font-size: 14px;
      }}

      .tooltip div {{
        display: flex;
        justify-content: space-between;
        gap: 16px;
        padding: 3px 0;
        font-size: 12px;
      }}

      .tooltip span {{
        display: inline-flex;
        align-items: center;
        gap: 7px;
      }}

      .tooltip i {{
        width: 9px;
        height: 9px;
        border-radius: 999px;
        display: inline-block;
      }}

      .winner {{
        border-radius: 8px;
        background: #111827;
        color: #ffffff;
        padding: 14px;
        margin-bottom: 12px;
      }}

      .winner span {{
        display: block;
        color: #d0d5dd;
        font-size: 12px;
        font-weight: 700;
      }}

      .winner strong {{
        display: block;
        margin-top: 4px;
        font-size: 20px;
      }}

      .winner em {{
        display: block;
        margin-top: 2px;
        color: #9ee6b2;
        font-style: normal;
        font-weight: 800;
      }}

      .cards {{
        display: grid;
        gap: 9px;
        max-height: 570px;
        overflow: auto;
        padding-right: 2px;
      }}

      .rank-card {{
        border: 1px solid #e4e7ec;
        border-radius: 8px;
        background: #f8fafc;
        padding: 11px;
      }}

      .rank-card.main {{
        border-color: #111827;
        background: #ffffff;
      }}

      .rank-title {{
        display: grid;
        grid-template-columns: auto 1fr auto;
        align-items: center;
        gap: 8px;
        margin-bottom: 9px;
      }}

      .rank-title strong {{
        font-size: 14px;
      }}

      .rank-title em {{
        color: #172033;
        font-style: normal;
        font-weight: 800;
        font-size: 13px;
      }}

      .rank-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 7px;
      }}

      .rank-grid div {{
        border-top: 1px solid #e4e7ec;
        padding-top: 7px;
      }}

      .rank-grid span {{
        display: block;
        color: #667085;
        font-size: 11px;
        font-weight: 700;
      }}

      .rank-grid b {{
        font-size: 13px;
      }}

      @media (max-width: 900px) {{
        .market-wrap {{
          grid-template-columns: 1fr;
        }}

        .chart-box {{
          height: 430px;
        }}
      }}
    </style>
    """
