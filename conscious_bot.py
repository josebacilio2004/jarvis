from transformers import pipeline
import spacy

# 1. Cargamos el modelo de "Consciencia" (Zero-Shot Classification en español)
print("Cargando motor de consciencia (Transformers)... esto puede tardar un poco la primera vez.")
# Usamos un modelo optimizado para entender español
clasificador = pipeline("zero-shot-classification", model="Recognai/bert-base-spanish-wwm-cased-xnli")

# 2. Categorías que la IA "conoce" por su propio razonamiento
categorias_inteligentes = ["un saludo cordial", "una queja de salud", "un sentimiento de felicidad", 
                           "una duda matematica", "una despedida", "una peticion de aprendizaje"]

print("\n--- IA CONSCIENTE ACTIVADA ---")
print("Puedes hablar de CUALQUIER cosa. La IA razonará tu intención.\n")

while True:
    usuario = input("Tú: ")
    if usuario.lower() == "salir": break
    
    # La IA analiza el texto sin haber visto ejemplos previos de esta conversacion
    resultado = clasificador(usuario, categorias_inteligentes, hypothesis_template="Este mensaje es {}")
    
    intento_ganador = resultado['labels'][0]
    confianza = resultado['scores'][0]
    
    # Respuestas dinámicas basadas en razonamiento puro
    if confianza > 0.4:
        if "saludo" in intento_ganador:
            print(f"Bot: ¡Hola! Qué gusto saludarte. Mi red neuronal detecta un ambiente amigable.")
        elif "salud" in intento_ganador:
            print(f"Bot: He detectado que mencionas un tema de salud. Lamento que no te sientas bien. ¿Has consultado a un médico?")
        elif "matematica" in intento_ganador:
            print(f"Bot: Veo que tienes una duda lógica o matemática. Aunque soy una IA de lenguaje, puedo intentar ayudarte con el razonamiento.")
        elif "aprendizaje" in intento_ganador:
            print(f"Bot: Entiendo que quieres que evolucione. Estoy procesando tu mensaje para mejorar mi red neuronal.")
        elif "felicidad" in intento_ganador:
            print(f"Bot: ¡Esa energía positiva es contagiosa! Me alegra mucho leer eso.")
        else:
            print(f"Bot: Entiendo que te refieres a {intento_ganador}.")
    else:
        print("Bot: Entiendo tus palabras, pero mi nivel de confianza es bajo. ¿Podrías explicarme un poco más?")

    print(f"(Razonamiento IA: {intento_ganador} | Confianza: {confianza*100:.2f}%)\n")
