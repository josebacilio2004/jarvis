import psycopg2
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
import datetime

# 1. Conexión a PostgreSQL (Docker)
def get_db_connection():
    try:
        return psycopg2.connect(
            host="localhost",
            database="chatbot_db",
            user="admin",
            password="password123"
        )
    except Exception as e:
        print(f"Error de conexión a DB: {e}")
        return None

# Inicializar tablas si no existen
conn = get_db_connection()
if conn:
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS historial (
            id SERIAL PRIMARY KEY,
            mensaje TEXT,
            intento VARCHAR(50),
            fecha TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()

# 2. Motor NLP
nlp = spacy.load("es_core_news_sm")

def limpiar(texto):
    doc = nlp(texto.lower())
    return " ".join([t.lemma_ for t in doc if not t.is_stop and not t.is_punct])

# 3. Datos iniciales y Entrenamiento
datos_base = [
    ("hola", "saludo"), ("adios", "despedida"), 
    ("me gusta", "positivo"), ("es malo", "negativo")
]
frases, etiquetas = zip(*datos_base)
frases_limpias = [limpiar(f) for f in frases]

modelo = make_pipeline(TfidfVectorizer(), MLPClassifier(hidden_layer_sizes=(10,), max_iter=2000))
modelo.fit(frases_limpias, etiquetas)

# 4. Bucle Interactivo
print("\n--- BOT CONECTADO A POSTGRESQL ---")
while True:
    user_input = input("Tú: ")
    if user_input.lower() == "salir": break
    
    # Predecir
    limpio = limpiar(user_input)
    probs = modelo.predict_proba([limpio])[0]
    confianza = max(probs)
    intento = modelo.predict([limpio])[0] if confianza > 0.5 else "desconocido"
    
    # Guardar en Base de Datos
    if conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO historial (mensaje, intento, fecha) VALUES (%s, %s, %s)",
                   (user_input, intento, datetime.datetime.now()))
        conn.commit()
        cur.close()
        print(f"Bot: (Información persistida en Postgres)")

    print(f"Bot: Detecté que es un {intento} (Confianza: {confianza*100:.2f}%)")
