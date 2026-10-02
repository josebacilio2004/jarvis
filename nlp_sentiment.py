import numpy as np
from simple_nn import RedNeuronal

# 1. Datos de Entrenamiento (Frases simples)
frases = [
    "excelente servicio",
    "me encanta esto",
    "muy buen producto",
    "horrible experiencia",
    "no me gusta nada",
    "pesimo servicio"
]

# Etiquetas: 1 para Positivo, 0 para Negativo
etiquetas = np.array([[1], [1], [1], [0], [0], [0]])

# 2. Vectorización (Bag of Words desde cero)
# Creamos un vocabulario con todas las palabras únicas
vocabulario = sorted(list(set(" ".join(frases).split())))
print(f"Vocabulario ({len(vocabulario)} palabras): {vocabulario}")

def vectorizar(frase, vocab):
    vector = np.zeros(len(vocab))
    palabras = frase.split()
    for p in palabras:
        if p in vocab:
            vector[vocab.index(p)] = 1
    return vector

# Convertimos todas las frases en vectores numéricos
X = np.array([vectorizar(f, vocabulario) for f in frases])

# 3. Crear y Entrenar la Red
# Entrada: tamaño del vocabulario, Oculta: 8 neuronas, Salida: 1
red_nlp = RedNeuronal([len(vocabulario), 8, 1])
red_nlp.entrenar(X, etiquetas, iteraciones=5000, tasa_aprendizaje=0.2)

# 4. Probar con frases nuevas
print("\n--- Probando la IA con frases nuevas ---")
test_frases = [
    "muy bueno",
    "no me gusta",
    "excelente producto",
    "pesimo"
]

for f in test_frases:
    v = vectorizar(f, vocabulario).reshape(1, -1)
    prediccion = red_nlp.feedforward(v)[0][0]
    sentimiento = "Positivo" if prediccion > 0.5 else "Negativo"
    print(f"Frase: '{f}' -> Predicción: {prediccion:.4f} ({sentimiento})")
