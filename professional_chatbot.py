import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.metrics import confusion_matrix, classification_report
import random

# 1. Dataset Expandido con nueva categoria: "pregunta"
datos = [
    ("hola", "saludo"), ("buenos dias", "saludo"), ("hey", "saludo"),
    ("me encanta", "positivo"), ("genial", "positivo"), ("excelente", "positivo"),
    ("no me gusta", "negativo"), ("pesimo", "negativo"), ("horrible", "negativo"),
    ("adios", "despedida"), ("chao", "despedida"),
    ("cuanto es", "pregunta"), ("que hora es", "pregunta"), ("ayudame con", "pregunta"),
    ("donde esta", "pregunta"), ("por que", "pregunta"), ("como puedo", "pregunta")
]

frases, y = zip(*datos)

# 2. Pipeline Profesional
modelo = make_pipeline(
    TfidfVectorizer(ngram_range=(1, 2)),
    MLPClassifier(hidden_layer_sizes=(20, 10), max_iter=2000, random_state=42)
)

print("Entrenando cerebro profesional...")
modelo.fit(frases, y)

# 3. Mostrar Métricas (Evaluando con los mismos datos de entrenamiento por ahora)
y_pred = modelo.predict(frases)
print("\n--- REPORTE DE MÉTRICAS ---")
print(classification_report(y, y_pred))

# 4. Respuestas
respuestas = {
    "saludo": ["¡Hola! Soy tu IA mejorada.", "¡Hola! ¿En qué te ayudo hoy?"],
    "positivo": ["¡Me alegra que te guste!", "¡Excelente! Gracias por el feedback."],
    "negativo": ["Lamento eso. ¿Podemos hacer algo mejor?", "Entiendo, tomamos nota."],
    "pregunta": ["Soy una IA de lenguaje, aún no puedo responder datos en tiempo real, pero entiendo que tienes una duda.", "Buena pregunta, estoy aprendiendo a investigar datos externos."],
    "despedida": ["¡Hasta luego!", "Nos vemos."],
    "desconocido": ["Mmm, eso está fuera de mi entrenamiento actual.", "No estoy seguro de cómo responder a eso."]
}

print("\n--- CHATBOT PRO ACTIVADO ---")
while True:
    user = input("Tú: ").lower()
    if user == "salir": break
    
    # Obtener probabilidades
    probs = modelo.predict_proba([user])[0]
    max_prob = max(probs)
    idx = np.argmax(probs)
    categoria = modelo.classes_[idx]
    
    # Lógica de Confianza Estratégica
    # Si la confianza es baja (ej: < 0.5), no arriesgamos una respuesta incorrecta
    if max_prob < 0.5:
        categoria = "desconocido"
        
    res = random.choice(respuestas[categoria])
    print(f"Bot: {res} (Categoría: {categoria} | Confianza: {max_prob*100:.2f}%)\n")
