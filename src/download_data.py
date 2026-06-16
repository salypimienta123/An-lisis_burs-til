import yfinance as yf

def descargar_datos(ticker):
    """
    Importamos el ticker y el periodo en concreto
    """
    return yf.download(ticker, period="15y")