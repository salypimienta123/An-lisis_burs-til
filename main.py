from download_data import descargar_datos
from indicators import media_movil
from download_data import descargar_datos
from heatmaps import rentabilidades_anuales
from heatmaps import crear_heatmap

from download_data import descargar_datos
from heatmaps import rentabilidades_anuales, crear_heatmap


def main() -> None:
    print("=" * 60)
    print("📈 ANALIZADOR BURSÁTIL")
    print("=" * 60)

    ticker = input("Introduce un ticker: ").upper()

    print(f"\nDescargando datos de {ticker}...")

    datos = descargar_datos(ticker)

    print("Calculando rentabilidades...")

    rentabilidades = rentabilidades_anuales(datos)

    print("Generando heatmap...")

    crear_heatmap(rentabilidades, ticker)

    print("Proceso completado.")


if __name__ == "__main__":
    main()