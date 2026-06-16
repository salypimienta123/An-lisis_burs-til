import mplfinance as mpf


import mplfinance as mpf


def grafico_xtb(datos, ticker):

    datos = datos.copy()

    if hasattr(datos.columns, "nlevels") and datos.columns.nlevels > 1:
        datos.columns = datos.columns.droplevel(1)

    #datos["MM50"] = datos["Close"].rolling(50).mean()
    #datos["MM200"] = datos["Close"].rolling(200).mean()

    mc = mpf.make_marketcolors(up="green",down="red",edge="inherit",wick="inherit",volume="inherit")
    estilo = mpf.make_mpf_style(marketcolors=mc,gridstyle=":",y_on_right=True)
    fig, axlist = mpf.plot(datos,type="candle",volume=False,mav=(50, 200),style=estilo,figsize=(8, 4),returnfig=True)
    axlist[0].set_ylabel(None)

    return fig