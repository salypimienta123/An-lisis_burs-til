import requests
import pandas as pd


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