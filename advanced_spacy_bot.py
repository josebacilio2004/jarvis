import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
import random

# Cargar el modelo de SpaCy en español
nlp = spacy.load("es_core_news_sm")

def limpiar_texto(texto):
    # Lematización: convierte "corriendo" -> "correr", "gatos" -> "gato"
    doc = nlp(texto.lower())
    # Filtramos palabras de parada (stop words) como "el", "la", "de"
    tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
    return " ".join(tokens)

# 1. Dataset de entrenamiento
datos = [
    ("Hola, ¿cómo estás?", "saludo"),
    ("Me llamo José", "identificacion"),
    ("Mi nombre es Luis", "identificacion"),
    ("No me gusta este servicio", "negativo"),
    ("La comida estuvo excelente", "positivo"),
    ("¿Qué hora es?", "pregunta"),
    ("Adiós, nos vemos", "despedida")
]

frases_originales, etiquetas = zip(*datos)
# Limpiamos las frases de entrenamiento con SpaCy
frases_limpias = [limpiar_texto(f) for f in frases_originales]

# 2. Entrenar la red
modelo = make_pipeline(
    TfidfVectorizer(),
    MLPClassifier(hidden_layer_sizes=(15,), max_iter=2000, random_state=42)
)
modelo.fit(frases_limpias, etiquetas)

print("\n--- CHATBOT CON SPACY ACTIVADO ---")
print("Detectando entidades y lematizando en tiempo real...\n")

memoria_nombres = {} # Simulación de base de datos para "José"

while True:
    usuario = input("Tú: ")
    if usuario.lower() == "salir": break
    
    # Análisis de SpaCy para Entidades (Nombres propios)
    doc_usuario = nlp(usuario)
    for ent in doc_usuario.ents:
        if ent.label_ == "PER": # PER = Persona
            memoria_nombres['nombre'] = ent.text
            print(f"Bot: (Guardando '{ent.text}' en memoria...)")

    # Limpiar y predecir
    usuario_limpio = limpiar_texto(usuario)
    intento = modelo.predict([usuario_limpio])[0]
    prob = max(modelo.predict_proba([usuario_limpio])[0])

    # Respuestas dinámicas
    if intento == "identificacion" and 'nombre' in memoria_nombres:
        print(f"Bot: ¡Un gusto conocerte, {memoria_nombres['nombre']}! Soy una IA.")
    elif intento == "saludo" and 'nombre' in memoria_nombres:
        print(f"Bot: ¡Hola de nuevo, {memoria_nombres['nombre']}! ¿En qué te ayudo?")
    else:
        # Respuestas genéricas según el intento
        respuestas = {
            "saludo": "¡Hola! ¿Cómo estás?",
            "negativo": "Lamento escuchar eso, trabajaremos para mejorar.",
            "positivo": "¡Qué alegría! Nos motiva mucho tu comentario.",
            "pregunta": "Entiendo que tienes una duda, aún no tengo acceso a datos externos.",
            "despedida": "¡Adiós! Que tengas un gran día."
        }
        print(f"Bot: {respuestas.get(intento, 'No estoy seguro de entender.')} (Intento: {intento})")
    print("")
