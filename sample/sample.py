import sqlite3
import requests
import subprocess
from urllib.parse import urlparse
import os

def setup_db():
    con = sqlite3.connect(":memory:")
    cur = con.cursor()
    cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)")
    cur.executemany(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        [("alice", "s3cret"), ("bob", "hunter2")]
    )
    # Configuración de tabla para pruebas de SQL Injection
    cur.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, price REAL)")
    cur.executemany(
        "INSERT INTO products (name, price) VALUES (?, ?)",
        [("apple", 1.0), ("banana", 0.5), ("cherry", 2.0)]
    )
    con.commit()
    return con

def login(con, username, password):
    cur = con.cursor()
    # Implementación vulnerable a SQL Injection
    sql_query = f"SELECT id FROM users WHERE username = '{username}' AND password = '{password}'"
    cur.execute(sql_query)
    return cur.fetchone()

def new_login(con, username, password):
    cur = con.cursor()
    # Implementación segura mediante consultas parametrizadas
    cur.execute(
        "SELECT id FROM users WHERE username = ? AND password = ?",
        (username, password)
    )
    return cur.fetchone()

def check_username(username):
    # Implementación vulnerable a Server-Side Request Forgery (SSRF)
    response = requests.get(f"https://api.github.com/users/{username}")
    return response

def is_online_username(username):
    # Implementación vulnerable a inyección de comandos
    import os
    os.system(f"touch /tmp/{username}")

# Casos de prueba adicionales

def search_products(con, query):
    cur = con.cursor()
    # Vulnerabilidad de SQL Injection por concatenación de cadenas
    sql_query = f"SELECT * FROM products WHERE name LIKE '%{query}%'"
    cur.execute(sql_query)
    return cur.fetchall()

def safe_ping(hostname):
    # Implementación segura de ejecución de comandos (lista de argumentos)
    try:
        # Nota: Herramientas SAST pueden reportar falso positivo por uso de subprocess
        subprocess.run(["ping", "-c", "1", hostname], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def fetch_website(url):
    # Implementación segura contra SSRF (Validación de lista blanca)
    allowed_domains = ["google.com", "github.com"]
    try:
        domain = urlparse(url).netloc
        if domain in allowed_domains:
            # Nota: Posible falso positivo en SAST debido a URL dinámica
            return requests.get(url)
    except:
        pass
    return None

def unsafe_ping(hostname):
    # Vulnerabilidad de inyección de comandos (shell=True)
    subprocess.Popen(f"ping -c 1 {hostname}", shell=True)

def get_user_profile(con, user_id):
    cur = con.cursor()
    # Mitigación de SQL Injection mediante validación de tipos (casting)
    # Nota: Uso de f-string seguro tras validación de tipo
    try:
        uid = int(user_id)
        cur.execute(f"SELECT * FROM users WHERE id = {uid}")
        return cur.fetchone()
    except ValueError:
        return None

def demo():
    con = setup_db()

    print("--- Running Demo ---")
    username = "alice"
    password = "s3cret"
    
    # Casos originales
    # login(con, username, password)
    # new_login(con, username, password)
    # check_username(username)
    # is_online_username(username)

    # Nuevos casos
    print(f"Search 'apple': {search_products(con, 'apple')}")
    print(f"Safe ping localhost: {safe_ping('localhost')}")
    print(f"Fetch google: {fetch_website('https://google.com')}")
    print(f"Get profile 1: {get_user_profile(con, '1')}")
    # unsafe_ping("localhost") # No ejecutar para evitar efectos secundarios

if __name__ == "__main__":
    demo()
