import matplotlib.pyplot as plt
from sklearn import datasets, metrics
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split

# 1. Cargar el dataset de dígitos (8x8 píxeles cada uno)
print("Cargando imágenes de dígitos...")
digitos = datasets.load_digits()

# Mostrar cómo se ve una imagen para la IA
plt.gray()
plt.matshow(digitos.images[0])
plt.title(f"Ejemplo de imagen: Un {digitos.target[0]}")
plt.show()

# 2. Preparar los datos
# Las imágenes son 8x8, pero la red necesita una fila larga de 64 números (8*8)
n_samples = len(digitos.images)
datos = digitos.images.reshape((n_samples, -1))

# Dividir en: 70% para entrenar y 30% para probar si aprendió bien
X_train, X_test, y_train, y_test = train_test_split(
    datos, digitos.target, test_size=0.3, shuffle=False
)

# 3. Crear la Red Neuronal (MLP)
# Una capa oculta de 50 neuronas es suficiente para este reto
red_imagenes = MLPClassifier(hidden_layer_sizes=(50,), max_iter=1000, random_state=1)

print("Entrenando la red para reconocer imágenes...")
red_imagenes.fit(X_train, y_train)

# 4. Evaluar
predicciones = red_imagenes.predict(X_test)
print(f"\nReporte de Clasificación:\n{metrics.classification_report(y_test, predicciones)}")

# Mostrar una predicción real
plt.matshow(X_test[10].reshape(8, 8))
plt.title(f"Predicción de la IA: {predicciones[10]}")
plt.show()
