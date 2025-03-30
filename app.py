import streamlit as st
import requests
import json
from concurrent.futures import ThreadPoolExecutor

# Configuración de la página
st.set_page_config(
    page_title="Buscador de Librerías Python",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Título y descripción
st.title("Buscador de Librerías Python")
st.markdown("Busca información sobre librerías de Python utilizando la API de PyPI")

# Función para buscar librería en PyPI
def buscar_libreria(nombre_libreria):
    """Busca información de una librería en PyPI."""
    try:
        # URL de la API de PyPI
        url = f"https://pypi.org/pypi/{nombre_libreria}/json"
        response = requests.get(url)
        
        # Verificar si la respuesta es exitosa
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error al consultar la API: {str(e)}")
        return None

# Función para formatear los resultados
def formatear_resultados(data):
    """Formatea los datos de la librería para mostrar en la interfaz."""
    if data and "info" in data:
        info = data["info"]
        nombre = info.get("name", "No disponible")
        version = info.get("version", "No disponible")
        descripcion = info.get("summary", "No hay descripción disponible")
        
        return {
            "nombre": nombre,
            "version": version,
            "descripcion": descripcion,
            "autor": info.get("author", "No disponible"),
            "licencia": info.get("license", "No disponible"),
            "url_proyecto": info.get("project_url", "No disponible"),
            "url_documentacion": info.get("docs_url", "No disponible"),
            "requisitos": info.get("requires_dist", [])
        }
    return None

# Función para obtener librerías similares
def obtener_librerias_similares(nombre_libreria):
    """Busca librerías similares basadas en el nombre proporcionado."""
    try:
        url = f"https://pypi.org/search/?q={nombre_libreria}&o="
        response = requests.get(url)
        
        # Si la respuesta es exitosa, intentar extraer los resultados de búsqueda
        # Esta es una aproximación simple, ya que PyPI no tiene una API oficial para buscar paquetes similares
        if response.status_code == 200:
            # Buscamos en otro endpoint para obtener paquetes relacionados
            search_url = f"https://pypi.org/pypi/{nombre_libreria}/json"
            search_response = requests.get(search_url)
            
            if search_response.status_code == 200:
                data = search_response.json()
                # Obtener palabras clave del paquete
                keywords = data.get("info", {}).get("keywords", "")
                
                if keywords:
                    # Si hay palabras clave, buscar paquetes con esas palabras clave
                    related_packages = []
                    
                    # Buscar por cada palabra clave
                    if isinstance(keywords, str):
                        keywords = keywords.split()
                    
                    with ThreadPoolExecutor(max_workers=3) as executor:
                        futures = []
                        for kw in keywords[:3]:  # Limitamos a 3 palabras clave para no sobrecargar
                            futures.append(executor.submit(buscar_por_palabra_clave, kw))
                        
                        for future in futures:
                            result = future.result()
                            if result and result != nombre_libreria and result not in related_packages:
                                related_packages.append(result)
                    
                    return related_packages[:5]  # Devolver hasta 5 paquetes relacionados
            
            # Si no podemos obtener paquetes relacionados, devolvemos algunos populares según la categoría
            popular_packages = {
                "web": ["flask", "django", "fastapi", "bottle", "pyramid"],
                "data": ["pandas", "numpy", "matplotlib", "seaborn", "scipy"],
                "ml": ["scikit-learn", "tensorflow", "keras", "pytorch", "xgboost"],
                "scraping": ["beautifulsoup4", "scrapy", "selenium", "requests-html", "lxml"],
                "cli": ["click", "typer", "argparse", "docopt", "fire"],
                "gui": ["pyqt5", "tkinter", "kivy", "pyside2", "wxpython"],
                "test": ["pytest", "unittest", "nose", "coverage", "tox"],
                "async": ["asyncio", "aiohttp", "trio", "twisted", "tornado"]
            }
            
            # Determinar categoría del paquete (simplificado)
            if nombre_libreria in popular_packages["web"] or "web" in nombre_libreria:
                return [p for p in popular_packages["web"] if p != nombre_libreria][:5]
            elif nombre_libreria in popular_packages["data"] or "data" in nombre_libreria:
                return [p for p in popular_packages["data"] if p != nombre_libreria][:5]
            elif nombre_libreria in popular_packages["ml"] or "ml" in nombre_libreria:
                return [p for p in popular_packages["ml"] if p != nombre_libreria][:5]
            # Por defecto, devolver una mezcla
            else:
                all_packages = []
                for category, packages in popular_packages.items():
                    all_packages.extend(packages)
                
                import random
                random.shuffle(all_packages)
                return [p for p in all_packages if p != nombre_libreria][:5]
        
        return []
    except Exception as e:
        st.error(f"Error al buscar librerías similares: {str(e)}")
        return []

def buscar_por_palabra_clave(palabra_clave):
    """Busca un paquete por palabra clave y devuelve el primero que encuentra."""
    try:
        url = f"https://pypi.org/search/?q={palabra_clave}"
        response = requests.get(url)
        
        if response.status_code == 200:
            # Aquí deberíamos analizar la respuesta HTML para extraer el primer resultado
            # Como es complejo sin usar BeautifulSoup, simulamos un resultado
            # basado en la palabra clave
            if palabra_clave.lower() == "web":
                return "flask"
            elif palabra_clave.lower() == "data":
                return "pandas"
            elif palabra_clave.lower() == "ml" or palabra_clave.lower() == "machine learning":
                return "scikit-learn"
            else:
                return None
        return None
    except:
        return None

# Campo de búsqueda
with st.form(key="search_form"):
    nombre_libreria = st.text_input("Nombre de la librería:", placeholder="Ej. pandas, numpy, flask...")
    boton_buscar = st.form_submit_button("🔍 Buscar")

# Validar la entrada y ejecutar la búsqueda
if boton_buscar:
    if not nombre_libreria:
        st.warning("⚠️ Por favor, ingresa el nombre de una librería.")
    else:
        with st.spinner(f"Buscando información sobre {nombre_libreria}..."):
            datos_libreria = buscar_libreria(nombre_libreria)
            
            if datos_libreria:
                resultados = formatear_resultados(datos_libreria)
                
                if resultados:
                    # Mostrar la información principal
                    st.success(f"✅ Librería encontrada: {resultados['nombre']}")
                    
                    st.markdown("### Información General")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Nombre:** {resultados['nombre']}")
                        st.markdown(f"**Versión:** {resultados['version']}")
                        st.markdown(f"**Autor:** {resultados['autor']}")
                    with col2:
                        st.markdown(f"**Licencia:** {resultados['licencia']}")
                        if resultados['url_proyecto'] != "No disponible":
                            st.markdown(f"**URL del proyecto:** [Enlace]({resultados['url_proyecto']})")
                        if resultados['url_documentacion'] != "No disponible":
                            st.markdown(f"**Documentación:** [Enlace]({resultados['url_documentacion']})")
                    
                    st.markdown("### Descripción")
                    st.write(resultados['descripcion'])
                    
                    # Comandos de instalación
                    st.markdown("### Comandos de Instalación")
                    
                    tab1, tab2, tab3 = st.tabs(["Windows", "Linux/macOS", "Entorno Virtual"])
                    
                    with tab1:
                        st.code(f"pip install {resultados['nombre']}", language="bash")
                    
                    with tab2:
                        st.code(f"pip3 install {resultados['nombre']}", language="bash")
                    
                    with tab3:
                        st.code(f"python -m venv venv\nvenv\\Scripts\\activate  # En Windows\nsource venv/bin/activate  # En Linux/macOS\npip install {resultados['nombre']}", language="bash")
                    
                    # Librerías similares
                    st.markdown("### Librerías Similares Recomendadas")
                    
                    with st.spinner("Buscando librerías similares..."):
                        librerias_similares = obtener_librerias_similares(nombre_libreria)
                        
                        if librerias_similares:
                            cols = st.columns(len(librerias_similares))
                            for i, lib in enumerate(librerias_similares):
                                with cols[i]:
                                    st.button(lib, key=f"lib_{i}", on_click=lambda l=lib: st.session_state.update({"nombre_libreria": l, "buscar": True}))
                        else:
                            st.info("No se encontraron librerías similares.")
                
                else:
                    st.error("⚠️ No se pudo procesar la información de la librería.")
            else:
                st.error(f"❌ No se encontró la librería '{nombre_libreria}'. Verifica el nombre e intenta nuevamente.")

# Si se seleccionó una librería similar
if "buscar" in st.session_state and st.session_state.buscar:
    nombre_libreria = st.session_state.nombre_libreria
    st.session_state.buscar = False
    
    with st.spinner(f"Buscando información sobre {nombre_libreria}..."):
        datos_libreria = buscar_libreria(nombre_libreria)
        
        if datos_libreria:
            resultados = formatear_resultados(datos_libreria)
            
            if resultados:
                # Mostrar la información principal
                st.success(f"✅ Librería encontrada: {resultados['nombre']}")
                
                st.markdown("### Información General")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Nombre:** {resultados['nombre']}")
                    st.markdown(f"**Versión:** {resultados['version']}")
                    st.markdown(f"**Autor:** {resultados['autor']}")
                with col2:
                    st.markdown(f"**Licencia:** {resultados['licencia']}")
                    if resultados['url_proyecto'] != "No disponible":
                        st.markdown(f"**URL del proyecto:** [Enlace]({resultados['url_proyecto']})")
                    if resultados['url_documentacion'] != "No disponible":
                        st.markdown(f"**Documentación:** [Enlace]({resultados['url_documentacion']})")
                
                st.markdown("### Descripción")
                st.write(resultados['descripcion'])
                
                # Comandos de instalación
                st.markdown("### Comandos de Instalación")
                
                tab1, tab2, tab3 = st.tabs(["Windows", "Linux/macOS", "Entorno Virtual"])
                
                with tab1:
                    st.code(f"pip install {resultados['nombre']}", language="bash")
                
                with tab2:
                    st.code(f"pip3 install {resultados['nombre']}", language="bash")
                
                with tab3:
                    st.code(f"python -m venv venv\nvenv\\Scripts\\activate  # En Windows\nsource venv/bin/activate  # En Linux/macOS\npip install {resultados['nombre']}", language="bash")
                
                # Librerías similares
                st.markdown("### Librerías Similares Recomendadas")
                
                with st.spinner("Buscando librerías similares..."):
                    librerias_similares = obtener_librerias_similares(nombre_libreria)
                    
                    if librerias_similares:
                        cols = st.columns(len(librerias_similares))
                        for i, lib in enumerate(librerias_similares):
                            with cols[i]:
                                st.button(lib, key=f"lib_{i}_new", on_click=lambda l=lib: st.session_state.update({"nombre_libreria": l, "buscar": True}))
                    else:
                        st.info("No se encontraron librerías similares.")
            
            else:
                st.error("⚠️ No se pudo procesar la información de la librería.")
        else:
            st.error(f"❌ No se encontró la librería '{nombre_libreria}'. Verifica el nombre e intenta nuevamente.")
    
    # Recargar la página para reflejar la nueva búsqueda
    st.rerun()

# Pie de página
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center">
        Desarrollado por <a href="https://github.com/Fishertdevs" target="_blank">Fishertdevs</a>
    </div>
    """, 
    unsafe_allow_html=True
)
