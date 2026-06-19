import math
import json
from functools import lru_cache
from urllib.request import urlopen

import pandas as pd
import yfinance as yf


GEOJSON_MUNDIAL_URL = (
    "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"
)


INDICES_MUNDIALES = [
    {
        "nombre": "S&P 500",
        "ticker": "^GSPC",
        "pais": "Estados Unidos",
        "iso3": "USA",
        "latitud": 40.7128,
        "longitud": -74.0060,
        "pib_per_capita": 82769,
    },
    {
        "nombre": "Nasdaq Composite",
        "ticker": "^IXIC",
        "pais": "Estados Unidos",
        "iso3": "USA",
        "latitud": 40.7580,
        "longitud": -73.9855,
        "pib_per_capita": 82769,
    },
    {
        "nombre": "Dow Jones",
        "ticker": "^DJI",
        "pais": "Estados Unidos",
        "iso3": "USA",
        "latitud": 40.7069,
        "longitud": -74.0113,
        "pib_per_capita": 82769,
    },
    {
        "nombre": "DAX",
        "ticker": "^GDAXI",
        "pais": "Alemania",
        "iso3": "DEU",
        "latitud": 50.1109,
        "longitud": 8.6821,
        "pib_per_capita": 52746,
    },
    {
        "nombre": "CAC 40",
        "ticker": "^FCHI",
        "pais": "Francia",
        "iso3": "FRA",
        "geojson_nombre": "France",
        "latitud": 48.8566,
        "longitud": 2.3522,
        "pib_per_capita": 44461,
    },
    {
        "nombre": "IBEX 35",
        "ticker": "^IBEX",
        "pais": "Espana",
        "iso3": "ESP",
        "latitud": 40.4168,
        "longitud": -3.7038,
        "pib_per_capita": 32677,
    },
    {
        "nombre": "FTSE 100",
        "ticker": "^FTSE",
        "pais": "Reino Unido",
        "iso3": "GBR",
        "latitud": 51.5074,
        "longitud": -0.1278,
        "pib_per_capita": 48867,
    },
    {
        "nombre": "Nikkei 225",
        "ticker": "^N225",
        "pais": "Japon",
        "iso3": "JPN",
        "latitud": 35.6762,
        "longitud": 139.6503,
        "pib_per_capita": 33834,
    },
    {
        "nombre": "Hang Seng",
        "ticker": "^HSI",
        "pais": "Hong Kong",
        "iso3": "HKG",
        "latitud": 22.3193,
        "longitud": 114.1694,
        "pib_per_capita": 50248,
    },
    {
        "nombre": "Shanghai Composite",
        "ticker": "000001.SS",
        "pais": "China",
        "iso3": "CHN",
        "latitud": 31.2304,
        "longitud": 121.4737,
        "pib_per_capita": 12614,
    },
    {
        "nombre": "Nifty 50",
        "ticker": "^NSEI",
        "pais": "India",
        "iso3": "IND",
        "latitud": 19.0760,
        "longitud": 72.8777,
        "pib_per_capita": 2485,
    },
    {
        "nombre": "Bovespa",
        "ticker": "^BVSP",
        "pais": "Brasil",
        "iso3": "BRA",
        "latitud": -23.5505,
        "longitud": -46.6333,
        "pib_per_capita": 10044,
    },
]


PERIODOS_YFINANCE = {
    "Día": {"period": "5d", "interval": "1d", "filas": 2},
    "Dia": {"period": "5d", "interval": "1d", "filas": 2},
    "Mes": {"period": "1mo", "interval": "1d", "filas": None},
    "Año": {"period": "1y", "interval": "1d", "filas": None},
    "Ano": {"period": "1y", "interval": "1d", "filas": None},
    "5 años": {"period": "5y", "interval": "1wk", "filas": None},
    "5 anos": {"period": "5y", "interval": "1wk", "filas": None},
}


@lru_cache(maxsize=1)
def _cargar_geojson_paises():
    with urlopen(GEOJSON_MUNDIAL_URL, timeout=20) as respuesta:
        return json.loads(respuesta.read().decode("utf-8"))


def _serie_cierre(datos):
    if datos.empty:
        return pd.Series(dtype=float)

    if isinstance(datos.columns, pd.MultiIndex):
        if "Close" in datos.columns.get_level_values(0):
            cierre = datos["Close"]
            if isinstance(cierre, pd.DataFrame):
                cierre = cierre.iloc[:, 0]
        else:
            cierre = datos.xs("Close", axis=1, level=-1).iloc[:, 0]
    else:
        cierre = datos["Close"] if "Close" in datos.columns else pd.Series(dtype=float)

    return pd.to_numeric(cierre, errors="coerce").dropna()


def _descargar_cierres(ticker, periodo):
    config = PERIODOS_YFINANCE.get(periodo, PERIODOS_YFINANCE["Mes"])

    datos = yf.download(
        ticker,
        period=config["period"],
        interval=config["interval"],
        progress=False,
        auto_adjust=False,
        threads=False,
    )

    cierres = _serie_cierre(datos)
    filas = config.get("filas")
    if filas:
        cierres = cierres.tail(filas)

    return cierres


def _calcular_metricas(indice, periodo):
    cierres = _descargar_cierres(indice["ticker"], periodo)

    if cierres.empty:
        raise ValueError("Sin datos disponibles")

    precio_actual = float(cierres.iloc[-1])
    maximo = float(cierres.max())
    minimo = float(cierres.min())

    precio_inicial = float(cierres.iloc[0])
    if precio_inicial == 0:
        rentabilidad = 0.0
    else:
        rentabilidad = ((precio_actual / precio_inicial) - 1) * 100

    if len(cierres) >= 2 and float(cierres.iloc[-2]) != 0:
        variacion = ((precio_actual / float(cierres.iloc[-2])) - 1) * 100
    else:
        variacion = rentabilidad

    return {
        "precio_actual": precio_actual,
        "variacion": variacion,
        "maximo": maximo,
        "minimo": minimo,
        "rentabilidad": rentabilidad,
    }


def _formato_numero(valor, decimales=2):
    if valor is None or not math.isfinite(valor):
        return "N/D"
    return f"{valor:,.{decimales}f}"


def _tooltip(indice, metricas=None, error=None):
    pib = indice.get("pib_per_capita")
    pib_texto = f"${pib:,.0f}" if pib else "N/D"

    if error:
        cuerpo = f"<tr><td colspan='2'>Datos no disponibles: {error}</td></tr>"
    else:
        cuerpo = f"""
        <tr><td>Precio actual</td><td>{_formato_numero(metricas["precio_actual"])}</td></tr>
        <tr><td>Variacion %</td><td>{_formato_numero(metricas["variacion"])}%</td></tr>
        <tr><td>Maximo</td><td>{_formato_numero(metricas["maximo"])}</td></tr>
        <tr><td>Minimo</td><td>{_formato_numero(metricas["minimo"])}</td></tr>
        <tr><td>Rentabilidad acumulada</td><td>{_formato_numero(metricas["rentabilidad"])}%</td></tr>
        """

    return f"""
    <div style="font-family:Arial, sans-serif; font-size:13px; min-width:230px;">
        <strong>{indice["nombre"]}</strong><br>
        <span>{indice["pais"]} - {indice["ticker"]}</span>
        <table style="margin-top:6px; width:100%;">
            {cuerpo}
            <tr><td>PIB per capita</td><td>{pib_texto}</td></tr>
        </table>
    </div>
    """


def _tooltip_pais(resultados_pais):
    primer_indice = resultados_pais[0]["indice"]
    filas = []

    for resultado in resultados_pais:
        indice = resultado["indice"]
        metricas = resultado["metricas"]

        if metricas is None:
            filas.append(
                f"""
                <tr>
                    <td>{indice["nombre"]}</td>
                    <td colspan="5">Datos no disponibles</td>
                </tr>
                """
            )
            continue

        filas.append(
            f"""
            <tr>
                <td>{indice["nombre"]}</td>
                <td>{_formato_numero(metricas["precio_actual"])}</td>
                <td>{_formato_numero(metricas["variacion"])}%</td>
                <td>{_formato_numero(metricas["maximo"])}</td>
                <td>{_formato_numero(metricas["minimo"])}</td>
                <td>{_formato_numero(metricas["rentabilidad"])}%</td>
            </tr>
            """
        )

    pib = primer_indice.get("pib_per_capita")
    pib_texto = f"${pib:,.0f}" if pib else "N/D"

    return f"""
    <div style="font-family:Arial, sans-serif; font-size:13px; min-width:520px;">
        <strong>{primer_indice["pais"]}</strong><br>
        <span>PIB per capita: {pib_texto}</span>
        <table style="margin-top:8px; width:100%; border-collapse:collapse;">
            <thead>
                <tr>
                    <th style="text-align:left;">Indice</th>
                    <th style="text-align:right;">Precio</th>
                    <th style="text-align:right;">Var.</th>
                    <th style="text-align:right;">Max.</th>
                    <th style="text-align:right;">Min.</th>
                    <th style="text-align:right;">Rent.</th>
                </tr>
            </thead>
            <tbody>{''.join(filas)}</tbody>
        </table>
    </div>
    """


def _crear_colormap(rentabilidades):
    from branca.colormap import LinearColormap

    valores = [abs(valor) for valor in rentabilidades if math.isfinite(valor)]
    max_abs = max(valores) if valores else 1
    max_abs = max(max_abs, 1)

    return LinearColormap(
        colors=["#8b0000", "#d73027", "#f7f7f7", "#1a9850", "#006400"],
        index=[-max_abs, -max_abs / 2, 0, max_abs / 2, max_abs],
        vmin=-max_abs,
        vmax=max_abs,
        caption="Rentabilidad acumulada (%)",
    )


def _agrupar_por_pais(resultados):
    paises = {}

    for resultado in resultados:
        iso3 = resultado["indice"]["iso3"]
        paises.setdefault(iso3, []).append(resultado)

    return paises


def _agrupar_por_nombre_geojson(resultados):
    paises = {}

    for resultado in resultados:
        nombre = resultado["indice"].get("geojson_nombre")
        if nombre:
            paises.setdefault(nombre, []).append(resultado)

    return paises


def _rentabilidad_pais(resultados_pais):
    rentabilidades = [
        resultado["metricas"]["rentabilidad"]
        for resultado in resultados_pais
        if resultado["metricas"] is not None
    ]

    if not rentabilidades:
        return None

    return sum(rentabilidades) / len(rentabilidades)


def _anadir_paises_coloreados(mapa, resultados, colormap):
    import folium

    geojson = _cargar_geojson_paises()
    resultados_por_pais = _agrupar_por_pais(resultados)
    resultados_por_nombre = _agrupar_por_nombre_geojson(resultados)

    folium.GeoJson(
        geojson,
        name="Paises",
        style_function=lambda feature: {
            "fillColor": "#d9dee3",
            "color": "#ffffff",
            "weight": 0.4,
            "fillOpacity": 0.16,
        },
    ).add_to(mapa)

    for feature in geojson["features"]:
        iso3 = feature["properties"].get("ISO3166-1-Alpha-3")
        nombre = feature["properties"].get("name")
        resultados_pais = resultados_por_pais.get(iso3) or resultados_por_nombre.get(nombre)

        if not resultados_pais:
            continue

        rentabilidad = _rentabilidad_pais(resultados_pais)
        color = colormap(rentabilidad) if rentabilidad is not None else "#808080"

        folium.GeoJson(
            feature,
            name=resultados_pais[0]["indice"]["pais"],
            style_function=lambda feature, color=color: {
                "fillColor": color,
                "color": "#2f3b45",
                "weight": 0.8,
                "fillOpacity": 0.68,
            },
            highlight_function=lambda feature: {
                "weight": 2,
                "color": "#111827",
                "fillOpacity": 0.82,
            },
            tooltip=folium.Tooltip(_tooltip_pais(resultados_pais), sticky=True),
        ).add_to(mapa)


@lru_cache(maxsize=8)
def crear_mapa_indices(periodo):
    import folium

    resultados = []

    for indice in INDICES_MUNDIALES:
        try:
            metricas = _calcular_metricas(indice, periodo)
            resultados.append({"indice": indice, "metricas": metricas, "error": None})
        except Exception as exc:
            resultados.append({"indice": indice, "metricas": None, "error": str(exc)})

    rentabilidades = [
        resultado["metricas"]["rentabilidad"]
        for resultado in resultados
        if resultado["metricas"] is not None
    ]
    colormap = _crear_colormap(rentabilidades)

    mapa = folium.Map(
        location=[20, 0],
        zoom_start=2,
        tiles="CartoDB positron",
        control_scale=True,
        world_copy_jump=True,
    )

    try:
        _anadir_paises_coloreados(mapa, resultados, colormap)
    except Exception:
        pass

    for resultado in resultados:
        indice = resultado["indice"]
        metricas = resultado["metricas"]
        error = resultado["error"]

        if metricas:
            rentabilidad = metricas["rentabilidad"]
            color = colormap(rentabilidad)
            radio = 4
            fill_opacity = 0.95
        else:
            color = "#808080"
            radio = 4
            fill_opacity = 0.7

        folium.CircleMarker(
            location=[indice["latitud"], indice["longitud"]],
            radius=radio,
            color=color,
            weight=2,
            fill=True,
            fill_color=color,
            fill_opacity=fill_opacity,
            tooltip=folium.Tooltip(
                _tooltip(indice, metricas=metricas, error=error),
                sticky=True,
            ),
        ).add_to(mapa)

    colormap.add_to(mapa)

    return mapa
