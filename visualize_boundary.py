import numpy as np
import matplotlib.pyplot as plt
from simple_nn import RedNeuronal, X, y

# Usamos la red que ya definimos (pero la re-entrenamos un poco más para que sea perfecta)
red = RedNeuronal([2, 5, 1]) # Un poco más de neuronas ocultas para mejor resolución
red.entrenar(X, y, iteraciones=20000, tasa_aprendizaje=0.1)

def plot_decision_boundary(red, X, y):
    # Crear una malla de puntos para cubrir el espacio de entrada
    x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
    y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
    xx, yy = np.meshgrid(np.arange(x_min, x_max, 0.02),
                         np.arange(y_min, y_max, 0.02))
    
    # Predecir para cada punto de la malla
    grid_points = np.c_[xx.ravel(), yy.ravel()]
    Z = red.feedforward(grid_points)
    Z = Z.reshape(xx.shape)
    
    # Graficar
    plt.figure(figsize=(8, 6))
    plt.contourf(xx, yy, Z, cmap=plt.cm.RdYlBu, alpha=0.8)
    plt.scatter(X[:, 0], X[:, 1], c=y.flatten(), s=100, edgecolors='k', cmap=plt.cm.RdYlBu)
    plt.title("Frontera de Decisión: Cómo la Red separa los datos")
    plt.xlabel("Entrada 1")
    plt.ylabel("Entrada 2")
    plt.colorbar(label="Probabilidad de Salida")
    plt.show()

print("\nGenerando mapa visual de la neurona...")
plot_decision_boundary(red, X, y)
