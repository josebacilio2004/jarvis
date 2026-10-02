from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
import random

# 1. Base de Conocimiento (Intenciones y Respuestas)
datos = [
    # Saludos
    ("hola", "saludo"), ("buenos dias", "saludo"), ("hey", "saludo"), ("que tal", "saludo"),
    # Sentimiento Positivo
    ("me encanta", "positivo"), ("excelente", "positivo"), ("muy bueno", "positivo"), ("genial", "positivo"),
    ("estoy feliz", "positivo"), ("maravilla", "positivo"), ("increible", "positivo"),
    # Sentimiento Negativo
    ("no me gusta", "negativo"), ("horrible", "negativo"), ("pesimo", "negativo"), ("muy malo", "negativo"),
    ("estoy enojado", "negativo"), ("asco", "negativo"), ("sucio", "negativo"),
    # Despedidas
    ("adios", "despedida"), ("chao", "despedida"), ("hasta luego", "despedida"), ("nos vemos", "despedida")
]

frases, intenciones = zip(*datos)

# 2. Entrenar el "Cerebro" del Chat
modelo_chat = make_pipeline(
    TfidfVectorizer(),
    MLPClassifier(hidden_layer_sizes=(10,), max_iter=2000, random_state=42)
)
modelo_chat.fit(frases, intenciones)

# 3. Diccionario de Respuestas
respuestas = {
    "saludo": ["¡Hola! ¿En qué puedo ayudarte?", "¡Buen día! ¿Cómo va todo?", "¡Hola! Qué gusto verte."],
    "positivo": ["¡Me alegra mucho escuchar eso!", "¡Qué bien! Trabajamos para eso.", "¡Genial! Disfrútalo."],
    "negativo": ["Lamento mucho escuchar eso. ¿Cómo puedo compensarlo?", "Sentimos mucho la mala experiencia.", "Tomaremos nota para mejorar de inmediato."],
    "despedida": ["¡Adiós! Vuelve pronto.", "¡Hasta luego! Ten un gran día.", "Nos vemos, ¡cuídate!"],
    "desconocido": ["No estoy seguro de entenderte, ¿puedes decirme más?", "Interesante... cuéntame más."]
}

# 4. Bucle del Chat
print("\n--- IA CHATBOT ACTIVADA ---")
print("(Escribe 'salir' para terminar)\n")

while True:
    usuario = input("Tú: ").lower()
    
    if usuario == "salir":
        print("Bot: ¡Hasta pronto!")
        break
    
    # Predecir intencion
    probabilidades = modelo_chat.predict_proba([usuario])[0]
    max_prob = max(probabilidades)
    
    if max_prob < 0.4: # Si la red no está segura
        categoria = "desconocido"
    else:
        categoria = modelo_chat.predict([usuario])[0]
    
    # Responder
    respuesta = random.choice(respuestas[categoria])
    print(f"Bot: {respuesta} (Intento detectado: {categoria} - Confianza: {max_prob*100:.2f}%)\n")
