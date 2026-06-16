import pandas as pd


def estadisticas(rentabilidades):

    rent = rentabilidades["Rentabilidad"]

    return {"Rentabilidad media": rent.mean(),"Mejor año": rent.max(),"Peor año": rent.min(),
        "Años positivos": (rent > 0).sum(),
        "Años negativos": (rent < 0).sum()
    }