import re
#este método recibe la lista "query" y el índice i que marca por donde vamos        
def get_sintagma(list,i):
        cont= 1
        i += 1
        x = ''

        while cont > 0 and i < len(list):
            if list[i] == '(':
                cont += 1
            elif list[i] == ')':
                cont -= 1

            if cont > 0:
                x += list[i] + ' '
            i += 1

        print(x.strip())
        print(i)
    
 

def encontrar_termino(query):
    
        op=["AND", "OR", "NOT"]
        
        #Expresion regular que va a buscar los parentesis
        sep_parentesis = re.compile(r'\(|\)|"|[\w:]+')
        #Lista para separar las palabras de todos los demas simbolos
        spp = sep_parentesis.findall(query)
        
        sp =[]
        
        i=0
        
        while i < len(spp):
            if spp[i][-1] == ':':
                x = spp[i]
                t=""
                i+=2
                while spp[i] != '"':
                    t += f' {spp[i]}'
                    i+=1
                sp.append(f'{x}"{t.strip()}"')    
            else:
                sp.append(spp[i])
            i+=1    
            print(sp)
                
        print(sp)

def tratar_busqueda(termino):
        p = termino.find(":")
        tipo = termino[:p]
        busqueda = termino[p+1:]
        print(tipo)
        print(busqueda)
        
query = '(NOT summary:"todo el mundo") AND (summary:todo AND summary:el AND summary:mundo)'
query2 = 'title:información AND summary:recuperación AND NOT section-name:precisión'

encontrar_termino(query)