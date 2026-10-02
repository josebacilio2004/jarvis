# Deep Dive: La Matemática detrás de la Red Neuronal

Para entender cómo aprende tu red, debemos mirar tres pilares:

## 1. El Forward Pass (Propagación hacia adelante)
Cada neurona es una función matemática simple:
`a = f(Σ(w * x) + b)`

Donde:
- `x`: Entradas.
- `w`: Pesos (La fuerza de la conexión).
- `b`: Sesgo (Bias - Permite mover la función de activación).
- `f`: Función de activación (Sigmoide: `1 / (1 + e^-x)`).

## 2. El Descenso del Gradiente (Optimizador)
El objetivo es minimizar la **Función de Pérdida (L)**.
Actualizamos los pesos usando esta regla:
`w_nuevo = w_viejo - (tasa_aprendizaje * ∂L/∂w)`

- `∂L/∂w` es la pendiente (gradiente). Si es positiva, bajamos el peso; si es negativa, lo subimos.

## 3. Backpropagation (El "Cerebro" del aprendizaje)
Para ajustar un peso en la primera capa basado en un error que ocurrió en la última, usamos la **Regla de la Cadena**:

Si `y = f(u)` y `u = g(x)`, entonces:
`dy/dx = (dy/du) * (du/dx)`

Esto permite que el error "fluya" hacia atrás por todas las capas, indicándole a cada neurona exactamente cuánto debe cambiar sus pesos para que el error total disminuya.

---

### Ejemplo Visual de un Peso:
Imagina un peso inicial de `2.0`. La red predice `0.8` pero lo real era `1.0`.
1. El error es `0.2`.
2. El gradiente (derivada) nos dice que para subir la predicción, el peso debe subir.
3. El gradiente calculado es `0.5`.
4. Si la tasa de aprendizaje es `0.1`:
   `w = 2.0 + (0.1 * 0.5) = 2.05`
   
En la siguiente vuelta, la red estará un poquito más cerca de la verdad.
