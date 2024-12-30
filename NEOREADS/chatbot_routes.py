import logging
import os
from flask import Blueprint, request, jsonify, render_template
import pandas as pd
from unidecode import unidecode
import json

#Crear el Blueprint
chatbot_bp = Blueprint('chatbot', __name__)

#Inicializar el modelo
recommendation_model = None

def initialize_model(model):
    global recommendation_model
    recommendation_model = model

#(NO VUELVE A PASAR! CARPETA BORRADA) Carpeta Logs existe
log_directory = 'Logs'
os.makedirs(log_directory, exist_ok=True)

#Configurar logging en la carpeta Logs
logging.basicConfig(
    filename=os.path.join(log_directory, 'chatbot_logs.log'),
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

#Ruta del archivo CSV
DATA_PATH = 'goodreads_data/libros.csv'

#Cargar datos del CSV
libros_df = pd.read_csv(DATA_PATH)

#Mapeo de generos (el CSV ha cogido mixtos)
GENERO_MAPEO = {
    "fiction": "ficcion",
    "romance": "romance",
    "adventure": "aventura",
    "fantasy": "fantasia",
    "mystery": "misterio",
    "drama": "drama",
    "science fiction": "ciencia ficcion",
    "horror": "horror",
    "thriller": "suspenso",
    "history": "historia",
    "biography": "biografia",
    "poetry": "poesia"
}

#No reconoce: tildes, mayusculas y minusculas (^.^)
def normalizar_texto(texto):
    return unidecode(texto.lower())

#Crear Blueprint
chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')


############################################## RECONOCIMIENTO DE PREGUNTAS CHATBOT ############################################

def buscar_libros(pregunta, df):
    pregunta = normalizar_texto(pregunta)

    #Libros con un rango de paginas (1–1000)
    df = df[(df['Número de Páginas'].astype(float) >= 1) & (df['Número de Páginas'].astype(float) <= 1000)]

    try:
        #Numero de paginas
        num_paginas = next((int(p) for p in pregunta.split() if p.isdigit()), None)

        #Filtro combinado: genero + numero de paginas
        for genero_ing, genero_esp in GENERO_MAPEO.items():
            if (genero_esp in pregunta or genero_ing in pregunta) and num_paginas:
                rango_inferior = num_paginas
                rango_superior = num_paginas + 50
                resultados = df[
                    (df['Géneros'].apply(
                        lambda x: genero_ing in normalizar_texto(x) or genero_esp in normalizar_texto(x)
                        if pd.notna(x) else False
                    )) & 
                    (df['Número de Páginas'].astype(float).between(rango_inferior, rango_superior))
                ]
                logging.info(f"Resultado por género y número de páginas: {resultados.head(5)}")
                return resultados.head(5).to_dict(orient='records')

        #Filtro por rango de paginas
        if "menos de" in pregunta and "paginas" in pregunta:
            rango_superior = (num_paginas // 100) * 100
            resultados = df[df['Número de Páginas'].astype(float) < rango_superior]
            logging.info(f"Resultado por menos de {rango_superior} páginas: {resultados.head(5)}")
            return resultados.head(5).to_dict(orient='records')

        if "mas de" in pregunta and "paginas" in pregunta:
            rango_inferior = ((num_paginas // 100) * 100) + 100
            resultados = df[df['Número de Páginas'].astype(float) >= rango_inferior]
            logging.info(f"Resultado por más de {rango_inferior} páginas: {resultados.head(5)}")
            return resultados.head(5).to_dict(orient='records')

        #Filtro por un numero exacto de paginas
        if "paginas" in pregunta and num_paginas:
            rango_inferior = num_paginas
            rango_superior = num_paginas + 50  #+50 páginas (para que no siempre sea justo)
            resultados = df[df['Número de Páginas'].astype(float).between(rango_inferior, rango_superior)]
            logging.info(f"Resultado por {num_paginas} páginas: {resultados.head(5)}")
            return resultados.head(5).to_dict(orient='records')

        #Filtro por genero con mapeo ampliado (Inglis Vs Castellano (¬.¬))
        for genero_ing, genero_esp in GENERO_MAPEO.items():
            if genero_esp in pregunta or genero_ing in pregunta:
                resultados = df[df['Géneros'].apply(
                    lambda x: genero_ing in normalizar_texto(x) or genero_esp in normalizar_texto(x)
                    if pd.notna(x) else False
                )]
                logging.info(f"Resultado por género {genero_esp}: {resultados.head(5)}")
                return resultados.head(5).to_dict(orient='records')

        #Filtro por autor:(nombre y apellido)
        if "autor" in pregunta or "escritor" in pregunta or "libros de" in pregunta:
            autor_query = pregunta.split("de")[-1].strip()
            autor_query = normalizar_texto(autor_query)

            #Buscamos en los autores del CSV
            resultados = df[df['Autores'].apply(
                lambda x: autor_query in normalizar_texto(x) if pd.notna(x) else False
            )]

            if not resultados.empty:
                logging.info(f"Resultado por autor {autor_query}: {resultados.head(5)}")
                return resultados.head(5).to_dict(orient='records')
            else:
                logging.warning(f"No se encontraron libros del autor '{autor_query}'")
                return [{"Error": f"No encontré libros del autor '{autor_query}'."}]

        #Si escribimos solo un nombre o apellido,  lo busca
        if len(pregunta.split()) == 1:
            palabra_clave = pregunta.strip()
            resultados = df[df['Autores'].apply(
                lambda x: palabra_clave in normalizar_texto(x) if pd.notna(x) else False
            )]

            if not resultados.empty:
                logging.info(f"Resultado por palabra clave {palabra_clave}: {resultados.head(5)}")
                return resultados.head(5).to_dict(orient='records')
            else:
                logging.warning(f"No se encontraron libros relacionados con '{palabra_clave}'")
                return [{"Error": f"No encontré libros relacionados con '{palabra_clave}'."}]

    except Exception as e:
        logging.error(f"Error al procesar la pregunta: {str(e)}")
        return [{"Error": f"Hubo un error procesando tu pregunta: {str(e)}"}]

    return [{"Error": "No entendí tu pregunta. Por favor, pregunta sobre autor, género o número de páginas."}]


############################################## INTEGRACION DEL MODELO ############################################
def generar_recomendaciones(input_usuario):
    if recommendation_model is None:
        return [{"Error": "El modelo no está disponible en este momento."}]
    try:
        # Aquí puedes preprocesar la entrada del usuario si es necesario
        recomendaciones = recommendation_model.predict([input_usuario])
        return [{"Recomendación": rec} for rec in recomendaciones]
    except Exception as e:
        logging.error(f"Error generando recomendaciones: {str(e)}")
        return [{"Error": f"No se pudo generar una recomendación: {str(e)}"}]


############################################## RENDERIZACION DEL CHATBOT ############################################

@chatbot_bp.route('/')
def chatbot():
    return render_template('chatbot.html')

@chatbot_bp.route('/details', methods=['GET'])
def chatbot_details():
    return render_template('chatbot_details.html')

############################################## RESPUESTAS DE PREGUNTAS CHATBOT Y RETROALIMENTACION ############################################

@chatbot_bp.route('/ask', methods=['POST'])
def ask_chatbot():
    data = request.get_json()
    pregunta = data.get('message', '').strip()

    if not pregunta:
        logging.info("Consulta vacía.")
        return jsonify({"reply": ["Por favor, haz una pregunta válida."]})

    try:
        resultados = buscar_libros(pregunta, libros_df)
        respuestas = []

        for i, libro in enumerate(resultados):
            if "Error" in libro:
                respuestas.append(libro["Error"])
            else:
                respuesta = (
                        f"<div><strong>Recomendación {i + 1}:</strong> <br>"
                        f"Título: {libro['Título']}.<br>"
                        f"Escrito por: {libro['Autores']}.<br>"
                        f"Tiene un total de: {int(libro['Número de Páginas'])} páginas.<br>"
                        f"Género: {libro.get('Géneros', 'No especificado')}.</div>"
                )
                respuestas.append(respuesta)

        #Sin resultado
        if not respuestas:
            respuestas.append("No encontré libros que coincidan con tu búsqueda.")

        #Respuestas en un solo string con salto de linea (Para que se vea lo mas bonito y legible posible)
        respuesta_final = "<br>".join(respuestas)

        #Nueva pregunta
        respuesta_final += "<br><p>¿Te gustaría buscar más libros? Escribe una nueva pregunta.</p>"

        logging.info(f"Respuestas generadas: {respuesta_final}")
        return jsonify({"reply": [respuesta_final]})

    except Exception as e:
        logging.error(f"Error procesando la pregunta: {str(e)}")
        return jsonify({"reply": [f"Error procesando la pregunta: {str(e)}"]}), 500

############################################### METRICAS DEL SISTEMA ###########################################

@chatbot_bp.route('/feedback', methods=['GET'])
def get_feedback():
    feedback_data = {"positivo": 10, "negativo": 5}
    return jsonify(feedback_data)

@chatbot_bp.route('/model_metrics', methods=['GET'])
def get_model_metrics():
    import json
    try:
        with open("models/model_metrics.json", "r") as metrics_file:
            metrics = json.load(metrics_file)
        return jsonify(metrics)
    except FileNotFoundError:
        return jsonify({"error": "No se encontraron métricas del modelo."})

