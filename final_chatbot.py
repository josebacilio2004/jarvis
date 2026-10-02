import joblib
import spacy
import psycopg2
import datetime

nlp = spacy.load("es_core_news_sm")

def limpiar(texto):
    doc = nlp(texto.lower())
    return " ".join([t.lemma_ for t in doc if not t.is_stop and not t.is_punct])

try:
    modelo = joblib.load('modelo_chatbot.pkl')
    print("¡Cerebro cargado con éxito!")
except:
    print("Error: No se encontró un modelo entrenado. Ejecuta primero train_brain.py")
    exit()

def log_to_db(mensaje, intento):
    try:
        conn = psycopg2.connect(host="localhost", database="chatbot_db", user="admin", password="password123")
        cur = conn.cursor()
        cur.execute("INSERT INTO historial (mensaje, intento, fecha) VALUES (%s, %s, %s)",
                   (mensaje, intento, datetime.datetime.now()))
        conn.commit()
        conn.close()
    except: pass

print("\n--- CHATBOT CON APRENDIZAJE ACTIVO ---")
while True:
    user = input("Tú: ")
    if user.lower() == "salir": break
    
    limpio = limpiar(user)
    probs = modelo.predict_proba([limpio])[0]
    confianza = max(probs)
    intento = modelo.predict([limpio])[0] if confianza > 0.6 else "desconocido"
    
    log_to_db(user, intento)
    
    if intento == "desconocido":
        print("Bot: No estoy seguro de qué significa eso. Lo he guardado para aprenderlo luego.")
    else:
        print(f"Bot: Entiendo que esto es un {intento} (Confianza: {confianza*100:.1f}%)")
