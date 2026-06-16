import yfinance as yf
import pandas as pd


def obtener_fundamentales(ticker):

    info = yf.Ticker(ticker).info

    datos = {
        "Market Cap": info.get("marketCap"),
        "PER": info.get("trailingPE"),
        "Forward PER": info.get("forwardPE"),
        "Dividend Yield (%)": (
            info.get("dividendYield", 0) * 100
            if info.get("dividendYield")
            else None
        ),
        "Beta": info.get("beta"),
        "ROE (%)": (
            info.get("returnOnEquity", 0) * 100
            if info.get("returnOnEquity")
            else None
        ),
        "Margen Beneficio (%)": (
            info.get("profitMargins", 0) * 100
            if info.get("profitMargins")
            else None
        )
    }

    return pd.DataFrame(
        datos.items(),
        columns=["Métrica", "Valor"]
    )