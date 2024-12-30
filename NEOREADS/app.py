import pickle 
from flask import Flask, render_template, request, jsonify
from chatbot_routes import chatbot_bp
import pandas as pd

app = Flask(__name__)

#Ruta del modelo
MODEL_PATH = "models/fine_tuned_model.pkl"

#Cargar el modelo al iniciar la página
try:
    with open(MODEL_PATH, 'rb') as model_file:
        recommendation_model = pickle.load(model_file)
        print("Modelo ajustado cargado correctamente.")
except Exception as e:
    #Si el modelo no existe
    print(f"Error al cargar el modelo ajustado: {e}")
    recommendation_model = None

#Registrar Blueprint
app.register_blueprint(chatbot_bp)

#Ruta del archivo CSV
DATA_PATH = 'goodreads_data/libros.csv'

#Cargar datos de libros desde el CSV
try:
    libros_df = pd.read_csv(DATA_PATH)
    print("Archivo cargado correctamente.")

    #Limpiar los datos
    libros_df['Imagen de la Portada'] = libros_df['Imagen de la Portada'].str.strip()  # Eliminar espacios adicionales
    libros_df = libros_df.astype(str).fillna("No disponible")
except FileNotFoundError:
    print(f"Error: No se encontró el archivo en la ruta {DATA_PATH}.")
    libros_df = pd.DataFrame()
except Exception as e:
    print(f"Error al cargar los datos: {e}")
    libros_df = pd.DataFrame()

#Diccionarios para pasarlo a las plantillas
books = libros_df.to_dict(orient='records')

############################ Index #########################
@app.route('/')
def index():
    try:
        sales_data = pd.read_csv('goodreads_data/sales_chart_data.csv')

        #10 entradas
        if len(sales_data) > 10:
            sales_data = sales_data.head(10)

        chart_data = {
            "labels": sales_data['saga'].tolist(),
            "values": sales_data['Número de Ventas'].tolist()
        }
    except FileNotFoundError:
        #No exista el archivo de ventas
        print("No se encontró el archivo de datos de ventas.")
        chart_data = {"labels": [], "values": []}
    except Exception as e:
        print(f"Error al cargar los datos de ventas: {e}")
        chart_data = {"labels": [], "values": []}

    return render_template('index.html', chart_data=chart_data)

############################ Barra de Busqueda #########################

@app.route('/search')
def buscar_libros():
    query = request.args.get('query', '').lower()

    #Si no hay busqueda, se va a todos los libros
    if not query:
        return render_template('books.html', books=books, query=None)

    #Filtrar por Titulo, Autores, Generos o ISBN
    resultados = [
        libro for libro in books
        if query in str(libro.get('Título', '')).lower()
        or query in str(libro.get('Autores', '')).lower()
        or query in str(libro.get('Géneros', '')).lower()
        or query in str(libro.get('ISBN', '')).lower() 
    ]

    #Resultados filtrados
    return render_template('books.html', books=resultados, query=query)

############################ Explorar Libros #########################
@app.route('/books')
def lista_libros():
    if libros_df.empty:
        return render_template('books.html', books=[], message="No hay libros disponibles.")
    return render_template('books.html', books=books)

@app.route('/books/<int:book_id>')
def detalle_libro(book_id):
    if 0 <= book_id < len(books):
        book = books[book_id]
        return render_template('technicalSheet.html', book=book)
    else:
        return "Libro no encontrado", 404

############################ Mi Libreria #########################
@app.route('/library')
def library():
    return render_template('library.html')

############################ ChatBot #########################
@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

#Ruta para manejar las preguntas del chatbot
@app.route('/chatbot/ask', methods=['POST'])
def chatbot_ask():
    try:
        #Mensaje del usuario
        user_message = request.json.get('message', '').lower()
        
        #Respuesta basica
        if 'recomiéndame' in user_message or 'recomendar' in user_message:
            reply = "¡Claro! Te recomiendo 'El Hobbit' de J.R.R. Tolkien. Es una fantástica obra para empezar tu viaje en la literatura de fantasía."
        elif 'ayuda' in user_message:
            reply = "Estoy aquí para ayudarte. Preguntame sobre libros, autores o generos, y hare todo lo posible para responder."
        else:
            reply = "Lo siento, no entendi tu pregunta. Por favor, intenta reformularla o se más especifico."

        #Devolver la respuesta
        return jsonify({"reply": reply})

    except Exception as e:
        #Errores
        return jsonify({"reply": f"Hubo un error procesando tu mensaje: {str(e)}"}), 500

############################ Configuracion ########################
@app.route('/settings')
def settings():
    return render_template('settings.html')


############################ Errores #########################
#Errores Bonitos
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', message="Página no encontrada."), 404

if __name__ == '__main__':
    app.run(debug=True)
