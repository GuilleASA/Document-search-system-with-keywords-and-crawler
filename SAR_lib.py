import json
from nltk.stem.snowball import SnowballStemmer
import os
import re
import sys
import math
from pathlib import Path
from typing import Optional, List, Union, Dict
import pickle

class SAR_Indexer:
    """
    Prototipo de la clase para realizar la indexacion y la recuperacion de artículos de Wikipedia
        
        Preparada para todas las ampliaciones:
          parentesis + multiples indices + posicionales + stemming + permuterm

    Se deben completar los metodos que se indica.
    Se pueden añadir nuevas variables y nuevos metodos
    Los metodos que se añadan se deberan documentar en el codigo y explicar en la memoria
    """

    # lista de campos, el booleano indica si se debe tokenizar el campo
    # NECESARIO PARA LA AMPLIACION MULTIFIELD
    fields = [
        ("all", True), ("title", True), ("summary", True), ("section-name", True), ('url', False),
    ]
    def_field = 'all'
    PAR_MARK = '%'
    # numero maximo de documento a mostrar cuando self.show_all es False
    SHOW_MAX = 10

    all_atribs = ['urls', 'index', 'sindex', 'ptindex', 'docs', 'weight', 'articles',
                  'tokenizer', 'stemmer', 'show_all', 'use_stemming']

    def __init__(self):
        """
        Constructor de la classe SAR_Indexer.
        NECESARIO PARA LA VERSION MINIMA

        Incluye todas las variables necesaria para todas las ampliaciones.
        Puedes añadir más variables si las necesitas 

        """
        self.urls = set() # hash para las urls procesadas,
        self.index = {} # hash para el indice invertido de terminos --> clave: termino, valor: posting list
        self.sindex = {} # hash para el indice invertido de stems --> clave: stem, valor: lista con los terminos que tienen ese stem
        self.ptindex = {} # hash para el indice permuterm.
        self.docs = {} # diccionario de terminos --> clave: entero(docid),  valor: ruta del fichero.
        self.weight = {} # hash de terminos para el pesado, ranking de resultados.
        self.articles = {} # hash de articulos --> clave entero (artid), valor: la info necesaria para diferencia los artículos dentro de su fichero
        self.tokenizer = re.compile("\W+") # expresion regular para hacer la tokenizacion
        self.stemmer = SnowballStemmer('spanish') # stemmer en castellano
        self.show_all = False # valor por defecto, se cambia con self.set_showall()
        self.show_snippet = False # valor por defecto, se cambia con self.set_snippet()
        self.use_stemming = False # valor por defecto, se cambia con self.set_stemming()
        self.use_ranking = False  # valor por defecto, se cambia con self.set_ranking()


    ###############################
    ###                         ###
    ###      CONFIGURACION      ###
    ###                         ###
    ###############################


    def set_showall(self, v:bool):
        """

        Cambia el modo de mostrar los resultados.
        
        input: "v" booleano.

        UTIL PARA TODAS LAS VERSIONES

        si self.show_all es True se mostraran todos los resultados el lugar de un maximo de self.SHOW_MAX, no aplicable a la opcion -C

        """
        self.show_all = v


    def set_snippet(self, v:bool):
        """

        Cambia el modo de mostrar snippet.
        
        input: "v" booleano.

        UTIL PARA TODAS LAS VERSIONES

        si self.show_snippet es True se mostrara un snippet de cada noticia, no aplicable a la opcion -C

        """
        self.show_snippet = v


    def set_stemming(self, v:bool):
        """

        Cambia el modo de stemming por defecto.
        
        input: "v" booleano.

        UTIL PARA LA VERSION CON STEMMING

        si self.use_stemming es True las consultas se resolveran aplicando stemming por defecto.

        """
        self.use_stemming = v



    #############################################
    ###                                       ###
    ###      CARGA Y GUARDADO DEL INDICE      ###
    ###                                       ###
    #############################################


    def save_info(self, filename:str):
        """
        Guarda la información del índice en un fichero en formato binario
        
        """
        info = [self.all_atribs] + [getattr(self, atr) for atr in self.all_atribs]
        with open(filename, 'wb') as fh:
            pickle.dump(info, fh)

    def load_info(self, filename:str):
        """
        Carga la información del índice desde un fichero en formato binario
        
        """
        #info = [self.all_atribs] + [getattr(self, atr) for atr in self.all_atribs]
        with open(filename, 'rb') as fh:
            info = pickle.load(fh)
        atrs = info[0]
        for name, val in zip(atrs, info[1:]):
            setattr(self, name, val)

    ###############################
    ###                         ###
    ###   PARTE 1: INDEXACION   ###
    ###                         ###
    ###############################

    def already_in_index(self, article:Dict) -> bool:
        """

        Args:
            article (Dict): diccionario con la información de un artículo

        Returns:
            bool: True si el artículo ya está indexado, False en caso contrario
        """
        return article['url'] in self.urls

    #Autor: Ruben
    def index_dir(self, root:str, **args):
        """
        
        Recorre recursivamente el directorio o fichero "root" 
        NECESARIO PARA TODAS LAS VERSIONES
        
        Recorre recursivamente el directorio "root"  y indexa su contenido
        los argumentos adicionales "**args" solo son necesarios para las funcionalidades ampliadas

        """
        self.multifield = args['multifield']
        self.positional = args['positional']
        self.stemming = args['stem']
        self.permuterm = args['permuterm']

        #Coprobamos si tenemos multifield
        if self.multifield:
            #En caso de tenerlo inicializamos todos los diccionarios
            for campo,_ in self.fields:
                self.index[campo]={}
        else:
            #Si no tenemos mulifield solo inicializamos all
            self.index["all"] = {}

        file_or_dir = Path(root)
        
        if file_or_dir.is_file():
            # is a file
            self.index_file(root)
        elif file_or_dir.is_dir():
            # is a directory

            for d, _, files in os.walk(root):
                for filename in sorted(files):
                    if filename.endswith('.json'):
                        fullname = os.path.join(d, filename)
                        self.index_file(fullname)
        else:
            print(f"ERROR:{root} is not a file nor directory!", file=sys.stderr)
            sys.exit(-1)

        ##########################################
        ## COMPLETAR PARA FUNCIONALIDADES EXTRA ##
        ##########################################

        #Al usar sets para la eliminacion de duplicados es necesario pasar los sets a listas
        #Habrá también que ordenarlas para poder realizar correctamente las operaciones de OR, AND y NOT (los sets no guardan el orden de insercion)
        #Solo se hará si se usan posicionales, en cuyo caso los repetidos se evitan de otra forma
        if not self.positional:
            for term in (self.index["all"].keys()):
                self.index["all"][term] = sorted(list(self.index["all"][term]))

        #Si es necesario hacer stemming se realiza
        if self.stemming:
            self.make_stemming()

        #Miramos si es necesario realizar permuterm, en cuyo caso llamamos a make_permuterm
        if self.permuterm:
            self.make_permuterm()
        
        
    def parse_article(self, raw_line:str) -> Dict[str, str]:
        """
        Crea un diccionario a partir de una linea que representa un artículo del crawler

        Args:
            raw_line: una linea del fichero generado por el crawler

        Returns:
            Dict[str, str]: claves: 'url', 'title', 'summary', 'all', 'section-name'
        """
        
        article = json.loads(raw_line)
        sec_names = []
        txt_secs = ''
        for sec in article['sections']:
            txt_secs += sec['name'] + '\n' + sec['text'] + '\n'
            txt_secs += '\n'.join(subsec['name'] + '\n' + subsec['text'] + '\n' for subsec in sec['subsections']) + '\n\n'
            sec_names.append(sec['name'])
            sec_names.extend(subsec['name'] for subsec in sec['subsections'])
        article.pop('sections') # no la necesitamos 
        article['all'] = article['title'] + '\n\n' + article['summary'] + '\n\n' + txt_secs
        article['section-name'] = '\n'.join(sec_names)

        return article
                
    
    #Autor: Ruben
    def index_file(self, filename:str):
        """

        Indexa el contenido de un fichero.
        
        input: "filename" es el nombre de un fichero generado por el Crawler cada línea es un objeto json
            con la información de un artículo de la Wikipedia

        NECESARIO PARA TODAS LAS VERSIONES

        dependiendo del valor de self.multifield y self.positional se debe ampliar el indexado

        """
        #Insertamos el documento nuevo
        docActual = len(self.docs)
        self.docs[docActual] = filename

        #Evita comprobaciones en cada iter del for
        if self.positional:
            indexador = self.index_line_positional
        else:
            indexador = self.index_line

        for i, line in enumerate(open(filename)):
            j = self.parse_article(line)
            # 
            # En la version basica solo se debe indexar el contenido "article"
            #
            #################
            ### COMPLETAR ###
            #################

            # Comprobacion de que no se ha procesado la url
            if self.already_in_index(j): continue
            
            #la anyadimos en caso de no haberla procesado
            self.urls.add(j["url"])

            #Obtenemos el id del articulo
            id = len(self.urls)
            #Anyadimos el articulo nuevo encontrado, con el docId, y la linea de ese docId donde esta
            self.articles[id] = (docActual,i)
            #Coprobamos si la busqueda ha de ser por multifield
            if self.multifield:
                #En caso de serlo llamaremos a index multifield, indicandole el id del documento, la linea actual y el indexador con el que debe realizar la indexacion
                self.index_multifield(id,j,indexador)
            else:
                #En caso de no ser multifield solo indexamos el apartado de all
                indexador(id,j["all"],"all",True)

    #Autor: Ruben
    def index_line(self,id,texto,indice,tockenizar):
        """
        Indexa un articulo en el indice invertido con indices posicionales de los terminos.
        
        id: Id del articulo que se indexa
        texto: String que se va a indexar
        indice: diccionario del indice invertido donde almacenar el resultado
        tockenizar: bool que indica si el texto pasado se ha de tockenizar o no

        """
        #Miramos si hay que tockenizar el texto
        if tockenizar:
            #Lo tockenizamos, es decir separamos las palabras y tockenizamos las palabras
            texto = self.tokenize(texto)
        else:
            texto = [texto]
            
        
        #Recorremos los tocken
        for word in texto:
            try:
                #Intentamos anyadir el id a la posting list del tocken
                self.index[indice][word].add(id)
            except KeyError:
                #En caso de no haberse encontrado antes el tocken se crea la lista nueva
                self.index[indice][word] = {id}
    
    #Autor: Ruben
    def index_line_positional(self,id,texto,indice,tockenizar):
        """
        Indexa un articulo en el indice invertido con indices posicionales de los terminos.
        
        id: Id del articulo que se indexa
        texto: String que se va a indexar
        indice: diccionario del indice invertido donde almacenar el resultado
        tockenizar: bool que indica si el texto pasado se ha de tockenizar o no

        """
        #Miramos si hay que tockenizar el texto
        if tockenizar:
            #Lo tockenizamos
            texto = self.tokenize(texto)
        else:
            texto = [texto]
        # creamos una variable pos -> contador que nos indicará la posición en la que ha aparecido el token:
        pos = 0
        #Recorremos los tocken,quitamos todos los caracteres que no sean alfanumeros
        for word in texto:
            try:
                #Comprobamos si el articulo ya esta en la posting list y si el termino esta en el indice
                if id in (l:=self.index[indice][word]).keys():
                    #Si esta anyadimos al articulo la posicion
                    l[id].append(pos)
                else:
                    #En caso de que este el termino, pero no este el id
                    self.index[indice][word][id] = [pos]
            except KeyError:
                #En caso de no estar el termino lo anyadimos con la posicion
                self.index[indice][word] = {id:[pos]}
            #Incrementamos el contador de la posicion
            pos+=1
        

    #Autor: Ruben
    def index_multifield(self,id,line,indexador):
        """
        Indexa un articulo en el indice invertido con multifield.

        id: Id del articulo que se indexa
        line: Diccionario con todos los apartados a indexar
        indexador: Funcion que se usara para indexar cada uno de los campos

        """
        #Recorremos los campos existentes en los articulos
        for campo,tockenizar in self.fields:
            #Indexamos el campo con el indexador indicado
            indexador(id,line[campo],campo,tockenizar)

            


    def set_stemming(self, v:bool):
        """

        Cambia el modo de stemming por defecto.
        
        input: "v" booleano.

        UTIL PARA LA VERSION CON STEMMING

        si self.use_stemming es True las consultas se resolveran aplicando stemming por defecto.

        """
        self.use_stemming = v


    def tokenize(self, text:str):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Tokeniza la cadena "texto" eliminando simbolos no alfanumericos y dividientola por espacios.
        Puedes utilizar la expresion regular 'self.tokenizer'.

        params: 'text': texto a tokenizar

        return: lista de tokens

        """
        return self.tokenizer.sub(' ', text.lower()).split()

    #Autor: Ruben
    def make_stemming(self):
        """

        Crea el indice de stemming (self.sindex) para los terminos de todos los indices.

        NECESARIO PARA LA AMPLIACION DE STEMMING.

        "self.stemmer.stem(token) devuelve el stem del token"


        """
        ####################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE STEMMING ##
        ####################################################

        #Recorremos todos los campos de index, en caso de Multifield tendremos varios, en caso contrario solo tendremos "all"
        for dic in self.index.keys():
            #Inicializamos un diccionario donde guardaremos todas las raices con sus terminos
            self.sindex[dic]={}
            #Recorremos todos los terminos almacenados
            for term in (self.index[dic].keys()):
                #Obtenemos la raiz
                raiz = self.stemmer.stem(term)
                try:
                    #Intentamos anyadir el termino a la raiz correspondiente
                    self.sindex[dic][raiz].add(term)
                except KeyError:
                    #En caso de no haberse encontrado antes el tocken se crea un set con los terminos para evitar repetidos
                    self.sindex[dic][raiz] = {term}

    #Autor: Jose
    def make_permuterm(self):
        """

        Crea el indice permuterm (self.ptindex) para los terminos de todos los indices.

        NECESARIO PARA LA AMPLIACION DE PERMUTERM


        """
        #####################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE PERMUTERM ##
        #####################################################
        """
        indexacion multiple
        self.ptindex = {indice (all): 
                            [(Ptermino ,Termino)]}
                            
        1.Recorrer cada indice (los generados cuando multifile)
        1.2 Genera la lista vacia
            2.Recorrer todos los terminos de cada indice multifile
                3.Cada termino generar sus permuterms
                4.Guardar cada permuterm con su termino (tupla en ptindex[indice])
            5.Ordenar ptindex[indice]
            
        indexacion unica
        1.Recorrer todos los terminos de self.index.keys
            2.Cada termino generar sus permuterms
            3.Guardar cada permuterm con su termino (tupla en ptindex["all"])
        4.Ordenar ptindex["all"]
        """
        if self.multifield:
            #En caso de tenerlo inicializamos todos los diccionarios
            for campo,_ in self.fields:                         #(indexacion multiple) 1
                self.ptindex[campo] = []                            #(indexacion multiple) 1.2
                for term in self.index[campo].keys():               #(indexacion multiple) 2
                    for i in range(0,len(term)+1):
                        pterm = f'{term[i:]}${term[0:i]}'           #(indexacion multiple) 3
                        self.ptindex[campo].append((pterm,term))    #(indexacion multiple) 4
                self.ptindex[campo].sort()                          #(indexacion multiple) 5
        else:
            self.ptindex["all"] = []
            for term in self.index["all"].keys():               #(indexacion unica) 1
                for i in range(0,len(term)+1):
                    pterm = f'{term[i:]}${term[0:i]}'           #(indexacion unica) 2
                    self.ptindex["all"].append((pterm,term))    #(indexacion unica) 3
            self.ptindex["all"].sort()   



    #Autor: Ruben
    def show_stats(self):
        """
        NECESARIO PARA TODAS LAS VERSIONES
        
        Muestra estadisticas de los indices
        
        """
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################
        #Imprimimos las stats resultantes al indexar
        print("========================================")
        print("Number of indexed files:",len(self.docs))
        print("----------------------------------------")
        print("Number of indexed articles:",len(self.urls))
        print("----------------------------------------")
        if self.multifield:
            print("TOKENS:")
            for campo,_ in self.fields:
                    print(f"\t#of tokens in '{campo}': {len(self.index[campo].keys())}")
        else:
            print("TOKENS:","of tokens in 'all':", len(self.index["all"].keys()))
        print("----------------------------------------")
        if self.permuterm:
            if self.multifield:
                print("PERMUTERMS:")
                for campo,_ in self.fields:
                        print(f"\t# of tokens in '{campo}': {len(self.ptindex[campo])}")
            else:
                print("PERMUTERMS:","of tokens in 'all':", len(self.ptindex["all"]))
            print("----------------------------------------")
        
        if self.stemming:
            if self.multifield:
                print("STEMS:")
                for campo,_ in self.fields:
                        print(f"\t# of tokens in '{campo}': {len(self.sindex[campo].keys())}")
            else:
                print("STEMS:","of tokens in 'all':", len(self.sindex["all"].keys()))
            print("----------------------------------------")
        if self.positional:
            print("Positional queries are allowed.")
        else:
            print("Positional queries are NOT allowed.")
        print("========================================")

        



    #################################
    ###                           ###
    ###   PARTE 2: RECUPERACION   ###
    ###                           ###
    #################################

    ###################################
    ###                             ###
    ###   PARTE 2.1: RECUPERACION   ###
    ###                             ###
    ###################################
       
    #Autores: Alex y Guillem
    def solve_query(self, query:str, prev:Dict={}):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Resuelve una query.
        Debe realizar el parsing de consulta que sera mas o menos complicado en funcion de la ampliacion que se implementen


        param:  "query": cadena con la query
                "prev": incluido por si se quiere hacer una version recursiva. No es necesario utilizarlo.


        return: posting list con el resultado de la query

        """
        
        if query is None or len(query) == 0:
            return []

        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################
        
        #OPERADORES disponibles 
        op=["AND", "OR", "NOT"]
        
        #Expresion regular que va a buscar los parentesis
        sep_parentesis = re.compile(r'\(|\)|"|[\w\:\-\?\*]+')
        #Lista para separar las palabras de todos los demas simbolos
        spp = sep_parentesis.findall(query)
        
        '''
        Para title:"hola que tal"..., se guarda ['title:','"','hola','que','tal','"',...] (no nos interesa)
        ahora con un bucle juntaremos algunos elementos para tener ['title:"hola que tal"',....] en otra lista
        '''
        sp =[]
        i=0
        #recorremos la lista
        while i < len(spp):
            #si el elemento tiene EN EL FINAL ':', significa que nos sigue un termino "hola que tal" (para positionals)
            if spp[i][-1] == ':':
                #vamos recorriendo la lista y concatenandolo a x hasta que encontremos '"'
                x = spp[i]
                t=""
                i+=2
                while spp[i] != '"':
                    t += f' {spp[i]}'
                    i+=1
                sp.append(f'{x}"{t.strip()}"')    
            #si no, lo copiamos en la lista final
            else:
                sp.append(spp[i])
            i+=1
        i = -1
        #recorremos la lista 
        while i < len(sp):
            #siempre que no se trate de la primera iteración (i = -1), i marcará una posición donde esté AND/OR
            if i > 0:
                #guardamos en una variable si estamos efectuando AND o OR
                if sp[i] == op[0]:
                    opf = self.and_posting
                elif sp[i] == op[1]:
                    opf = self.or_posting
            
            #si el siguiente al operador AND/OR no es NOT, no es el inicio de un paréntesis y no es el inicio de un término "positionals"    
            if sp[i+1] != op[2] and sp[i+1] != '(' and sp[i+1] != '"':
                #si contiene ':', se trata de multifield, llamamos a un método para tratar la busqueda especial
                if ':' in sp[i+1]:
                    x = self.tratar_busqueda(sp[i+1])
                    #si no se trata de la primera iteración, aplicamos AND/OR entre lo que ya teníamos "res" y lo nuevo "x", si no, iniciamos "res" con lo nuevo
                    if i >= 0: res = opf(res,x)
                    else: res = x
                    #en este caso, sumamos i+1 (se suma otro 1 al final del bucle)
                    i+=1
                else:
                    #si no contiene ':', se trata de un término normal
                    x = self.get_posting(sp[i+1],"all")
                    #si no se trata de la primera iteración, aplicamos AND/OR entre lo que ya teníamos "res" y lo nuevo "x", si no, iniciamos "res" con lo nuevo
                    if i >= 0: res = opf(res,x)
                    else: res = x
                    #en este caso, sumamos i+1 (se suma otro 1 al final del bucle)
                    i+=1
            elif sp[i+1] == '(':
                #si el siguiente a la operación AND/OR es '(', llamamos a un método para acotar los paréntesis y llamaremos a solve_query (se resuelve recursivamente)
                par = self.get_sintagma(sp,i+1)
                #el primer elemento del par nos devuelve la lista correspondiente a la subquery
                x = par[0]
                #si no se trata de la primera iteración, aplicamos AND/OR entre lo que ya teníamos "res" y lo nuevo "x", si no, iniciamos "res" con lo nuevo
                if i >= 0: res = opf(res,x)
                else: res = x
                #el segundo elemento del par nos devuelve la nueva i (se suma otro 1 al final del buecle)
                i = par[1]
            elif sp[i+1] == '"':
                #si el siguiente al operador AND/OR es '"', se trata de un término positionals, llamamos a un método especial para acotar el término
                par = self.acotarTerm(sp,i+1)
                #el primer elemento del par nos devuelve la lista del término positionals
                x = par[0]
                #si no se trata de la primera iteración, aplicamos AND/OR entre lo que ya teníamos "res" y lo nuevo "x", si no, iniciamos "res" con lo nuevo
                if i >= 0 : res = opf(res,x)
                else: res = x
                #el segundo elemento del par nos devuelve la nueva i (se suma otro 1 al final del buecle)
                i = par[1]
            #si no se cumple nada de lo anterior, la palabra siguiente a la operación AND/OR es una NOT, comprobaremos todo lo anterior pero con i+2 (la siguiente a la not)
            elif sp[i+2] == '(':
                #si el siguiente a la operación NOT es '(', llamamos a un método para acotar los paréntesis y llamaremos a solve_query (se resuelve recursivamente)
                par = self.get_sintagma(sp,i+2)
                #el primer elemento del par nos devuelve la lista correspondiente a la subquery
                #aplicamos la NOT a la lista
                x = self.reverse_posting(par[0])
                #si no se trata de la primera iteración, aplicamos AND/OR entre lo que ya teníamos "res" y lo nuevo "x", si no, iniciamos "res" con lo nuevo
                if i >= 0: res = opf(res,x)
                else: res = x
                #el segundo elemento del par nos devuelve la nueva i (se suma otro 1 al final del buecle)
                i = par[1]
            elif sp[i+2] == '"':
                #si el siguiente al operador NOT es '"', se trata de un término positionals, llamamos a un método especial para acotar el término
                par = self.acotarTerm(sp,i+2)
                #el primer elemento del par nos devuelve la lista del término positionals
                #aplicamos la NOT a la lista
                x = self.reverse_posting(par[0])
                #si no se trata de la primera iteración, aplicamos AND/OR entre lo que ya teníamos "res" y lo nuevo "x", si no, iniciamos "res" con lo nuevo 
                if i >= 0: res = opf(res,x)
                else: res = x
                #el segundo elemento del par nos devuelve la nueva i (se suma otro 1 al final del buecle)
                i = par[1]   
            elif ':' in sp[i+2]:
                #si contiene ':', se trata de multifield, llamamos a un método para tratar la busqueda especial
                #aplicamos la NOT a la lista
                x = self.reverse_posting(self.tratar_busqueda(sp[i+2]))
                #si no se trata de la primera iteración, aplicamos AND/OR entre lo que ya teníamos "res" y lo nuevo "x", si no, iniciamos "res" con lo nuevo
                if i >= 0: res = opf(res,x)
                else: res = x
                #en este caso, sumamos i+2 (se suma otro 1 al final del bucle)
                i+=2
            else:
                #Si no ocurre nada de lo anterior, la siguiente a la not es un término normal
                #aplicamos la NOT a la lista
                x = self.reverse_posting(self.get_posting(sp[i+2],"all"))
                #si no se trata de la primera iteración, aplicamos AND/OR entre lo que ya teníamos "res" y lo nuevo "x", si no, iniciamos "res" con lo nuevo
                if i >= 0: res = opf(res,x)
                else: res = x
                #en este caso, sumamos i+2 (se suma otro 1 al final del bucle)
                i+=2
            #sumamos uno, así el puntero i señalará a la siguiente AND o OR
            i+=1
        
        return res
    
    #Autor: Guillermo
    def tratar_busqueda(self,termino):
        
        '''
            Llama al método get_posting correctamente cuando es "multifield"
            param:  "termino": cadena de la forma x:y donde "x" será el tipo de búsqueda (title,summary...) y "y" es la busquda a realizar
        
            return: posting list con el resultado de la query
        '''
    
        #buscamos el indice del ':' y llamamos al get_posting
        p = termino.find(":")
        #tipo = lo que precede a los dos puntos
        tipo = termino[:p]
        #busqueda = lo que hay detrás de los puntos
        busqueda = termino[p+1:]
        res = list(self.get_posting(busqueda,tipo))
        return res
        
    #Autor: Guillermo
    def acotarTerm(self,lista,i):
        '''
            Llama al método get_posting correctamente cuando es positionals
            param:  "lista" de la query inicial
                    "i" el puntero que indica por donde vamos
        
            return: par donde el primer término es el resultado de la query, el puntero i
        '''
        #sumamos uno para no contar el '"'
        i+=1
        x = ""
        #mientras no sea '"' seguimos concatenando
        while lista[i] != '"': 
            x+= f' {lista[i]}'
            i+=1 

        x = f'"{x.strip()}"'
        #hacemos la consulta
        r = self.get_posting(x,"all")
        return(r,i)    
        
    #Autor: Guillermo       
    def get_sintagma(self,list,i):
        """

        Dada una lista con la query separada y un entero i que indica el primer parentesis calcula 
        donde acaba ese parentesis y resuelve la subquery asociada al mimso


        param:  "list": query separada por palabras y parentesis.
                "i": entero que indica la posicion del primer parentesis

        return: tupla con (posting list de subquery resuelta, posicion donde acaba el parentesis)

        """
        #Contador de parentesis abiertos
        cont = 1
        #Posicion en la que nos encontramos
        i += 1
        #Acumulador de la query
        x = ''
        #Mientras que no encontremos el parentesis que cierra la subconsulta o lleguemos a la longitud de la consulta
        while cont > 0 and i < len(list):
            #Si encontramos un parentesis '(' sumamos 1
            if list[i] == '(':
                cont += 1
            #Si encontramos un parentesis ')' restamos 1
            elif list[i] == ')':
                cont -= 1

            #Si el contador es > a 0
            if cont > 0:
                #Acumulamos la consulta
                x += list[i] + ' '
            #Incrementamos el contador de posicion en 1
            i += 1
        #Cuando salimos tenemos en i la posicion del ultimo parentesis
        x = self.solve_query(x.strip())
        #Devolvemos una tupla con el resultado de la query y la posicion siguiente
        return (x,i-1)
    
    #Autor: Ruben y Alex
    def get_posting(self, term:str, field:Optional[str]=None):
        """

        Devuelve la posting list asociada a un termino. 
        Dependiendo de las ampliaciones implementadas "get_posting" puede llamar a:
            - self.get_positionals: para la ampliacion de posicionales
            - self.get_permuterm: para la ampliacion de permuterms
            - self.get_stemming: para la amplaicion de stemming


        param:  "term": termino del que se debe recuperar la posting list.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario si se hace la ampliacion de multiples indices

        return: posting list
        
        NECESARIO PARA TODAS LAS VERSIONES

        """
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################

        #Pasamos el termino a minusculas
        term = term.lower()


        #Comprobamos si el termino tiene ", en cuyo caso es una busqueda posicional
        if '"' in term:
            #Realizamos la busqueda posicional
            return self.get_positionals(term,field)
        
        #Comprobamos si la consulta es con comodines, en cuyo caso es una busqueda de permuterm
        if '?' in term or '*' in term:
            return self.get_permuterm(term,field)

        #En caso de estar usando stemming llamamos al metodo get_stemming para obtener la posting list adecuada
        if self.use_stemming:
            return self.get_stemming(term,field)

        #En caso de no estar usando ninguna modificacion
        #Comprobamos si el termino se encuentra en el indice invertido

        if term in self.index[field].keys():
            #En caso de encontrarse devolvemos la posting list del termino
            #Miraremos si se ha indexado posicionalmente, en cuyo caso solo nos quedaremos con los id de los documentos
            if isinstance((res:=self.index[field][term]),dict):
                #Se hace una conversion a diccionario para obtener las id y despues lo pasamos a lista 
                return list(self.index[field][term])
            #En caso de no ser posicional devolvemos la lista
            return res
        else:
            #Si no se encuentra devolveremos una lista vacia
            return []  


    #Autor: Ruben
    def get_positionals(self, terms:str, field):
        """

        Devuelve la posting list asociada a una secuencia de terminos consecutivos.
        NECESARIO PARA LA AMPLIACION DE POSICIONALES

        param:  "terms": lista con los terminos consecutivos para recuperar la posting list.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """
        ########################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE POSICIONALES ##
        ########################################################


        #Obtenemos todos los terminos de la busqueda y los separamos en una lista
        terms = self.tokenize(terms)
        #Obtenemos el index indicado por el field
        index = self.index[field]
        #Sacamos el indice posicional del primer termino
        try:
            positionals = [index[terms[0]]]
        except KeyError:
            return []
        #Lo ponemos en la lista donde obtendremos los documentos donde estan todos los terminos pasados
        match = list(positionals[0])
        #Recorremos el resto de terminos
        for i in terms[1:]:
            #Vamos anyadiendo a positionals todos los indices posicionales de los terminos
            try:
                positionals.append(index[i])
            except KeyError:
                return []
            #Hacemos el and con lo que ya teniamos en match y el ultimo indice anyadido a positionals
            match = self.and_posting(match,list(positionals[-1]))
        #Creamos una lista para almacenar el resultado
        res = []
        #Recorremos todos los id de los documentos en los que aparecen todas las palabras
        for id in match:
            #Recorremos las posciones del primer termino en el documento id
            for pos in positionals[0][id]:
                #Creamos una variable que indicara que esta el termino
                esta = True
                #Incrementamos en 1 la posicion, pues sera en la que deberia estar el siguiente termino
                pos+=1
                #Vamos recorriendo el resto de indices posicioanles de los terminos siguientes al primero
                for dic in positionals[1:]:
                    #Si la posicion buscada esta en el indice posicinal incrementamos el contador y seguiremos para comprobar que estan todas las palabras seguidas
                    if pos in dic[id]:
                        pos+=1
                    #Si no esta la posicion ponemos la variable esta a false, indicando que no sigue el orden de palabras que deberia y salimos del bucle, pues los siguientes documentos no nos interesan ya
                    else:
                        esta = False
                        break
                #En caso de haber encontrado todas las palabras en orden esta=True y por tanto lo anyadimos a res
                if esta: 
                    res.append(id)
                    #No hara falta seguir mirando posiciones de este documento, pues ya hemos encontrado la primera aparacion y es suficiente, continuamos con el resto de documentos
                    break

        #Una vez finalizado el proceso devolvemos el resultado final
        return res

    #Autor: Ruben
    def get_stemming(self, term:str, field: Optional[str]=None):
        """

        Devuelve la posting list asociada al stem de un termino.
        NECESARIO PARA LA AMPLIACION DE STEMMING

        param:  "term": termino para recuperar la posting list de su stem.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """
        
        stem = self.stemmer.stem(term)

        ####################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE STEMMING ##
        ####################################################

        #Comrobamos si tenemos en sindex la raiz pasada 
        if stem in self.sindex[field].keys():
            #En caso de tenerla inicializamos una lista
            res = []
            #Recorremos todos los terminos de la raiz 
            for termino in self.sindex[field][stem]:
                #Miraremos si se ha indexado posicionalmente, en cuyo caso solo nos quedaremos con los id de los documentos
                if isinstance((posicionales:=self.index[field][termino]),dict):
                    #Vamos acumulando las posting list de los terminos para obtener la posting list de la raiz
                    #A la vez vamos transformando los posicinales para solo hacer el or con las id de los documentos
                    res = self.or_posting(res,list(posicionales))
                else:
                    #Vamos acumulando las posting list de los terminos para obtener la posting list de la raiz
                    res = self.or_posting(res,posicionales)
            #Devolvemos la posting list obtenida
            return res
        else:
            #En caso de no tenerla devolvemos una lista vacia
            return []  
    
    #Autor: Jose
    def get_permuterm(self, term:str, field:Optional[str]=None):
        """

        Devuelve la posting list asociada a un termino utilizando el indice permuterm.
        NECESARIO PARA LA AMPLIACION DE PERMUTERM

        param:  "term": termino para recuperar la posting list, "term" incluye un comodin (* o ?).
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """
        ##################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA PERMUTERM ##
        ##################################################
        """
        1. Sí field es None se asigna a "all".
        2. Si el término contiene ? se asigna una variable que afecta qué términos se recogen.
        2.1. Genera el permuterm del termino de busqueda
        3. Se recorre mediante búsqueda binaria la lista que contiene los pares (permuterm, término).
        4. Cuando la búsqueda binaria encuentra un match (el pivote de la búsqueda inicia por la versión permuter del término) finaliza la búsqueda.
            4.1. Cuando la búsqueda binaria no encuentra ningun un match finaliza la búsqueda.
        5. Se recorre desde la posición pivote final hacia izquierda y derecha para la recogida de términos válidos.
            5.1. Un elemento es válido cuando el elemento inicia por la versión permuterm del término.
            5.2. Si se trata de una búsqueda ? se debe cumplir que la longitud del elemento sea igual a la longitud de la versión permuterm del termino.
        6. Extrae los posting list en OR logica de todos los elementos recogidos.
        """

        #1. Sí field es None se asigna a "all".
        if(field == None):
            field = "all"
        
        #2. Si el término contiene ? se asigna una variable que afecta qué términos se recogen.
        comodin = term.find("*")
        LetraComodin = False
        if (comodin == -1):  
            comodin = term.find("?")
            LetraComodin = True

        #2.1. Genera el permuterm del termino de busqueda
        pbusqueda = f'{term[comodin+1:]}${term[0:comodin]}'

        punteroMax:int = len(self.ptindex[field])
        punteroMin:int = 0
        puntero:int = int(punteroMax/2)

        pivote:str = self.ptindex[field][puntero][0]
        notFound = True

        sol:list = []

        #3. Se recorre mediante búsqueda binaria la lista que contiene los pares (permuterm, término).
        while notFound:
            #4. Cuando la búsqueda binaria encuentra un match (el pivote de la búsqueda inicia por la versión permuter del término) finaliza la búsqueda.
            if (pivote.startswith(pbusqueda)):#*/? match exit
                notFound = False
            #4.1. Cuando la búsqueda binaria no encuentra ningun un match finaliza la búsqueda.
            elif(punteroMin > punteroMax):#no match exit
                notFound = False

            elif(pivote < pbusqueda):#si pivote es menor que version pterm de la busqueda cambia punteros
                punteroMin = puntero+1
                puntero = int((punteroMin + punteroMax) / 2)
                pivote = self.ptindex[field][puntero][0]
            elif (pivote > pbusqueda):#si pivote es mayor que version pterm de la busqueda cambia punteros
                punteroMax = puntero-1
                puntero = int((punteroMin + punteroMax) / 2)
                pivote = self.ptindex[field][puntero][0]


        Pmatch = puntero-1
        checker:str = self.ptindex[field][Pmatch][0]
        #5. Se recorre desde la posición pivote final hacia izquierda para la recogida de términos válidos.
        while(checker.startswith(pbusqueda)):#postCheck recoge a la izquierda hasta no hacer match
            if(not LetraComodin):
                sol.append(self.ptindex[field][Pmatch][1])
            elif (len(checker) == len(pbusqueda)+1):
                sol.append(self.ptindex[field][Pmatch][1])
            Pmatch-=1
            checker = self.ptindex[field][Pmatch][0]

        Pmatch = puntero
        checker = self.ptindex[field][Pmatch][0]
        #5. Se recorre desde la posición pivote final hacia derecha para la recogida de términos válidos.
        while(checker.startswith(pbusqueda)):#postCheck recoge a la derecha hasta no hacer match
            if(not LetraComodin):
                sol.append(self.ptindex[field][Pmatch][1])
            elif (len(checker) == len(pbusqueda)+1):
                sol.append(self.ptindex[field][Pmatch][1])
            Pmatch+=1
            checker = self.ptindex[field][Pmatch][0]

        PostingsPterms:list = []
        #6. Extrae los posting list en OR logica de todos los elementos recogidos.
        for termino in sol:
            if isinstance(self.index[field][termino],dict):
                PostingsPterms = self.or_posting(PostingsPterms,list(self.index[field][termino]))
            else:
                PostingsPterms = self.or_posting(PostingsPterms,self.index[field][termino])
                
        return PostingsPterms
        


    #Autor: Alex
    def reverse_posting(self, p:list):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Devuelve una posting list con todas las noticias excepto las contenidas en p.
        Util para resolver las queries con NOT.


        param:  "p": posting list


        return: posting list con todos los artid exceptos los contenidos en p

        """
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################

        #extraemos todos los id de los articulos:  
        idArt=list(self.articles.keys())
        #devolvemos aquellos artid que no aparecen en p 
        return self.minus_posting(idArt,p)



    #Autor: Alex
    def and_posting(self, p1:list, p2:list):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Calcula el AND de dos posting list de forma EFICIENTE

        param:  "p1", "p2": posting lists sobre las que calcular


        return: posting list con los artid incluidos en p1 y p2

        """
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################
        #lista donde se almacenarán aquellos id que aparecen en ambas posting list  
        res = []
        #putero a la primera posting list 
        p1p = 0
        #puntero a la segunda posting list 
        p2p = 0
        #mientras que ambos punteros no se salgan del rango de las respectivas posting list a las que apuntan 
        while p1p < len(p1) and p2p < len(p2):
            #si ambos artid son iguales se añaden a la respuesta y los punteros avanzan una posición 
            if p1[p1p] == p2[p2p]:
                res.append(p1[p1p])
                p1p += 1
                p2p += 1
            #si el valor al que apunta el primer puntero es menor este avanza en una posición 
            elif p1[p1p] < p2[p2p]:
                p1p += 1
            #si el valor al que apunta el segundo puntero es menor se avanza en una posición el puntero 
            else:
                p2p += 1
        #se devuelve la lista resultante 
        return res


    #Autor: Alex
    def or_posting(self, p1:list, p2:list):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Calcula el OR de dos posting list de forma EFICIENTE

        param:  "p1", "p2": posting lists sobre las que calcular


        return: posting list con los artid incluidos de p1 o p2

        """
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################
        #lista donde se almacenarán los id de los artículos 
        res = []
        #posición a la que apunta el primer puntero a la primera posting list  
        p1p = 0
        #posición a la que apunta el primer puntero a la segunda posting list 
        p2p = 0
        #mientras que la posición a la que apunta ambos punteros esté dentro del rango de las posting list respectivas  
        while p1p < len(p1) and p2p < len(p2):
            #si los artid son iguales se añade a la res y se avanzan las posiciones de los punteros 
            if p1[p1p] == p2[p2p]:
                res.append(p1[p1p])
                p1p += 1
                p2p += 1
            #si el primer artículo es menor que el segundo, se almacena este y se avanza la posición del primer puntero 
            elif p1[p1p] < p2[p2p]:
                res.append(p1[p1p])
                p1p += 1
            # si el segundo artículo es menor que el primero, se almacena este y se avanza la posición del segundo puntero
            else:
                res.append(p2[p2p])
                p2p += 1
        #recorre las posiciones que no se hayan visitado de las listas y se almacenan los artículos en la res 
        while p1p < len(p1):
            res.append(p1[p1p])
            p1p += 1
        while p2p < len(p2):
            res.append(p2[p2p])
            p2p += 1
        #se devuelve la lista donde se han almacenado los valores 
        return res

    #Autor: Alex
    def minus_posting(self, p1, p2):
        """
        OPCIONAL PARA TODAS LAS VERSIONES

        Calcula el except de dos posting list de forma EFICIENTE.
        Esta funcion se incluye por si es util, no es necesario utilizarla.

        param:  "p1", "p2": posting lists sobre las que calcular


        return: posting list con los artid incluidos de p1 y no en p2

        """
        ########################################################
        ## COMPLETAR PARA TODAS LAS VERSIONES SI ES NECESARIO ##
        ########################################################

        #lista donde se almacenarán los valores a devolver 
        res = []
        #puntero a la primera posting list  
        p1p = 0
        #puntero a la segunda posting list 
        p2p = 0
        #mientrras que el valor de los punteros no supere la longitud de las posting list 
        while p1p < len(p1) and p2p < len(p2):
            #si los id de los articulos son iguales, incrementamos el valor de ambos punteros 
            if p1[p1p] == p2[p2p]:
                p1p += 1
                p2p += 1
            #si el valor al que apunta el primer puntero es menor al que apunta el segundo puntero, se añade este valor a res 
            elif p1[p1p] < p2[p2p]:
                res.append(p1[p1p])
                p1p += 1
            #en caso de que el valor de artid al que apunta el segundo puntero sea menor que el que apunta el primer puntero, se incrementa en uno el valor del segundo puntero 
            else:
                p2p += 1
        #desde la posicion actual del primer puntero hasta el final del primer posting list, se recorre la lista y se añaden los artid en res 
        while p1p < len(p1):
            res.append(p1[p1p])
            p1p += 1
        #se devuelven los artid resultantes 
        return res





    #####################################
    ###                               ###
    ### PARTE 2.2: MOSTRAR RESULTADOS ###
    ###                               ###
    #####################################

    def solve_and_count(self, ql:List[str], verbose:bool=True) -> List:
        results = []
        for query in ql:
            if len(query) > 0 and query[0] != '#':
                r = self.solve_query(query)
                results.append(len(r))
                if verbose:
                    print(f'{query}\t{len(r)}')
            else:
                results.append(0)
                if verbose:
                    print(query)
        return results


    def solve_and_test(self, ql:List[str]) -> bool:
        errors = False
        for line in ql:
            if len(line) > 0 and line[0] != '#':
                query, ref = line.split('\t')
                reference = int(ref)
                result = len(self.solve_query(query))
                if reference == result:
                    print(f'{query}\t{result}')
                else:
                    print(f'>>>>{query}\t{reference} != {result}<<<<')
                    errors = True

            else:
                print(line)

        return not errors

    #Autor: Alex
    def solve_snippet(self,query:str,palabras:List[str]):
        #filtramos aquellas consultas a las que se le puede aplicar snippet :
        #si se usa stemming en la consulta se descarta el uso de snipet 
        if self.use_stemming:
            return
        #si la consulta contiene paréntesis (), dods puntos (:), asterisco (*), o signo de interrogacion (?) se descarta el uso de snippet 
        c = re.findall(r'[():\"*?]',query)
        if len(c)!=0:
            return
        #se obtienen los terminos de la consulta, eliminando los AND, OR y NOT
        terminos = re.findall(r'\b(?!AND|OR|NOT)\w+\b', query)
        #si hay mas de 5 terminos en la consulta, se descarta el uso de snippet 
        if len(terminos)>5:
            return
        #diccionario: clave -> termino, valor -> contexto por detras de la palabra, la palabra, y contexto por delante 
        indice={}
        #almacenará el contexto que antecede la palabra 
        contexto=[]
        #se extraen todos los carácteres alfanuméricos del artículo 
        palabras=self.tokenize(palabras)
        #valor booleano que indica si el contxto por detras del termino tiene una longitud mayor que 5 
        anteriores = False
        #se recorren todas las palabras del artículo 
        for posicion,palabra in enumerate(palabras):
            #si la palabra está contenida en los térmios 
            if palabra in terminos:
                #si está en los términos y todavía no ha aparecido 
                if palabra not in indice:
                    #se coge el contexto quue sigue a la palabra 
                    siguientes = palabras[posicion+1:posicion+7]
                    #si la longitud de las siguientes palabras es mayor que 5 añadimos los puntos suspensivos al final. Esto significará que el texo no acaba en el contexto que sigue a la palabra
                    if len(siguientes) > 5:
                        siguientes.append("...")
                    #si se tiene un contexto anterior a la palabra de longitud mayor que 5, se añaden puntos suspensivos, seguido del contexto, la propia palabra y el contexto que la sigue 
                    if anteriores:
                        indice[palabra]=["..."]+contexto+[palabra]+siguientes   
                    #en caso contrario, simplemente se añade el contexto por detrás, junto a la palabra y el contexto por delante 
                    else:
                         indice[palabra]=contexto+[palabra]+siguientes
            #s ila longitud del contexto que le presigue es mayor que 5, se activa el booleano de anteriores y se elimina el primer elemento de la lista 
            if len(contexto) > 5:
                anteriores = True
                contexto.pop(0)
            #se añade la palabra actual al contexto 
            contexto.append(palabra)
        #se devuelve el indice 
        return indice

    #Autor: Alex
    def solve_and_show(self, query:str):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Resuelve una consulta y la muestra junto al numero de resultados 

        param:  "query": query que se debe resolver.

        return: el numero de artículo recuperadas, para la opcion -T

        """
        ################
        ## COMPLETAR  ##
        ################
        print("========================================")
        #se resuelve la query proporcionada 
        docs=self.solve_query(query)
        #se recorren todos los id de los articulos devueltos 
        for i,ai in enumerate(docs):
            #en caso que no se haya indicado que se muestren todos los resultados, si hemos extraido 10 articulos se detiene la busqueda
            if not self.show_all and i == 10:
                break
            #se obtiene el id del documento al que pertenece el articulo y se obtiene la linea en la cual se encuentra 
            di,nline=self.articles[ai]
            #se obriene la ruta del documento al cual pertenece el articulo  
            ruta=self.docs[di]
            #se recorre el documento linea por linea  
            for j, line in enumerate(open(ruta)):
                #si el numero de lina actual es diferente a la que buscamos seguimos buscando    
                if nline != j:
                    continue
                #se obtiene el diccionario de la linea si es la que buscamos
                line=self.parse_article(line)
                break
            #extraemos la url del diccionario de la linea 
            url = line["url"]
            #extraemos el titulo del diccionario de la linea 
            title = line["title"]
            #si se desea mostrar snippets: 
            if self.show_snippet:
                #mostramos la iteracion junto con el id del articulo y la url 
                print(f"#  {i} ( {ai}) {url}")
                #se muestra el titulo del articulo 
                print(title)
                #se aplica snippet de la query en el articulo actual 
                cont = self.solve_snippet(query,line["all"])
                #se muestra el contenido devuelto  
                for k in cont:
                    print(" ".join(cont[k]))
                print("")
            #si no se requiere el uso de snippet, simplemente mostramos la iteracin junto con id del articulo,el titulo y la url 
            else:
                print(f"#  {i} ( {ai}) {title}: {url}")
                
        print("========================================")
        #finalmente se muestra el numero de resultados y se devuelve este valor  
        print("Number of results: ",(ndocs := len(docs)))
        return ndocs

