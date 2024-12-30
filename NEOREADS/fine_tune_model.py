import pickle
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import json
import os

#Cargar los datos
DATA_PATH = "goodreads_data/Datos_libros_final.csv"
df = pd.read_csv(DATA_PATH)

#Columnas necesarias
required_columns = ["Número de Páginas", "Número de Ventas", "Géneros"]
for col in required_columns:
    if col not in df.columns:
        raise ValueError(f"La columna '{col}' no se encuentra en los datos.")

#Limpieza de datos
df["Número de Páginas"] = pd.to_numeric(df["Número de Páginas"], errors="coerce").fillna(0)
df["Número de Ventas"] = pd.to_numeric(df["Número de Ventas"], errors="coerce").fillna(0)
df["Géneros"] = df["Géneros"].fillna("No especificado")

#Variables de entrada y objetivo
X = df[["Número de Páginas", "Número de Ventas"]]  
y = df["Géneros"]

#Dividir en conjunto de entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

#Ajustar el modelo
print("Entrenando el modelo...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

#Evaluar el modelo
print("Evaluando el modelo...")
y_pred = model.predict(X_test)
print("Reporte de clasificación:")
print(classification_report(y_test, y_pred))
print(f"Precisión: {accuracy_score(y_test, y_pred):.2f}")

#Crear la carpeta 'models'
MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)

#Guardar metricas en 'models'
METRICS_PATH = os.path.join(MODELS_DIR, "model_metrics.json")
metrics = classification_report(y_test, y_pred, output_dict=True)
with open(METRICS_PATH, "w") as metrics_file:
    json.dump(metrics, metrics_file)
print(f"Métricas del modelo guardadas en {METRICS_PATH}")

#4.Guardar el modelo en 'models'
MODEL_PATH = os.path.join(MODELS_DIR, "fine_tuned_model.pkl")
with open(MODEL_PATH, "wb") as model_file:
    pickle.dump(model, model_file)
print(f"Modelo ajustado guardado en {MODEL_PATH}")
