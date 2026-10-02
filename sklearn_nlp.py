from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
import numpy as np

# 1. Dataset más grande para aprovechar la potencia
frases = [
    "la comida estuvo excelente y el trato fue genial",
    "me encanto la rapidez y el sabor",
    "increible servicio, volveria mil veces",
    "una maravilla de lugar, muy recomendado",
    "el peor lugar donde he comido jamas",
    "la comida estaba fria y el mesero fue grosero",
    "no me gusto nada, una perdida de tiempo",
    "experiencia horrible, no lo recomiendo",
    "estuvo bien, pero podria mejorar",
    "normal, nada del otro mundo"
]

# Etiquetas: 1 (Positivo), 0 (Negativo), 0.5 (Neutral - sklearn lo tratará como clases distintas si queremos)
# Para simplificar: 1 (Positivo), 0 (Negativo)
y = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0]

# 2. Vectorización Profesional con TF-IDF
# TF-IDF no solo cuenta palabras, sino que les da más peso a las palabras importantes
vectorizador = TfidfVectorizer()
X = vectorizador.fit_transform(frases)

# 3. Red Neuronal de Scikit-learn (MLP: Multi-layer Perceptron)
# Definimos una red con 2 capas ocultas de 10 y 5 neuronas respectivamente
modelo = MLPClassifier(hidden_layer_sizes=(10, 5), max_iter=1000, random_state=1)

# Entrenar
print("Entrenando modelo profesional...")
modelo.fit(X, y)

# 4. Predicción con frases complejas
nuevas_frases = [
    "fue una experiencia increible",
    "el servicio fue pesimo y grosero",
    "me gusto el sabor pero estaba frio"
]

X_test = vectorizador.transform(nuevas_frases)
predicciones = modelo.predict(X_test)
probabilidades = modelo.predict_proba(X_test)

print("\n--- Resultados con Scikit-learn ---")
for i, frase in enumerate(nuevas_frases):
    sentimiento = "Positivo" if predicciones[i] == 1 else "Negativo"
    confianza = probabilidades[i][predicciones[i]] * 100
    print(f"'{frase}' -> {sentimiento} (Confianza: {confianza:.2f}%)")
