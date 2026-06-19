import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


def grafico_xtb(datos, ticker):

    datos = datos.copy()

    if hasattr(datos.columns, "nlevels") and datos.columns.nlevels > 1:
        datos.columns = datos.columns.droplevel(1)

    datos = datos.dropna(subset=["Close"])

    fig, (ax_precio, ax_volumen) = plt.subplots(
        2,
        1,
        figsize=(12, 6.2),
        sharex=True,
        gridspec_kw={"height_ratios": [4.5, 1.2], "hspace": 0.04},
    )

    fig.patch.set_facecolor("white")

    ax_precio.plot(
        datos.index,
        datos["Close"],
        color="#111111",
        linewidth=1.6,
    )

    ultimo_precio = float(datos["Close"].iloc[-1])
    ax_precio.axhline(
        ultimo_precio,
        color="#111111",
        linewidth=0.8,
        linestyle=":",
        alpha=0.6,
    )
    ax_precio.annotate(
        f"{ultimo_precio:,.2f}",
        xy=(1, ultimo_precio),
        xycoords=("axes fraction", "data"),
        xytext=(8, 0),
        textcoords="offset points",
        va="center",
        fontsize=9,
        color="#111111",
        bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "#111111"},
    )

    if "Volume" in datos.columns:
        ax_volumen.bar(
            datos.index,
            datos["Volume"].fillna(0),
            color="#222222",
            alpha=0.35,
            width=8,
        )

    ax_precio.set_ylabel("Precio", color="#111111")
    ax_volumen.set_ylabel("Volumen", color="#111111")
    ax_volumen.set_xlabel("")

    ax_precio.yaxis.set_major_formatter(FuncFormatter(lambda valor, _: f"{valor:,.0f}"))
    ax_volumen.yaxis.set_major_formatter(
        FuncFormatter(lambda valor, _: f"{valor / 1_000_000:,.0f}M")
    )

    for ax in (ax_precio, ax_volumen):
        ax.set_facecolor("white")
        ax.grid(True, color="#d9d9d9", linewidth=0.7, alpha=0.55)
        ax.tick_params(colors="#111111", labelsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#111111")
        ax.spines["bottom"].set_color("#111111")

    fig.autofmt_xdate(rotation=0)
    fig.subplots_adjust(left=0.07, right=0.96, top=0.98, bottom=0.10)

    return fig
