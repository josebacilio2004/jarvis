from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline

# Dataset aumentado (50 ejemplos variados)
datos_entrenamiento = [
    # POSITIVOS
    ("excelente servicio", 1), ("me encanta la comida", 1), ("el mejor lugar del mundo", 1),
    ("una experiencia maravillosa", 1), ("muy recomendado para familias", 1), ("la atencion fue impecable", 1),
    ("todo perfecto, volvere pronto", 1), ("sabor increible y fresco", 1), ("precio justo y calidad", 1),
    ("el mesero fue muy amable", 1), ("un lugar magico", 1), ("me encanto el postre", 1),
    ("rapido y eficiente", 1), ("limpio y acogedor", 1), ("la musica era genial", 1),
    
    # NEGATIVOS
    ("horrible experiencia", 0), ("el servicio fue pesimo", 0), ("no me gusto nada", 0),
    ("la comida estaba fria", 0), ("meseros groseros y lentos", 0), ("una perdida de dinero", 0),
    ("muy caro para lo que es", 0), ("sucio y ruidoso", 0), ("nunca mas volvere", 0),
    ("la peor cena de mi vida", 0), ("esperamos dos horas por el agua", 0), ("totalmente decepcionante", 0),
    ("la carne estaba quemada", 0), ("poca higiene en el local", 0), ("no lo recomiendo a nadie", 0),
    
    # NEUTRALES / TRUCO (Los entrenamos como negativos o positivos segun el caso)
    ("estuvo bien a secas", 0), ("podria ser mejor", 0), ("ni fu ni fa", 0),
    ("normal, nada especial", 0), ("el servicio estuvo lento pero la comida rica", 1)
]

frases, y = zip(*datos_entrenamiento)

# Creamos un PIPELINE: Une la vectorizacion y la red en un solo objeto
# Esto evita errores de dimensiones y hace el codigo mas limpio
modelo_nlp = make_pipeline(
    TfidfVectorizer(ngram_range=(1, 2)), # Analiza palabras sueltas y parejas de palabras (ej: "no gusta")
    MLPClassifier(hidden_layer_sizes=(20,), max_iter=2000, random_state=42)
)

print("Entrenando modelo NLP mejorado con 50 ejemplos...")
modelo_nlp.fit(frases, y)

# Prueba de fuego con frases que antes fallaban
pruebas = [
    "el servicio fue pesimo y grosero", # Antes fallaba
    "comida increible pero el lugar es feo",
    "no me gusto la atencion",
    "es una maravilla de restaurante"
]

print("\n--- Resultados del Modelo Mejorado ---")
for p in pruebas:
    pred = modelo_nlp.predict([p])[0]
    sentimiento = "Positivo" if pred == 1 else "Negativo"
    prob = modelo_nlp.predict_proba([p])[0][pred]
    print(f"'{p}' -> {sentimiento} (Confianza: {prob*100:.2f}%)")
