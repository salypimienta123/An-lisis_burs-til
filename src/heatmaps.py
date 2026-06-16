import math
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pandas.core.interchange.dataframe_protocol import DataFrame


def rentabilidades_anuales(df) -> pd.DataFrame:

    precios = df["Close"].squeeze()

    anual = precios.resample("YE").last()

    rentabilidades = anual.pct_change() * 100

    resultado = pd.DataFrame({
        "Precio": anual,
        "Rentabilidad": rentabilidades
    })

    return resultado.dropna()

def crear_heatmap(rentabilidades, empresa: str) -> None:
    """
    Generamos un heatmap de rentabilidades mediante seaborn.
    """
    "-------------------------------------------------"
    valores = rentabilidades["Rentabilidad"].values
    precios = rentabilidades["Precio"].values
    "-------------------------------------------------"
    n = math.ceil(math.sqrt(len(valores))) #calculamos el tamaño nxn
    matriz = np.full((n, n), np.nan) #creamos la matriz vacía

    #Rellenamos la matriz con los valores.
    for i, valor in enumerate(valores):
        fila = i // n
        columna = i % n
        matriz[fila, columna] = valor

    #rellenamos la matriz con los años.
    años = rentabilidades.index.year
    matriz_labels = np.full((n, n), "", dtype=object)

    for i, (año, precio, valor) in enumerate(zip(años, precios, valores)):
        fila = i // n
        columna = i % n

        matriz_labels[fila, columna] = (
            f"{año}\n"
            f"${precio:,.0f}\n"
            f"{valor:+.1f}%"
        )

    plt.figure(figsize=(10, 8) ) #,facecolor="#E0E0E0")
    sns.heatmap(matriz,annot=matriz_labels,fmt="",cmap="RdYlGn",center=0,square=True,linecolor="Black",linewidths=2,cbar=True,
                annot_kws={
                    "fontsize": 10,
                    "fontweight": "bold",
                    "color": "black"
                }
                )
    """
    plt.title("Heatmap de Rentabilidades Anuales",
        fontsize=20,
        fontweight="bold",
        color="black",
        pad=20
    )
    """
    fig = plt.gcf()

    plt.tight_layout()

    return fig