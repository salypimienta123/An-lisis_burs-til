import requests
import pandas as pd
import yfinance as yf
from datetime import datetime
from functools import lru_cache


def descargar_divisas():

    url = (
        "https://api.frankfurter.app/"
        "2004-01-01..2024-12-31"
        "?from=EUR&to=USD,GBP,CHF"
    )

    data = requests.get(url).json()

    df = pd.DataFrame.from_dict(
        data["rates"],
        orient="index"
    )

    df.index = pd.to_datetime(df.index)

    return df.sort_index()



import matplotlib.pyplot as plt


def grafico_divisas():

    df = descargar_divisas()

    df_yearly = df.resample("YE").mean()

    fig, ax = plt.subplots(figsize=(14, 8))

    ax.plot(df.index, df["USD"], alpha=0.4, label="USD")
    ax.plot(df.index, df["GBP"], alpha=0.4, label="GBP")
    ax.plot(df.index, df["CHF"], alpha=0.4, label="CHF")

    ax.plot(df_yearly.index, df_yearly["USD"], linewidth=2)
    ax.plot(df_yearly.index, df_yearly["GBP"], linewidth=2)
    ax.plot(df_yearly.index, df_yearly["CHF"], linewidth=2)

    ax.axvline(
        pd.to_datetime("2008-09-15"),
        linestyle="--",
        color="black"
    )

    ax.set_title("Tipos de cambio frente al EUR")

    return fig


# --------------------------------------------------
# ANALISIS BAYESIANO DE INVERSION
# --------------------------------------------------
# Este bloque no intenta predecir precios futuros. Convierte evidencias
# financieras observables en una probabilidad posterior de compra.
#
# Formula base:
# Odds posteriores = Odds previos x LR
# donde Odds = P(Compra) / (1 - P(Compra)).
#
# En LaTeX:
# P(H|E) = P(E|H)P(H) / P(E)
# Odds(H|E) = Odds(H) x LR(E)


PRIOR_COMPRA = 0.50

PALABRAS_POSITIVAS_NOTICIAS = [
    "beats expectations",
    "beat expectations",
    "raises guidance",
    "upgrade",
    "record revenue",
    "new product",
    "new contract",
    "margin expansion",
    "buyback",
    "share repurchase",
    "strong demand",
    "outperform",
    "surge",
    "rally",
    "profit rises",
    "earnings rise",
    "resultados mejores",
    "supera expectativas",
    "incremento de guidance",
    "nuevo producto",
    "nuevos contratos",
    "incremento de margenes",
    "recompras",
]

PALABRAS_NEGATIVAS_NOTICIAS = [
    "misses expectations",
    "missed expectations",
    "cuts guidance",
    "downgrade",
    "lawsuit",
    "regulatory probe",
    "investigation",
    "antitrust",
    "revenue decline",
    "falling revenue",
    "margin pressure",
    "market share loss",
    "layoffs",
    "warning",
    "plunge",
    "drops",
    "slumps",
    "caida de ingresos",
    "reduce guidance",
    "demanda",
    "investigacion regulatoria",
    "problemas regulatorios",
    "perdida de cuota",
]


def _valor_seguro(valor, defecto=0):
    if valor is None:
        return defecto
    try:
        return float(valor)
    except (TypeError, ValueError):
        return defecto


def _limitar(valor, minimo=0, maximo=100):
    return max(minimo, min(maximo, valor))


def _sumar_score(condicion, puntos):
    return puntos if condicion else 0


def _normalizar_fecha(fecha):
    if not fecha:
        return "N/D"

    try:
        if isinstance(fecha, (int, float)):
            return datetime.fromtimestamp(fecha).strftime("%Y-%m-%d")
        return pd.to_datetime(fecha).strftime("%Y-%m-%d")
    except Exception:
        return str(fecha)


@lru_cache(maxsize=128)
def _traducir_es(texto):
    if not texto or texto == "Sin titulo":
        return texto

    try:
        respuesta = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": texto[:450], "langpair": "en|es"},
            timeout=5,
        )
        respuesta.raise_for_status()
        traduccion = respuesta.json().get("responseData", {}).get("translatedText")
        return traduccion or texto
    except Exception:
        return texto


def _descargar_historial(ticker):
    accion = yf.Ticker(ticker)
    info = accion.info
    hist = accion.history(period="5y", auto_adjust=False)
    return accion, info, hist


def _score_value(info, hist):
    per = _valor_seguro(info.get("trailingPE"))
    forward_per = _valor_seguro(info.get("forwardPE"))
    precio = _valor_seguro(info.get("currentPrice") or info.get("regularMarketPrice"))

    minimo_52 = _valor_seguro(info.get("fiftyTwoWeekLow"))
    maximo_52 = _valor_seguro(info.get("fiftyTwoWeekHigh"))
    cerca_minimos = minimo_52 > 0 and precio <= minimo_52 * 1.25
    margen_seguridad = maximo_52 > 0 and precio <= maximo_52 * 0.80

    # Proxy conservador: yfinance no ofrece un PER sectorial homogeneo.
    per_sector_proxy = 22
    score = (
        _sumar_score(0 < per < per_sector_proxy, 30)
        + _sumar_score(0 < forward_per < per_sector_proxy, 25)
        + _sumar_score(cerca_minimos, 25)
        + _sumar_score(margen_seguridad, 20)
    )

    evidencias = [
        ("PER inferior al proxy sectorial", 0 < per < per_sector_proxy, 0.07),
        ("Forward PER atractivo", 0 < forward_per < per_sector_proxy, 0.06),
        ("Precio cercano a minimos de 52 semanas", cerca_minimos, 0.05),
        ("Margen de seguridad frente al maximo anual", margen_seguridad, 0.05),
    ]
    return _limitar(score), evidencias


def _score_dividend(info):
    dividend_yield = _valor_seguro(info.get("dividendYield"))
    payout = _valor_seguro(info.get("payoutRatio"))
    five_year_yield = _valor_seguro(info.get("fiveYearAvgDividendYield"))
    dividend_rate = _valor_seguro(info.get("dividendRate"))

    if dividend_yield < 1:
        dividend_yield *= 100
    if payout < 1:
        payout *= 100

    dividendo_sano = 2 <= dividend_yield <= 6
    payout_sostenible = 0 < payout <= 70
    historial = five_year_yield > 0
    dividendo_creciente = dividend_rate > 0 and dividend_yield > 0 and historial

    score = (
        _sumar_score(dividendo_sano, 30)
        + _sumar_score(payout_sostenible, 30)
        + _sumar_score(historial, 20)
        + _sumar_score(dividendo_creciente, 20)
    )

    evidencias = [
        ("Dividend Yield saludable", dividendo_sano, 0.05),
        ("Payout Ratio sostenible", payout_sostenible, 0.06),
        ("Historial de dividendos disponible", historial, 0.04),
        ("Dividendo activo y recurrente", dividendo_creciente, 0.04),
    ]
    return _limitar(score), evidencias


def _score_growth(info):
    eps_growth = _valor_seguro(info.get("earningsGrowth"))
    revenue_growth = _valor_seguro(info.get("revenueGrowth"))
    quarterly_growth = _valor_seguro(info.get("earningsQuarterlyGrowth"))
    forward_eps = _valor_seguro(info.get("forwardEps"))
    trailing_eps = _valor_seguro(info.get("trailingEps"))

    crecimiento_eps = eps_growth > 0.08
    crecimiento_ingresos = revenue_growth > 0.08
    expansion = quarterly_growth > 0.05
    forward_growth = forward_eps > trailing_eps > 0

    score = (
        _sumar_score(crecimiento_eps, 30)
        + _sumar_score(crecimiento_ingresos, 30)
        + _sumar_score(expansion, 20)
        + _sumar_score(forward_growth, 20)
    )

    evidencias = [
        ("Crecimiento EPS positivo", crecimiento_eps, 0.07),
        ("Crecimiento de ingresos positivo", crecimiento_ingresos, 0.07),
        ("Expansion reciente del negocio", expansion, 0.05),
        ("Forward EPS superior al EPS actual", forward_growth, 0.05),
    ]
    return _limitar(score), evidencias


def _score_momentum(hist):
    if hist.empty or "Close" not in hist:
        return 0, [("Sin historial suficiente para momentum", False, 0.06)]

    cierre = hist["Close"].dropna()
    if len(cierre) < 220:
        return 0, [("Historial insuficiente para medias moviles", False, 0.06)]

    precio = float(cierre.iloc[-1])
    mm50 = float(cierre.tail(50).mean())
    mm200 = float(cierre.tail(200).mean())
    maximo_52 = float(cierre.tail(252).max())
    precio_12m = float(cierre.iloc[-252]) if len(cierre) >= 252 else float(cierre.iloc[0])

    mm_alcista = mm50 > mm200
    tendencia = precio > mm50
    cerca_maximos = maximo_52 > 0 and precio >= maximo_52 * 0.90
    rentabilidad_12m = precio_12m > 0 and ((precio / precio_12m) - 1) > 0

    score = (
        _sumar_score(mm_alcista, 30)
        + _sumar_score(tendencia, 25)
        + _sumar_score(cerca_maximos, 20)
        + _sumar_score(rentabilidad_12m, 25)
    )

    evidencias = [
        ("MM50 superior a MM200", mm_alcista, 0.07),
        ("Precio por encima de la MM50", tendencia, 0.05),
        ("Precio cercano a maximos anuales", cerca_maximos, 0.04),
        ("Rentabilidad 12 meses positiva", rentabilidad_12m, 0.06),
    ]
    return _limitar(score), evidencias


def _score_quality(info, hist):
    roe = _valor_seguro(info.get("returnOnEquity"))
    deuda = _valor_seguro(info.get("debtToEquity"))
    margen_operativo = _valor_seguro(info.get("operatingMargins"))
    margen_neto = _valor_seguro(info.get("profitMargins"))

    if roe > 1:
        roe /= 100
    if margen_operativo > 1:
        margen_operativo /= 100
    if margen_neto > 1:
        margen_neto /= 100

    rentable_consistente = False
    if not hist.empty and "Close" in hist:
        rent_anual = hist["Close"].dropna().resample("YE").last().pct_change().dropna()
        rentable_consistente = len(rent_anual) >= 3 and (rent_anual > 0).mean() >= 0.60

    roe_elevado = roe > 0.15
    deuda_baja = deuda == 0 or deuda < 120
    margen_op_sano = margen_operativo > 0.12
    margen_neto_sano = margen_neto > 0.10

    score = (
        _sumar_score(roe_elevado, 25)
        + _sumar_score(deuda_baja, 20)
        + _sumar_score(margen_op_sano, 20)
        + _sumar_score(margen_neto_sano, 20)
        + _sumar_score(rentable_consistente, 15)
    )

    evidencias = [
        ("ROE superior al 15%", roe_elevado, 0.08),
        ("Deuda controlada", deuda_baja, 0.05),
        ("Margen operativo solido", margen_op_sano, 0.05),
        ("Margen neto solido", margen_neto_sano, 0.05),
        ("Rentabilidad anual consistente", rentable_consistente, 0.04),
    ]
    return _limitar(score), evidencias


def _clasificacion(probabilidad):
    if probabilidad < 30:
        return "🔴 Venta"
    if probabilidad < 50:
        return "🟠 Evitar"
    if probabilidad < 65:
        return "🟡 Neutral"
    if probabilidad < 80:
        return "🟢 Compra"
    return "🟢 Compra Fuerte"


def _actualizar_probabilidad(prior, evidencias):
    posterior = prior
    detalle = []

    for nombre, positiva, peso in evidencias:
        anterior = posterior
        # Likelihood ratio simplificado: una evidencia positiva multiplica
        # las odds por (1 + peso); una negativa por (1 - peso).
        lr = 1 + peso if positiva else max(0.1, 1 - peso)
        odds = posterior / (1 - posterior)
        odds_actualizadas = odds * lr
        posterior = odds_actualizadas / (1 + odds_actualizadas)

        detalle.append(
            {
                "evidencia": nombre,
                "resultado": "Positiva" if positiva else "Negativa",
                "cambio": (posterior - anterior) * 100,
                "posterior": posterior * 100,
            }
        )

    return posterior, detalle


def _extraer_noticia(noticia):
    contenido = noticia.get("content", noticia)
    proveedor = contenido.get("provider") or noticia.get("publisher") or {}
    enlace = (
        (contenido.get("canonicalUrl") or {}).get("url")
        or (contenido.get("clickThroughUrl") or {}).get("url")
        or noticia.get("link")
        or noticia.get("url")
        or ""
    )

    if isinstance(proveedor, dict):
        fuente = proveedor.get("displayName") or proveedor.get("name") or "N/D"
    else:
        fuente = str(proveedor)

    titulo = contenido.get("title") or noticia.get("title") or "Sin titulo"

    return {
        "titulo": titulo,
        "titulo_es": _traducir_es(titulo),
        "fecha": _normalizar_fecha(
            contenido.get("pubDate")
            or contenido.get("displayTime")
            or noticia.get("providerPublishTime")
        ),
        "fuente": fuente,
        "url": enlace,
        "texto": " ".join(
            [
                str(titulo),
                str(contenido.get("summary") or ""),
                str(contenido.get("description") or ""),
            ]
        ).lower(),
    }


def _clasificar_sentimiento(texto):
    positivos = sum(1 for palabra in PALABRAS_POSITIVAS_NOTICIAS if palabra in texto)
    negativos = sum(1 for palabra in PALABRAS_NEGATIVAS_NOTICIAS if palabra in texto)

    if positivos > negativos:
        return "Positivo", 1
    if negativos > positivos:
        return "Negativo", -1
    return "Neutral", 0


def analizar_noticias(ticker):
    accion = yf.Ticker(ticker)
    noticias_raw = accion.news or []
    noticias = []

    for noticia_raw in noticias_raw[:10]:
        noticia = _extraer_noticia(noticia_raw)
        sentimiento, valor = _clasificar_sentimiento(noticia["texto"])

        noticias.append(
            {
                "titulo": noticia["titulo"],
                "titulo_es": noticia["titulo_es"],
                "fecha": noticia["fecha"],
                "fuente": noticia["fuente"],
                "url": noticia["url"],
                "sentimiento": sentimiento,
                "valor": valor,
            }
        )

    if not noticias:
        return {
            "noticias": [],
            "score": 0,
            "positivas": 0,
            "negativas": 0,
            "neutrales": 0,
            "peso_bayesiano": 0,
        }

    positivas = sum(1 for noticia in noticias if noticia["valor"] > 0)
    negativas = sum(1 for noticia in noticias if noticia["valor"] < 0)
    neutrales = sum(1 for noticia in noticias if noticia["valor"] == 0)

    # Score agregado entre -100 y +100. Las noticias son evidencia blanda:
    # su LR maximo queda acotado al 10% para que nunca dominen el modelo.
    score = ((positivas - negativas) / len(noticias)) * 100
    peso_bayesiano = min(abs(score) / 100 * 0.10, 0.10)

    return {
        "noticias": noticias,
        "score": score,
        "positivas": positivas,
        "negativas": negativas,
        "neutrales": neutrales,
        "peso_bayesiano": peso_bayesiano,
    }


def _comparar_indices(ticker, hist):
    indices = {
        "S&P500": "^GSPC",
        "MSCI World": "URTH",
        "Nasdaq": "^IXIC",
    }

    if hist.empty or "Close" not in hist:
        return []

    cierre_accion = hist["Close"].dropna()
    if cierre_accion.empty:
        return []

    inicio = cierre_accion.index[0]
    fin = cierre_accion.index[-1]
    rent_accion = ((cierre_accion.iloc[-1] / cierre_accion.iloc[0]) - 1) * 100
    comparacion = []

    for nombre, ticker_indice in indices.items():
        try:
            datos_indice = yf.download(
                ticker_indice,
                start=inicio,
                end=fin,
                progress=False,
                auto_adjust=False,
                threads=False,
            )
            cierre_indice = datos_indice["Close"].dropna()
            if isinstance(cierre_indice, pd.DataFrame):
                cierre_indice = cierre_indice.iloc[:, 0]
            if cierre_indice.empty:
                continue

            rent_indice = ((cierre_indice.iloc[-1] / cierre_indice.iloc[0]) - 1) * 100
            comparacion.append(
                {
                    "indice": nombre,
                    "rentabilidad_accion": float(rent_accion),
                    "rentabilidad_indice": float(rent_indice),
                    "bate_indice": bool(rent_accion > rent_indice),
                }
            )
        except Exception:
            continue

    return comparacion


def _filosofia_dominante(scores):
    max_score = max(scores.values())
    dominantes = [nombre for nombre, score in scores.items() if score == max_score]
    return " + ".join(dominantes), max_score


def analisis_bayesiano(ticker):
    accion, info, hist = _descargar_historial(ticker)

    score_value, ev_value = _score_value(info, hist)
    score_dividend, ev_dividend = _score_dividend(info)
    score_growth, ev_growth = _score_growth(info)
    score_momentum, ev_momentum = _score_momentum(hist)
    score_quality, ev_quality = _score_quality(info, hist)

    scores = {
        "Value Investing": score_value,
        "Dividend Investing": score_dividend,
        "Growth Investing": score_growth,
        "Momentum Investing": score_momentum,
        "Quality Investing": score_quality,
    }

    noticias = analizar_noticias(ticker)
    evidencia_noticias = []
    if noticias["peso_bayesiano"] > 0:
        evidencia_noticias.append(
            (
                "Noticias recientes",
                noticias["score"] > 0,
                noticias["peso_bayesiano"],
            )
        )

    evidencias = (
        ev_value
        + ev_dividend
        + ev_growth
        + ev_momentum
        + ev_quality
        + evidencia_noticias
    )
    posterior, detalle_evidencias = _actualizar_probabilidad(PRIOR_COMPRA, evidencias)
    probabilidad = posterior * 100
    filosofia, filosofia_score = _filosofia_dominante(scores)
    impacto_noticias = sum(
        evidencia["cambio"]
        for evidencia in detalle_evidencias
        if evidencia["evidencia"] == "Noticias recientes"
    )

    return {
        "ticker": ticker.upper(),
        "nombre": info.get("longName") or info.get("shortName") or ticker.upper(),
        "prior": PRIOR_COMPRA * 100,
        "evidencias": detalle_evidencias,
        "posterior": probabilidad,
        "clasificacion": _clasificacion(probabilidad),
        "scores": scores,
        "filosofia_dominante": filosofia,
        "filosofia_score": filosofia_score,
        "comparacion_indices": _comparar_indices(ticker, hist),
        "noticias": noticias,
        "impacto_noticias": impacto_noticias,
    }
