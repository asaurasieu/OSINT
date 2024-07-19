import requests 
from bs4 import BeautifulSoup
from urllib.parse import urljoin
def extraer_encabezados(url, num_encabezados=20): 
    respuesta = requests.get(url)
    
    if respuesta.status_code !=200:
        print(f"Error al hacer la petición: {respuesta.status_code}")
        return []
    
    sopa = BeautifulSoup(respuesta.text, "html.parser")
    
    encabezados = []
    for i in range(1,7): 
        encabezados.extend(sopa.find_all(f'h{i}'))
        
    textos_encabezados = []
    for encabezado in encabezados[:num_encabezados]: 
        texto = encabezado.get_text(strip=True)
        link = None 
        a_tag = encabezado.find("a")
        if a_tag and 'href' in a_tag.attrs: 
            link = a_tag['href']
            if not link.startswith("https://"): 
                link = urljoin(url, link)
        textos_encabezados.append((encabezado.name, texto, link))
        
    return textos_encabezados 


        
        
def main():
    url = input("Introduce la URL de la página web: ")
    filtro = input("Introduce las palabras clave para filtrar separadas por comas: ")
    filtrar_palabras = [palabra.strip() for palabra in filtro.split(",")]
    
    encabezados = extraer_encabezados(url)  
      
    def filtrar_encabezados(encabezados):
        return [(etiqueta, texto, link) for etiqueta, texto , link in encabezados if any(palabra.lower() in texto.lower() for palabra in filtrar_palabras)]

    encabezados_filtrados = filtrar_encabezados(encabezados)
        
    if encabezados_filtrados:
        print(f"Se encontraron {len(encabezados_filtrados)} encabezados que contienen las palabras clave:")
        for etiqueta, texto, link  in encabezados_filtrados: 
            print(f"{etiqueta}: {texto} - Link: {link if link else 'No Link'}")
    else: 
        print("No se encontraron encabezados")
        
if __name__ == "__main__":
    main()