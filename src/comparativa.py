import yfinance as yf
import matplotlib.pyplot as plt

import yfinance as yf
import matplotlib.pyplot as plt


def comparativa_activos(ticker):

    datos = yf.download([ticker, "SPY", "URTH", "BTC-USD"], period="3y", auto_adjust=True, progress=False)["Close"]

    datos = datos / datos.iloc[0] * 100

    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(datos.index, datos[ticker], label=ticker, linewidth=3)
    ax.plot(datos.index, datos["SPY"], label="S&P 500", linewidth=2)
    ax.plot(datos.index, datos["URTH"], label="MSCI World", linewidth=2)
    ax.plot(datos.index, datos["BTC-USD"], label="Bitcoin", linewidth=2)

    ax.set_title(f"{ticker} vs S&P500, MSCI World y Bitcoin", fontsize=16, fontweight="bold")

    ax.set_ylabel("Rentabilidad Base 100")
    ax.legend(loc="upper left")
    ax.grid(alpha=0.3)

    plt.tight_layout()

    return fig