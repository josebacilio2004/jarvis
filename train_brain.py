import psycopg2
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
import joblib # Para guardar el modelo entrenado

# 1. Configuración
nlp = spacy.load("es_core_news_sm")

def get_db_connection():
    return psycopg2.connect(host="localhost", database="chatbot_db", user="admin", password="password123")

def limpiar(texto):
    doc = nlp(texto.lower())
    return " ".join([t.lemma_ for t in doc if not t.is_stop and not t.is_punct])

# 2. Función para enseñar al Bot
def ensenar_bot():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Buscar mensajes desconocidos en el historial
    cur.execute("SELECT DISTINCT mensaje FROM historial WHERE intento = 'desconocido'")
    desconocidos = cur.fetchall()
    
    if not desconocidos:
        print("¡El bot entiende todo por ahora! No hay mensajes nuevos para etiquetar.")
    else:
        print(f"Encontré {len(desconocidos)} frases que el bot no entendió.")
        for row in desconocidos:
            mensaje = row[0]
            print(f"\nFrase: '{mensaje}'")
            nueva_etiqueta = input("¿Qué intención es esta? (saludo/positivo/negativo/pregunta/ignorar): ")
            
            if nueva_etiqueta != "ignorar":
                # Guardar en la tabla de conocimiento real
                cur.execute("INSERT INTO conocimiento (pregunta_clave, respuesta) VALUES (%s, %s)", 
                           (mensaje, nueva_etiqueta))
                # MARCAR COMO ENTENDIDO en el historial para no preguntar de nuevo
                cur.execute("UPDATE historial SET intento = %s WHERE mensaje = %s", 
                           (nueva_etiqueta, mensaje))
        
    conn.commit()
    entrenar_modelo_final(conn)
    conn.close()

def entrenar_modelo_final(conn):
    cur = conn.cursor()
    cur.execute("SELECT pregunta_clave, respuesta FROM conocimiento")
    datos = cur.fetchall()
    
    if len(datos) < 2:
        print("Se necesitan al menos 2 ejemplos para entrenar.")
        return

    frases, etiquetas = zip(*datos)
    frases_limpias = [limpiar(f) for f in frases]
    
    modelo = make_pipeline(TfidfVectorizer(), MLPClassifier(hidden_layer_sizes=(20,), max_iter=2000))
    modelo.fit(frases_limpias, etiquetas)
    
    # Guardar el modelo en un archivo para que el chatbot lo use
    joblib.dump(modelo, 'modelo_chatbot.pkl')
    print("¡Cerebro re-entrenado y guardado en 'modelo_chatbot.pkl'!")

if __name__ == "__main__":
    # Primero creamos las tablas si no existen
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS conocimiento (id SERIAL PRIMARY KEY, pregunta_clave TEXT, respuesta TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS historial (id SERIAL PRIMARY KEY, mensaje TEXT, intento VARCHAR(50), fecha TIMESTAMP)")
    # Insertar datos base si la tabla está vacía
    cur.execute("SELECT COUNT(*) FROM conocimiento")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO conocimiento (pregunta_clave, respuesta) VALUES ('hola', 'saludo'), ('adios', 'despedida'), ('excelente', 'positivo'), ('horrible', 'negativo')")
    conn.commit()
    conn.close()
    
    ensenar_bot()
