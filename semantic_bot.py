import spacy
import numpy as np
import psycopg2

# 1. Cargar SpaCy
nlp = spacy.load("es_core_news_sm")

def get_db_connection():
    return psycopg2.connect(host="localhost", database="chatbot_db", user="admin", password="password123")

# 2. Base de conocimientos extendida
conocimiento_base = {
    "saludo": ["hola", "buenos dias", "como estas", "que tal"],
    "negativo": ["me duele algo", "estoy mal", "horrible", "pesimo", "no me gusta"],
    "positivo": ["excelente", "maravilla", "me gusta", "genial", "feliz"],
    "ayuda": ["ayudame", "tengo una duda", "necesito soporte", "auxilio"]
}

def encontrar_mejor_coincidencia(texto_usuario):
    doc_usuario = nlp(texto_usuario.lower())
    mejor_categoria = "desconocido"
    max_similitud = 0
    
    # Comparamos la frase del usuario con cada ejemplo que tenemos
    for categoria, ejemplos in conocimiento_base.items():
        for ejemplo in ejemplos:
            similitud = doc_usuario.similarity(nlp(ejemplo))
            if similitud > max_similitud:
                max_similitud = similitud
                mejor_categoria = categoria
                
    return mejor_categoria, max_similitud

print("\n--- BOT SEMÁNTICO ACTIVADO ---")
print("Este bot entiende conceptos, no solo palabras clave.\n")

while True:
    usuario = input("Tú: ")
    if usuario.lower() == "salir": break
    
    categoria, confianza = encontrar_mejor_coincidencia(usuario)
    
    # Si la similitud es alta (aunque las palabras no sean iguales)
    if confianza > 0.7:
        respuestas = {
            "saludo": "¡Hola! Qué gusto saludarte.",
            "negativo": "Lamento que te sientas así o tengas una mala experiencia. ¿Cómo te ayudo?",
            "positivo": "¡Me alegra mucho! Todo va por buen camino.",
            "ayuda": "Estoy aquí para ayudarte. Dime qué necesitas."
        }
        print(f"Bot: {respuestas.get(categoria)} (Similitud semántica: {confianza*100:.1f}%)")
    else:
        print(f"Bot: No estoy seguro, pero suena un poco a '{categoria}'. ¿Es correcto? (Confianza baja: {confianza*100:.1f}%)")
    print("")
