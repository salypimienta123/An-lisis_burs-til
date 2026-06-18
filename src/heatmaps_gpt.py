import html
import json
import math

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf


@st.cache_data(ttl=3600, show_spinner=False)
def _datos_heatmap_interactivo(ticker: str) -> tuple[pd.DataFrame, dict]:
    ticker = ticker.upper().strip()
    accion = yf.Ticker(ticker)

    precios = accion.history(period="15y", auto_adjust=False)
    if precios.empty or "Close" not in precios.columns:
        return pd.DataFrame(), {}

    cierre_anual = precios["Close"].resample("YE").last()
    rentabilidad = cierre_anual.pct_change() * 100

    resultado = pd.DataFrame(
        {
            "Year": cierre_anual.index.year,
            "Precio": cierre_anual.values,
            "Rentabilidad": rentabilidad.values,
        }
    ).dropna()

    financials = accion.financials
    balance = accion.balance_sheet

    fundamentales = []
    for _, fila in resultado.iterrows():
        year = int(fila["Year"])
        datos_year = _fundamentales_por_year(financials, balance, year)

        eps = datos_year.get("EPS")
        precio = fila["Precio"]
        per = precio / eps if eps and eps > 0 else np.nan

        fundamentales.append(
            {
                "PER": per,
                "EPS": eps,
                "Ingresos": datos_year.get("Ingresos"),
                "Beneficio neto": datos_year.get("Beneficio neto"),
                "Margen neto": datos_year.get("Margen neto"),
                "Deuda total": datos_year.get("Deuda total"),
                "Caja": datos_year.get("Caja"),
                "Patrimonio": datos_year.get("Patrimonio"),
            }
        )

    resultado = pd.concat(
        [resultado.reset_index(drop=True), pd.DataFrame(fundamentales)],
        axis=1,
    )

    try:
        info = accion.info
    except Exception:
        info = {}

    return resultado, info


def _fundamentales_por_year(financials: pd.DataFrame, balance: pd.DataFrame, year: int) -> dict:
    columna_fin = _columna_mas_cercana(financials, year)
    columna_balance = _columna_mas_cercana(balance, year)

    ingresos = _valor(financials, columna_fin, ["Total Revenue", "Operating Revenue"])
    beneficio = _valor(financials, columna_fin, ["Net Income", "Net Income Common Stockholders"])
    eps = _valor(financials, columna_fin, ["Diluted EPS", "Basic EPS"])
    deuda = _valor(balance, columna_balance, ["Total Debt"])
    caja = _valor(
        balance,
        columna_balance,
        ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"],
    )
    patrimonio = _valor(
        balance,
        columna_balance,
        ["Stockholders Equity", "Total Equity Gross Minority Interest"],
    )

    margen_neto = (beneficio / ingresos) * 100 if ingresos else np.nan

    return {
        "Ingresos": ingresos,
        "Beneficio neto": beneficio,
        "EPS": eps,
        "Margen neto": margen_neto,
        "Deuda total": deuda,
        "Caja": caja,
        "Patrimonio": patrimonio,
    }


def _columna_mas_cercana(df: pd.DataFrame, year: int):
    if df is None or df.empty:
        return None

    columnas = [col for col in df.columns if hasattr(col, "year")]
    if not columnas:
        return None

    mismas = [col for col in columnas if col.year == year]
    if mismas:
        return mismas[0]

    return min(columnas, key=lambda col: abs(col.year - year))


def _valor(df: pd.DataFrame, columna, filas: list[str]):
    if df is None or df.empty or columna is None:
        return np.nan

    for fila in filas:
        if fila in df.index:
            valor = df.loc[fila, columna]
            if pd.notna(valor):
                return float(valor)

    return np.nan


def heatmap_interactivo_empresa(ticker: str) -> None:
    ticker = ticker.upper().strip()

    with st.spinner("Descargando precios y fundamentales..."):
        datos, info = _datos_heatmap_interactivo(ticker)

    if datos.empty:
        st.warning("No se han encontrado datos suficientes para este ticker.")
        return

    empresa = info.get("longName", ticker)
    sector = info.get("sector", "N/A")
    industria = info.get("industry", "N/A")

    st.markdown(f"### {empresa}")
    st.caption(f"{sector} | {industria}")

    registros = _registros_para_componente(datos)
    componente = _crear_html_heatmap(registros, empresa, ticker)
    altura = _altura_componente(len(registros))

    components.html(componente, height=altura, scrolling=False)

    with st.expander("Ver tabla anual completa"):
        columnas = [
            "Year",
            "Precio",
            "Rentabilidad",
            "PER",
            "EPS",
            "Ingresos",
            "Beneficio neto",
            "Margen neto",
            "Deuda total",
            "Caja",
            "Patrimonio",
        ]
        st.dataframe(datos[columnas], use_container_width=True, hide_index=True)


def _registros_para_componente(datos: pd.DataFrame) -> list[dict]:
    valores = datos["Rentabilidad"].dropna()
    max_abs = max(abs(valores.min()), abs(valores.max()), 1)

    registros = []
    for _, fila in datos.iterrows():
        rentabilidad = float(fila["Rentabilidad"])
        registros.append(
            {
                "year": int(fila["Year"]),
                "price": _numero_o_none(fila["Precio"]),
                "return": _numero_o_none(fila["Rentabilidad"]),
                "per": _numero_o_none(fila["PER"]),
                "eps": _numero_o_none(fila["EPS"]),
                "revenue": _numero_o_none(fila["Ingresos"]),
                "net_income": _numero_o_none(fila["Beneficio neto"]),
                "net_margin": _numero_o_none(fila["Margen neto"]),
                "debt": _numero_o_none(fila["Deuda total"]),
                "cash": _numero_o_none(fila["Caja"]),
                "equity": _numero_o_none(fila["Patrimonio"]),
                "color": _color_rentabilidad(rentabilidad, max_abs),
            }
        )

    return registros


def _crear_html_heatmap(registros: list[dict], empresa: str, ticker: str) -> str:
    n = max(1, math.ceil(math.sqrt(len(registros))))
    data_json = json.dumps(registros, ensure_ascii=False)
    empresa_segura = html.escape(empresa)
    ticker_seguro = html.escape(ticker)

    return f"""
    <div class="gpt-wrap">
      <section class="heatmap-panel">
        <div class="panel-head">
          <div>
            <div class="eyebrow">{ticker_seguro}</div>
            <h3>Rentabilidades anuales</h3>
          </div>
          <div class="legend">
            <span class="legend-loss">Negativo</span>
            <span class="legend-mid"></span>
            <span class="legend-gain">Positivo</span>
          </div>
        </div>
        <div id="heatmapGrid" class="heatmap-grid" style="grid-template-columns: repeat({n}, minmax(82px, 1fr));"></div>
      </section>

      <aside class="detail-panel">
        <div class="panel-head">
          <div>
            <div class="eyebrow">Consulta anual</div>
            <h3 id="detailTitle">{empresa_segura}</h3>
          </div>
        </div>

        <div class="year-chip" id="selectedYear"></div>

        <div class="metric-row">
          <div class="metric-card">
            <span>Precio cierre</span>
            <strong id="priceValue"></strong>
          </div>
          <div class="metric-card">
            <span>Rentabilidad</span>
            <strong id="returnValue"></strong>
          </div>
        </div>

        <div class="metric-row compact">
          <div class="metric-card">
            <span>PER</span>
            <strong id="perValue"></strong>
          </div>
          <div class="metric-card">
            <span>EPS</span>
            <strong id="epsValue"></strong>
          </div>
        </div>

        <div class="detail-list">
          <div><span>Ingresos</span><strong id="revenueValue"></strong></div>
          <div><span>Beneficio neto</span><strong id="netIncomeValue"></strong></div>
          <div><span>Margen neto</span><strong id="marginValue"></strong></div>
          <div><span>Deuda total</span><strong id="debtValue"></strong></div>
          <div><span>Caja</span><strong id="cashValue"></strong></div>
           <div><span>Patrimonio</span><strong id="equityValue"></strong></div>
        </div>
      </aside>

      <div id="tooltip" class="tooltip"></div>
    </div>

    <script>
      const rows = {data_json};
      const grid = document.getElementById("heatmapGrid");
      const tooltip = document.getElementById("tooltip");
      let selectedYear = rows[rows.length - 1].year;

      function money(value) {{
        if (value === null || Number.isNaN(value)) return "N/A";
        return "$" + value.toLocaleString("en-US", {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
      }}

      function bigMoney(value) {{
        if (value === null || Number.isNaN(value)) return "N/A";
        const absValue = Math.abs(value);
        if (absValue >= 1_000_000_000) return "$" + (value / 1_000_000_000).toLocaleString("en-US", {{ maximumFractionDigits: 2 }}) + "B";
        if (absValue >= 1_000_000) return "$" + (value / 1_000_000).toLocaleString("en-US", {{ maximumFractionDigits: 2 }}) + "M";
        return "$" + value.toLocaleString("en-US", {{ maximumFractionDigits: 0 }});
      }}

      function percent(value) {{
        if (value === null || Number.isNaN(value)) return "N/A";
        const sign = value > 0 ? "+" : "";
        return sign + value.toFixed(2) + "%";
      }}

      function number(value) {{
        if (value === null || Number.isNaN(value)) return "N/A";
        return value.toLocaleString("en-US", {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
      }}

      function setText(id, value) {{
        document.getElementById(id).textContent = value;
      }}

      function selectRow(row) {{
        selectedYear = row.year;
        document.querySelectorAll(".heat-cell").forEach(cell => {{
          cell.classList.toggle("selected", Number(cell.dataset.year) === selectedYear);
        }});

        setText("selectedYear", row.year);
        setText("priceValue", money(row.price));
        setText("returnValue", percent(row.return));
        setText("perValue", number(row.per));
        setText("epsValue", money(row.eps));
        setText("revenueValue", bigMoney(row.revenue));
        setText("netIncomeValue", bigMoney(row.net_income));
        setText("marginValue", percent(row.net_margin));
        setText("debtValue", bigMoney(row.debt));
        setText("cashValue", bigMoney(row.cash));
        setText("equityValue", bigMoney(row.equity));
      }}

      function tooltipHtml(row) {{
        return `
          <b>${{row.year}}</b>
          <span>Precio cierre: <strong>${{money(row.price)}}</strong></span>
          <span>Rentabilidad: <strong>${{percent(row.return)}}</strong></span>
          <span>PER: <strong>${{number(row.per)}}</strong></span>
          <span>EPS: <strong>${{money(row.eps)}}</strong></span>
          <span>Margen neto: <strong>${{percent(row.net_margin)}}</strong></span>
        `;
      }}

      rows.forEach(row => {{
        const cell = document.createElement("button");
        cell.type = "button";
        cell.className = "heat-cell";
        cell.dataset.year = row.year;
        cell.style.background = row.color;
        cell.innerHTML = `
          <span class="cell-year">${{row.year}}</span>
          <span class="cell-price">${{money(row.price).replace(".00", "")}}</span>
          <span class="cell-return">${{percent(row.return).replace(".00", "")}}</span>
        `;

        cell.addEventListener("click", () => selectRow(row));
        cell.addEventListener("mouseenter", () => {{
          tooltip.innerHTML = tooltipHtml(row);
          tooltip.classList.add("show");
        }});
        cell.addEventListener("mousemove", event => {{
          const wrapBox = document.querySelector(".gpt-wrap").getBoundingClientRect();
          tooltip.style.left = (event.clientX - wrapBox.left + 14) + "px";
          tooltip.style.top = (event.clientY - wrapBox.top + 14) + "px";
        }});
        cell.addEventListener("mouseleave", () => tooltip.classList.remove("show"));

        grid.appendChild(cell);
      }});

      selectRow(rows[rows.length - 1]);
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

      .gpt-wrap {{
        position: relative;
        display: grid;
        grid-template-columns: minmax(0, 1.25fr) minmax(310px, 0.75fr);
        gap: 18px;
        padding: 2px;
      }}

      .heatmap-panel,
      .detail-panel {{
        border: 1px solid #d9dee8;
        border-radius: 8px;
        background: #ffffff;
        padding: 16px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
      }}

      .panel-head {{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 14px;
      }}

      .eyebrow {{
        color: #667085;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0;
        text-transform: uppercase;
      }}

      h3 {{
        margin: 2px 0 0;
        font-size: 20px;
        line-height: 1.2;
      }}

      .legend {{
        display: grid;
        grid-template-columns: auto 70px auto;
        align-items: center;
        gap: 8px;
        color: #667085;
        font-size: 12px;
        white-space: nowrap;
      }}

      .legend-mid {{
        height: 10px;
        border-radius: 999px;
        background: linear-gradient(90deg, #c94a44, #f5d47a, #3f8f54);
      }}

      .legend-loss {{
        color: #9f2f2f;
      }}

      .legend-gain {{
        color: #2f7a43;
      }}

      .heatmap-grid {{
        display: grid;
        gap: 9px;
      }}

      .heat-cell {{
        min-height: 88px;
        border: 2px solid #111827;
        border-radius: 6px;
        color: #111827;
        cursor: pointer;
        display: grid;
        place-items: center;
        padding: 9px 6px;
        transition: transform 140ms ease, box-shadow 140ms ease, outline-color 140ms ease;
        font: inherit;
        text-align: center;
      }}

      .heat-cell:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 22px rgba(15, 23, 42, 0.16);
      }}

      .heat-cell.selected {{
        outline: 4px solid #2563eb;
        outline-offset: 2px;
      }}

      .cell-year,
      .cell-price,
      .cell-return {{
        display: block;
        line-height: 1.15;
        text-shadow: 0 1px 0 rgba(255, 255, 255, 0.45);
      }}

      .cell-year {{
        font-size: 16px;
        font-weight: 800;
      }}

      .cell-price {{
        font-size: 14px;
        font-weight: 700;
      }}

      .cell-return {{
        font-size: 15px;
        font-weight: 800;
      }}

      .year-chip {{
        width: fit-content;
        min-width: 76px;
        border-radius: 6px;
        background: #111827;
        color: #ffffff;
        padding: 6px 12px;
        font-weight: 800;
        margin: 2px 0 14px;
        text-align: center;
      }}

      .metric-row {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
        margin-bottom: 10px;
      }}

      .metric-card {{
        border: 1px solid #e4e7ec;
        border-radius: 8px;
        background: #f8fafc;
        padding: 12px;
      }}

      .metric-card span,
      .detail-list span {{
        display: block;
        color: #667085;
        font-size: 12px;
        font-weight: 700;
      }}

      .metric-card strong {{
        display: block;
        margin-top: 5px;
        font-size: 20px;
        line-height: 1.15;
      }}

      .metric-row.compact .metric-card strong {{
        font-size: 18px;
      }}

      .detail-list {{
        margin-top: 12px;
        border-top: 1px solid #e4e7ec;
      }}

      .detail-list div {{
        display: flex;
        justify-content: space-between;
        gap: 16px;
        padding: 12px 0;
        border-bottom: 1px solid #edf0f5;
      }}

      .detail-list strong {{
        font-size: 14px;
        text-align: right;
      }}

      .tooltip {{
        position: absolute;
        z-index: 20;
        min-width: 220px;
        display: none;
        flex-direction: column;
        gap: 5px;
        border: 1px solid #d0d5dd;
        border-radius: 8px;
        background: #ffffff;
        color: #172033;
        padding: 10px 12px;
        box-shadow: 0 16px 32px rgba(15, 23, 42, 0.18);
        pointer-events: none;
        font-size: 13px;
      }}

      .tooltip.show {{
        display: flex;
      }}

      .tooltip b {{
        font-size: 15px;
      }}

      .tooltip span {{
        display: flex;
        justify-content: space-between;
        gap: 14px;
      }}

      @media (max-width: 820px) {{
        .gpt-wrap {{
          grid-template-columns: 1fr;
        }}

        .legend {{
          display: none;
        }}

        .heatmap-grid {{
          grid-template-columns: repeat(2, minmax(120px, 1fr)) !important;
        }}
      }}
    </style>
    """


def _altura_componente(num_registros: int) -> int:
    n = max(1, math.ceil(math.sqrt(num_registros)))
    filas = math.ceil(num_registros / n)
    return max(620, 170 + filas * 102)


def _color_rentabilidad(valor: float, max_abs: float) -> str:
    normalizado = max(-1, min(1, valor / max_abs))

    if normalizado < 0:
        t = normalizado + 1
        return _mezclar_rgb((194, 65, 65), (245, 211, 122), t)

    return _mezclar_rgb((245, 211, 122), (58, 133, 78), normalizado)


def _mezclar_rgb(inicio: tuple[int, int, int], fin: tuple[int, int, int], t: float) -> str:
    r = round(inicio[0] + (fin[0] - inicio[0]) * t)
    g = round(inicio[1] + (fin[1] - inicio[1]) * t)
    b = round(inicio[2] + (fin[2] - inicio[2]) * t)
    return f"rgb({r}, {g}, {b})"


def _numero_o_none(valor):
    if pd.isna(valor):
        return None
    return float(valor)
