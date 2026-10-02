import numpy as np
import matplotlib.pyplot as plt

# 1. Definición de la Función de Activación (Sigmoide)
# Ayuda a que la red aprenda patrones complejos (no lineales)
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

# Derivada de la sigmoide para el cálculo del gradiente (retropropagación)
def sigmoid_derivative(x):
    return x * (1 - x)

class RedNeuronal:
    def __init__(self, capas):
        # Inicialización de pesos de forma aleatoria
        # 'capas' es una lista con el número de neuronas por capa (ej: [2, 3, 1])
        self.pesos = []
        for i in range(len(capas) - 1):
            # Pesos entre la capa i y la capa i+1
            peso = np.random.uniform(-1, 1, (capas[i], capas[i+1]))
            self.pesos.append(peso)
        
        self.historial_error = []

    def feedforward(self, X):
        # Propagación hacia adelante: pasar los datos por la red
        self.activaciones = [X]
        for i in range(len(self.pesos)):
            neta = np.dot(self.activaciones[i], self.pesos[i])
            salida = sigmoid(neta)
            self.activaciones.append(salida)
        return self.activaciones[-1]

    def backpropagation(self, X, y, salida, tasa_aprendizaje):
        # Calcular el error final
        error = y - salida
        delta = error * sigmoid_derivative(salida)

        # Ajustar pesos desde la última capa hacia la primera
        for i in reversed(range(len(self.pesos))):
            # El cambio en el peso depende del error y de la activación anterior
            ajuste = self.activaciones[i].T.dot(delta) * tasa_aprendizaje
            
            # Calcular el delta para la capa anterior (encadenamiento)
            if i > 0:
                error_capa_oculta = delta.dot(self.pesos[i].T)
                delta = error_capa_oculta * sigmoid_derivative(self.activaciones[i])
            
            self.pesos[i] += ajuste

    def entrenar(self, X, y, iteraciones, tasa_aprendizaje):
        print(f"Entrenando durante {iteraciones} épocas...")
        for i in range(iteraciones):
            salida = self.feedforward(X)
            self.backpropagation(X, y, salida, tasa_aprendizaje)
            
            error_medio = np.mean(np.square(y - salida))
            self.historial_error.append(error_medio)
            
            if i % 1000 == 0:
                print(f"Época {i} - Error: {error_medio:.6f}")

# --- CONFIGURACIÓN DEL PROBLEMA (XOR) ---
# Entradas: [0,0], [0,1], [1,0], [1,1]
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
# Salidas deseadas: 0, 1, 1, 0
y = np.array([[0], [1], [1], [0]])

# Crear una red con: 2 entradas, 3 neuronas ocultas y 1 salida
red = RedNeuronal([2, 3, 1])

# Entrenar la red
red.entrenar(X, y, iteraciones=10000, tasa_aprendizaje=0.1)

# Probar la red
print("\n--- Resultados Finales ---")
resultados = red.feedforward(X)
for i in range(len(X)):
    print(f"Entrada: {X[i]} -> Predicción: {resultados[i][0]:.4f} (Real: {y[i][0]})")

# Graficar el aprendizaje
plt.plot(red.historial_error)
plt.title('Progreso del Aprendizaje (Reducción del Error)')
plt.xlabel('Épocas')
plt.ylabel('Error Cuadrático Medio')
plt.show()
