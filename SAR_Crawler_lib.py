#! -*- encoding: utf8 -*-
import heapq as hq

from typing import Tuple, List, Optional, Dict, Union

import requests
import bs4
import re
from urllib.parse import urljoin
import json
import math
import os

class SAR_Wiki_Crawler:

    def __init__(self):
        # Expresión regular para detectar si es un enlace de la Wikipedia
        self.wiki_re = re.compile(r"(http(s)?:\/\/(es)\.wikipedia\.org)?\/wiki\/[\w\/_\(\)\%]+")
        # Expresión regular para limpiar anclas de editar
        self.edit_re = re.compile(r"\[(editar)\]")
        # Formato para cada nivel de sección
        self.section_format = {
            "h1": "##{}##",
            "h2": "=={}==",
            "h3": "--{}--"
        }

        # Expresiones regulares útiles para el parseo del documento
        self.title_sum_re = re.compile(r"##(?P<title>.+)##\n(?P<summary>((?!==.+==).+|\n)+)(?P<rest>(.+|\n)*)")
        self.sections_re = re.compile(r"==.+==\n")
        self.section_re = re.compile(r"==(?P<name>.+)==\n(?P<text>((?!--.+--).+|\n)*)(?P<rest>(.+|\n)*)")
        self.subsections_re = re.compile(r"--.+--\n")
        self.subsection_re = re.compile(r"--(?P<name>.+)--\n(?P<text>(.+|\n)*)")


    def is_valid_url(self, url: str) -> bool:
        """Verifica si es una dirección válida para indexar

        Args:
            url (str): Dirección a verificar

        Returns:
            bool: True si es valida, en caso contrario False
        """
        return self.wiki_re.fullmatch(url) is not None


    def get_wikipedia_entry_content(self, url: str) -> Optional[Tuple[str, List[str]]]:
        """Devuelve el texto en crudo y los enlaces de un artículo de la wikipedia

        Args:
            url (str): Enlace a un artículo de la Wikipedia

        Returns:
            Optional[Tuple[str, List[str]]]: Si es un enlace correcto a un artículo
                de la Wikipedia en inglés o castellano, devolverá el texto y los
                enlaces que contiene la página.

        Raises:
            ValueError: En caso de que no sea un enlace a un artículo de la Wikipedia
                en inglés o español
        """
        if not self.is_valid_url(url):
            raise ValueError((
                f"El enlace '{url}' no es un artículo de la Wikipedia en español"
            ))

        try:
            req = requests.get(url)
        except Exception as ex:
            print(f"ERROR: - {url} - {ex}")
            return None


        # Solo devolvemos el resultado si la petición ha sido correcta
        if req.status_code == 200:
            soup = bs4.BeautifulSoup(req.text, "lxml")
            urls = set()

            for ele in soup.select((
                'div#catlinks, div.printfooter, div.mw-authority-control'
            )):
                ele.decompose()

            # Recogemos todos los enlaces del contenido del artículo
            for a in soup.select("div#bodyContent a", href=True):
                href = a.get("href")
                if href is not None:
                    urls.add(href)

            # Contenido del artículo
            content = soup.select((
                "h1.firstHeading,"
                "div#mw-content-text h2,"
                "div#mw-content-text h3,"
                "div#mw-content-text h4,"
                "div#mw-content-text p,"
                "div#mw-content-text ul,"
                "div#mw-content-text li,"
                "div#mw-content-text span"
            ))

            dedup_content = []
            seen = set()

            for element in content:
                if element in seen:
                    continue

                dedup_content.append(element)

                # Añadimos a vistos, tanto el elemento como sus descendientes
                for desc in element.descendants:
                    seen.add(desc)

                seen.add(element)

            text = "\n".join(
                self.section_format.get(element.name, "{}").format(element.text)
                for element in dedup_content
            )

            # Eliminamos el texto de las anclas de editar
            text = self.edit_re.sub('', text)

            return text, sorted(list(urls))

        return None

    # Autor: Guillem
    def parse_wikipedia_textual_content(self, text: str, url: str) -> Optional[Dict[str, Union[str,List]]]:
        """Devuelve una estructura tipo artículo a partir del text en crudo

        Args:
            text (str): Texto en crudo del artículo de la Wikipedia
            url (str): url del artículo, para añadirlo como un campo

        Returns:

            Optional[Dict[str, Union[str,List[Dict[str,Union[str,List[str,str]]]]]]]:

            devuelve un diccionario con las claves 'url', 'title', 'summary', 'sections':
                Los valores asociados a 'url', 'title' y 'summary' son cadenas,
                el valor asociado a 'sections' es una lista de posibles secciones.
                    Cada sección es un diccionario con 'name', 'text' y 'subsections',
                        los valores asociados a 'name' y 'text' son cadenas y,
                        el valor asociado a 'subsections' es una lista de posibles subsecciones
                        en forma de diccionario con 'name' y 'text'.

            en caso de no encontrar título o resúmen del artículo, devolverá None

        """
        
        #si la url no es valida, devolvemos none
        if not self.is_valid_url(url):
            return None
        
        def clean_text(txt):
            return '\n'.join(l for l in txt.split('\n') if len(l) > 0)
        
        #creamos el documento a devolver
        document = {}
        
        #limpiamos el texto de líneas vacías
        text_cleaned = clean_text(text)
        
        #extraemos el título y el texto que acompaña al títutlo
        match_t_s = self.title_sum_re.match(text_cleaned)
        
        if match_t_s is None: return None
        
        
        #creamos la estructura general del documento y 
        #metemos la información que ya tenemos
        document['url'] = url
        document['title'] = match_t_s.group('title')
        document['summary'] = match_t_s.group('summary')
        document['sections'] = []
        
        #extraemos un iterador que contendrá los títulos de las secciones
        #y sus principios y finales
        sections = self.sections_re.finditer(text_cleaned)
        
        stop = False
        
        #extraemos la primera coincidencia del iterador
        try:
            section = next(sections)
        except:
            stop = True
        
        
        #mientras el iterador no dé error, continuamos
        while not stop:
            
            #creamos la nueva section
            new_section = {}
            
            #añadimos nombre
            new_section['name'] = self.section_re.search(section.group(0)).group('name')
            
            #almacenamos en "stop" si el iterador se ha quedado sin secciones, capturado 
            #el error que salta
            try:
                next_section = next(sections)
            except:
                stop = True
            
            #si no hay error, sacamos el texto entre secciones, que va desde el final de la seccion que tratamos
            #hasta el principio de la siguiente, si hay error, el texto va desde el final de la sección, hasta el 
            #el final del texto    
            if not stop:
                text = text_cleaned[section.end():next_section.start()].rstrip('\n')    
                
                section = next_section
            else:    
                text = text_cleaned[section.end():].rstrip('\n') 
                
            new_section['text'] = ""
            new_section['subsections'] = []

            #extraemos un iterador que contendrá los títulos de las subsecciones
            #y sus principios y finales
            subsections = self.subsections_re.finditer(text)
            
            is_subsections = True
            
            #extraemos la primera coincidencia del iterador, puede que no haya subsecciones,
            #guardamos en un booleano si hay o no capturando la excepción
            try:  
                subsection = next(subsections)
            except:
                is_subsections = False
            
            #si hay subsecciones, hacemos lo siguiente
            if is_subsections:
                substop = False
                
                #guardamos el texto en otra variable, para poder extraer los indices de las subsecciones correctamente
                #esto es necesario porque a continuación, actualizaremos el texto para guardarlos en la seccion
                sub_text = text
                #actualizamos el texto de la sección, quitando las subsecciones
                text = text[:subsection.start()]
                
                #mientras el iterador no dé error, continuamos
                while not substop:
            
                    #creamos la nueva subsection
                    new_subsection = {}
                
                    #añadimos nombre
                    new_subsection['name'] = self.subsection_re.search(subsection.group(0)).group('name')
            
                    #almacenamos en "substop" si el iterador se ha quedado sin subsecciones, capturado 
                    #el error que salta
                    try:
                        next_subsection = next(subsections)
                    except:
                        substop = True
            
                    #si no hay error, sacamos el texto entre subsecciones, que va desde el final de la subseccion que tratamos
                    #hasta el principio de la siguiente, si hay error, el texto va desde el final de la subsección, hasta el 
                    #el final del texto    
                    if not substop:
                        subtext = sub_text[subsection.end():next_subsection.start()].rstrip('\n')    
                        subsection = next_subsection
                    else:    
                        subtext = sub_text[subsection.end():].rstrip('\n') 
                
                    new_subsection['text'] = subtext
                    
                    new_section['subsections'].append(new_subsection)
                
            new_section['text'] = text
            document['sections'].append(new_section)

        return document
            
            
    def save_documents(self,
        documents: List[dict], base_filename: str,
        num_file: Optional[int] = None, total_files: Optional[int] = None
    ):
        """Guarda una lista de documentos (text, url) en un fichero tipo json lines
        (.json). El nombre del fichero se autogenera en base al base_filename,
        el num_file y total_files. Si num_file o total_files es None, entonces el
        fichero de salida es el base_filename.

        Args:
            documents (List[dict]): Lista de documentos.
            base_filename (str): Nombre base del fichero de guardado.
            num_file (Optional[int], optional):
                Posición numérica del fichero a escribir. (None por defecto)
            total_files (Optional[int], optional):
                Cantidad de ficheros que se espera escribir. (None por defecto)
        """
        assert base_filename.endswith(".json")

        if num_file is not None and total_files is not None:
            # Separamos el nombre del fichero y la extensión
            base, ext = os.path.splitext(base_filename)
            # Padding que vamos a tener en los números
            padding = len(str(total_files))

            out_filename = f"{base}_{num_file:0{padding}d}_{total_files}{ext}"

        else:
            out_filename = base_filename

        with open(out_filename, "w", encoding="utf-8", newline="\n") as ofile:
            for doc in documents:
                print(json.dumps(doc, ensure_ascii=True), file=ofile)

    #Autor: Jose
    def start_crawling(self, 
                    initial_urls: List[str], document_limit: int,
                    base_filename: str, batch_size: Optional[int], max_depth_level: int,
                    ):        
         

        """Comienza la captura de entradas de la Wikipedia a partir de una lista de urls válidas, 
            termina cuando no hay urls en la cola o llega al máximo de documentos a capturar.
        
        Args:
            initial_urls: Direcciones a artículos de la Wikipedia
            document_limit (int): Máximo número de documentos a capturar
            base_filename (str): Nombre base del fichero de guardado.
            batch_size (Optional[int]): Cada cuantos documentos se guardan en
                fichero. Si se asigna None, se guardará al finalizar la captura.
            max_depth_level (int): Profundidad máxima de captura.
        """

        # URLs válidas, ya visitadas (se hayan procesado, o no, correctamente)
        visited = set()
        # URLs en cola
        to_process = set(initial_urls)
        # Direcciones a visitar
        queue = [(0, "", url) for url in to_process]
        hq.heapify(queue)
        # Buffer de documentos capturados
        documents: List[dict] = []
        # Contador del número de documentos capturados
        total_documents_captured = 0
        # Contador del número de ficheros escritos
        files_count = 0

        # En caso de que no utilicemos bach_size, asignamos None a total_files
        # así el guardado no modificará el nombre del fichero base
        if batch_size is None:
            total_files = None
        else:
            # Suponemos que vamos a poder alcanzar el límite para la nomenclatura
            # de guardado
            total_files = math.ceil(document_limit / batch_size)

        # COMPLETAR
        """
        El funcionamiento basico debe ser:
            1. Seleccionar una pagina no procesada de la cola de prioridad.

            2. Descarga el contenido textual de la pagina y los enlaces que aparecen en ella.

            3. Añadir, si procede, los enlaces a la cola de paginas pendientes de procesar.

            4. Analizar el contenido textual para generar el diccionario con el contenido estructurado
                del articulo
        """
        while (len(queue) > 0) and (total_documents_captured < document_limit):
            actual = hq.heappop(queue)  #Seleccionar una pagina de la cola
            actualURL = actual[2]
            if visited.intersection([actualURL]):
                continue        #Si ya ha sido visitada salta a la siguiente url en cola
                                #evita casos de ir al mismo documento C desde 2 documentos (A y B) sin procesar C antre medias
            
            profundidad = actual[0]
            visited.add(actualURL)
            content = self.get_wikipedia_entry_content(actualURL)   #Descarga el contenido raw
            if(content is None):
                continue    #Si content es None salta a la proxima URL
            rawText,urls = content   #Desempaca el content
            textual = self.parse_wikipedia_textual_content(rawText,actualURL)    #Descarga el contenido textual y los enlaces
            if textual is None:     #guarda de contenido nulo
                continue    #siguiente bucle de while
            documents.append(textual)   #guarda en el buffer
            total_documents_captured += 1   #incrementa los documentos capturados

            if (batch_size is not None) and (len(documents) == batch_size):    #guarda el buffer si esta "lleno"
                files_count+=1
                self.save_documents(documents,base_filename,files_count,total_files)
                documents.clear()   #vacia el buffer tras guardar

            for futureURL in urls:
                absoluteURL = urljoin(actualURL,futureURL)
                if profundidad == max_depth_level: 
                    break      #Si ya ha alcanzado maxima profundidad no añadas nada
                if not self.is_valid_url(absoluteURL):
                    continue      #Si URL NO valida salta a la siguiente url
                if to_process.intersection([absoluteURL]) or visited.intersection([absoluteURL]): 
                    continue      #Si ya ha sido visitada salta a la siguiente url
                to_process.add(absoluteURL)
                hq.heappush(queue,(profundidad + 1, actualURL, absoluteURL))

        if len(documents) != 0:    #guarda el buffer si "tiene algo"
            files_count+=1
            self.save_documents(documents,base_filename,files_count,total_files)
            documents.clear()   #vacia el buffer tras guardar


    def wikipedia_crawling_from_url(self,
        initial_url: str, document_limit: int, base_filename: str,
        batch_size: Optional[int], max_depth_level: int
    ):
        """Captura un conjunto de entradas de la Wikipedia, hasta terminar
        o llegar al máximo de documentos a capturar.
        
        Args:
            initial_url (str): Dirección a un artículo de la Wikipedia
            document_limit (int): Máximo número de documentos a capturar
            base_filename (str): Nombre base del fichero de guardado.
            batch_size (Optional[int]): Cada cuantos documentos se guardan en
                fichero. Si se asigna None, se guardará al finalizar la captura.
            max_depth_level (int): Profundidad máxima de captura.
        """
        if not self.is_valid_url(initial_url) and not initial_url.startswith("/wiki/"):
            raise ValueError(
                "Es necesario partir de un artículo de la Wikipedia en español"
            )

        self.start_crawling(initial_urls=[initial_url], document_limit=document_limit, base_filename=base_filename,
                            batch_size=batch_size, max_depth_level=max_depth_level)



    def wikipedia_crawling_from_url_list(self,
        urls_filename: str, document_limit: int, base_filename: str,
        batch_size: Optional[int]
    ):
        """A partir de un fichero de direcciones, captura todas aquellas que sean
        artículos de la Wikipedia válidos

        Args:
            urls_filename (str): Lista de direcciones
            document_limit (int): Límite máximo de documentos a capturar
            base_filename (str): Nombre base del fichero de guardado.
            batch_size (Optional[int]): Cada cuantos documentos se guardan en
                fichero. Si se asigna None, se guardará al finalizar la captura.

        """

        urls = []
        with open(urls_filename, "r", encoding="utf-8") as ifile:
            for url in ifile:
                url = url.strip()

                # Comprobamos si es una dirección a un artículo de la Wikipedia
                if self.is_valid_url(url):
                    if not url.startswith("http"):
                        raise ValueError(
                            "El fichero debe contener URLs absolutas"
                        )

                    urls.append(url)

        urls = list(set(urls)) # eliminamos posibles duplicados

        self.start_crawling(initial_urls=urls, document_limit=document_limit, base_filename=base_filename,
                            batch_size=batch_size, max_depth_level=0)





if __name__ == "__main__":
    raise Exception(
        "Esto es una librería y no se puede usar como fichero ejecutable"
    )
