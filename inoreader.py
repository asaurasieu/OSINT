import requests
from urllib.parse import urlencode, urlparse, parse_qs
from dotenv import load_dotenv
import os
import webbrowser
import uuid
import json

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

TOKEN_FILE = 'tokens.json'

def save_tokens(access_token, refresh_token):
    tokens = {
        'access_token': access_token,
        'refresh_token': refresh_token
    }
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f)

def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    return None

def obtener_codigo_autorizacion(client_id, redirect_uri):
    state = str(uuid.uuid4())  # Genera un UUID como estado único
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'read',
        'state': state
    }
    url = 'https://www.inoreader.com/oauth2/auth?' + urlencode(params)
    webbrowser.open(url)
    print(f"Estado generado: {state}")
    print(f"Por favor, autoriza la aplicación en la siguiente URL: {url}")
    redirect_response = input("Pega la URL completa de redirección aquí: ")
    parsed_url = urlparse(redirect_response)
    response_state = parse_qs(parsed_url.query).get('state', [None])[0]
    code = parse_qs(parsed_url.query).get('code', [None])[0]
    
    print(f"Estado recibido: {response_state}")
    print(f"Código recibido: {code}")
    
    if response_state != state:
        print("El estado de la respuesta no coincide. Posible ataque CSRF.")
        return None
    
    if not code:
        print("No se recibió ningún código de autorización.")
        return None
    
    return code

def obtener_token_acceso(client_id, client_secret, redirect_uri, code):
    url = 'https://www.inoreader.com/oauth2/token'
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
        'code': code,
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        tokens = response.json()
        save_tokens(tokens['access_token'], tokens['refresh_token'])
        return tokens['access_token']
    else:
        print(f"Error al obtener el token de acceso: {response.status_code}")
        print(response.text)
        return None

def refresh_token(client_id, client_secret, refresh_token):
    url = 'https://www.inoreader.com/oauth2/token'
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        tokens = response.json()
        save_tokens(tokens['access_token'], tokens['refresh_token'])
        return tokens['access_token']
    else:
        print(f"Error al refrescar el token: {response.status_code}")
        print(response.text)
        return None

def obtener_articulos_inoreader(token, stream_id, count=20):
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(f'https://www.inoreader.com/reader/api/0/stream/contents/{stream_id}?n={count}', headers=headers)
    
    if response.status_code == 401:
        # Token expired, refresh token
        tokens = load_tokens()
        if tokens:
            new_token = refresh_token(client_id, client_secret, tokens['refresh_token'])
            if new_token:
                headers = {
                    'Authorization': f'Bearer {new_token}',
                }
                response = requests.get(f'https://www.inoreader.com/reader/api/0/stream/contents/{stream_id}?n={count}', headers=headers)
    
    if response.status_code != 200:
        print(f"Error al hacer la petición: {response.status_code}")
        print(f"Contenido de la respuesta: {response.text}")
        return []
    
    data = response.json()
    return data.get('items', [])

def extraer_encabezados(articulos, num_encabezados=20):
    if not articulos:
        return []

    encabezados = []
    for articulo in articulos[:num_encabezados]:
        titulo = articulo.get('title', 'Sin título')
        link = articulo.get('canonical', [{}])[0].get('href', 'Sin enlace')
        encabezados.append((titulo, link))
    
    return encabezados

def main():
    client_id = os.getenv('INOREADER_CLIENT_ID')
    client_secret = os.getenv('INOREADER_CLIENT_SECRET')
    redirect_uri = os.getenv('INOREADER_REDIRECT_URI')
    if not client_id or not client_secret or not redirect_uri:
        print("No se encontraron las credenciales necesarias en el archivo .env")
        return

    tokens = load_tokens()
    if tokens:
        token = tokens['access_token']
    else:
        code = obtener_codigo_autorizacion(client_id, redirect_uri)
        if not code:
            print("No se pudo obtener el código de autorización.")
            return
        
        token = obtener_token_acceso(client_id, client_secret, redirect_uri, code)
        if not token:
            print("No se pudo obtener el token de acceso.")
            return

    # Solicitar al usuario seleccionar una carpeta
    print("Selecciona una carpeta:")
    carpetas = {
        '1': 'user/-/label/Global',
        '2': 'user/-/label/Empresas',
        '3': 'user/-/label/Vulnerabilidades/Ataques',
        '4': 'user/-/label/IA',
        '5': 'user/-/label/Clientes',
        '6': 'user/-/label/España',
        '7': 'user/-/label/LATAM Ciber',
        '8': 'user/-/label/LATAM Global'
    }
    for key, value in carpetas.items():
        print(f"{key}: {value.split('/')[-1]}")
    seleccion = input("Introduce el número de la carpeta deseada: ")
    stream_id = carpetas.get(seleccion)

    if not stream_id:
        print("Selección inválida.")
        return

    filtro = input("Introduce las palabras clave para filtrar separadas por comas: ")
    filtrar_palabras = [palabra.strip() for palabra in filtro.split(",")]
    
    articulos = obtener_articulos_inoreader(token, stream_id)  
    if not articulos:
        print("No se pudieron obtener artículos.")
        return
    
    encabezados = extraer_encabezados(articulos)  
    
    if not encabezados:
        print("No se encontraron encabezados en los artículos.")
        return
      
    def filtrar_encabezados(encabezados):
        return [(texto, link) for texto, link in encabezados if any(palabra.lower() in texto.lower() for palabra in filtrar_palabras)]

    encabezados_filtrados = filtrar_encabezados(encabezados)
        
    if encabezados_filtrados:
        print(f"Se encontraron {len(encabezados_filtrados)} encabezados que contienen las palabras clave:")
        for texto, link in encabezados_filtrados:
            print(f"Título: {texto}\nLink: {link}\n")
    else: 
        print("No se encontraron encabezados")
        
if __name__ == "__main__":
    main()
