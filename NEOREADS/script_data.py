import pandas as pd
import numpy as np

#Ruta
input_path = 'goodreads_data/Datos_libros_final.csv'
output_path = 'goodreads_data/Datos_libros_final.csv'
sales_chart_path = 'goodreads_data/sales_chart_data.csv'

#Cargar los datos y procesar libros
def process_books(input_path, output_path, sales_chart_path):
    try:
        df = pd.read_csv(input_path)
        print("Archivo cargado correctamente.")

        #Numero de Ventas
        if 'Número de Ventas' not in df.columns:
            df['Número de Ventas'] = np.random.randint(100, 1000, size=len(df))
        else:
            df['Número de Ventas'] = df['Número de Ventas'].fillna(0).astype(int)

        #Juntar ventas por saga 
        sales_data = df.groupby('saga', as_index=False)['Número de Ventas'].sum()

        #10 principales
        sales_data = sales_data.sort_values(by='Número de Ventas', ascending=False).head(10)

        #Guardar los datos procesados
        df.to_csv(output_path, index=False)
        sales_data.to_csv(sales_chart_path, index=False)
        print(f"Datos de libros procesados guardados en: {output_path}")
        print(f"Datos para el gráfico guardados en: {sales_chart_path}")
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo en la ruta {input_path}.")
    except Exception as e:
        print(f"Error al procesar los datos: {e}")

#Script principal
if __name__ == "__main__":
    print("Procesando datos de libros y generando datos para el gráfico...")
    process_books(input_path, output_path, sales_chart_path)

    #Archivo procesado
    try:
        processed_df = pd.read_csv(sales_chart_path)
        print("\nPrimeras filas del archivo de datos para el gráfico:")
        print(processed_df.head())
        print("\nNúmero total de entradas en el gráfico:", len(processed_df))
    except Exception as e:
        print(f"Error al cargar el archivo de datos para el gráfico: {e}")