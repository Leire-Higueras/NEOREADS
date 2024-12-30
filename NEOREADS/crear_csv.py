import requests
import pandas as pd
import os

#Funcion para buscar libros en la API de Google Books con paginacion
def buscar_libros_por_palabra_clave(palabra_clave, max_resultados_por_palabra=1000):
    libros = []
    resultados_por_pagina = 40
    for start_index in range(0, max_resultados_por_palabra, resultados_por_pagina):
        url = (f'https://www.googleapis.com/books/v1/volumes?q={palabra_clave}&startIndex={start_index}'
               f'&maxResults={resultados_por_pagina}&langRestrict=es')
        respuesta = requests.get(url)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            if 'items' in datos:
                for item in datos['items']:
                    info = item['volumeInfo']
                    libros.append({
                        'Título': info.get('title', 'N/A'),
                        'Autores': ', '.join(info.get('authors', [])),
                        'ISBN': next((id['identifier'] for id in info.get('industryIdentifiers', []) if id['type'] == 'ISBN_13'), 'N/A'),
                        'Número de Páginas': info.get('pageCount', 'N/A'),
                        'Fecha de Publicación': info.get('publishedDate', 'N/A'),
                        'Imagen de la Portada': info.get('imageLinks', {}).get('thumbnail', 'N/A'),
                        'Sinopsis': info.get('description', 'N/A'),
                        'Géneros': ', '.join(info.get('categories', [])),  #Combinar muchos generos
                        'Calificación de Usuarios': info.get('averageRating', 'N/A'),
                        'Número de Opiniones': info.get('ratingsCount', 'N/A')
                    })
    return libros

#Lista de subgeneros literarios
palabras_clave = [
    "novelas", "literatura", "fantasía", "romance", "ciencia ficción", "terror", "drama",
    "dark romance", "enemies to lovers", "monster romance", "comedia", "misterio",
    "BL", "boys love", "manga", "shonen", "shojo", "light novel", "romance paranormal"
]

#Obtener libros para todas las palabras clave
todos_los_libros = []
for palabra_clave in palabras_clave:
    print(f"Buscando libros para la palabra clave: {palabra_clave}")
    libros = buscar_libros_por_palabra_clave(palabra_clave)
    todos_los_libros.extend(libros)


#Crear la carpeta goodreads_data si no existe
carpeta_destino = "goodreads_data"
if not os.path.exists(carpeta_destino):
    os.makedirs(carpeta_destino)


#Guardar los libros en un archivo CSV
if todos_los_libros:
    #Eliminar duplicados por titulo
    df = pd.DataFrame(todos_los_libros).drop_duplicates(subset=['Título'])
    
    #Comprobar el Numero minimo de libros
    while len(df) < 10000:#minimo
        print(f"Actualmente hay {len(df)} libros. Ampliando búsquedas...")
        libros_extra = buscar_libros_por_palabra_clave("nuevas búsquedas", max_resultados_por_palabra=1000)
        df = pd.concat([df, pd.DataFrame(libros_extra)]).drop_duplicates(subset=['Título'])

    ruta_archivo = os.path.join(carpeta_destino, 'libros.csv')
    df.to_csv(ruta_archivo, index=False, encoding='utf-8-sig')
    print(f"Archivo CSV generado exitosamente en: {ruta_archivo}")
    print(f"Número total de libros recopilados: {len(df)}")
else:
    print("No se encontraron libros para las palabras clave proporcionadas.")
