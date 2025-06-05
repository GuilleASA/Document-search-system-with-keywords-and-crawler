from SAR_Crawler_lib import SAR_Wiki_Crawler

text = '''##Videojuego##
Un videojuego, o juego de v´ıdeo es un juego electr´onico en el que una o m´as personas ...
Al dispositivo de entrada, usado para manipular un videojuego se le conoce como controlador ...
Generalmente los videojuegos hacen uso de otras maneras, aparte de la imagen, de proveer ...
==Historia==
Los or´ıgenes del videojuego se remontan a la d´ecada de 1950, cuando poco despu´es de la ...
==Generalidades==
T´ıpicamente, los videojuegos recrean entornos y situaciones virtuales en los que el ....
Dependiendo del videojuego, una partida puede disputarla una sola persona contra la ...
Existen videojuegos de muchos tipos. Algunos de los g´eneros m´as representativos son los ...
--Tecnolog´ıa--
Un videojuego se ejecuta gracias a un programa de software (el videojuego en s´ı) que es ...
...
--Plataformas--
Los distintos tipos de dispositivo en los que se ejecutan los videojuegos se conocen como ...
--G´eneros--
Los videojuegos se pueden clasificar en g´eneros atendiendo a factores ...
--Multijugador--
En muchos juegos se puede encontrar la opci´on de multijugador, es decir, que varias personas ...
==Industria del videojuego==
'''

text2 = '''
##Videojuego##
simisimiyeysimiyeysimia
==Historia==
Los orígenes del cine se remontan a finales del siglo XIX, cuando los hermanos Lumière realizaron sus primeras proyecciones públicas.
==Desarrollo==
El desarrollo de la inteligencia artificial se ha acelerado en las últimas décadas, con avances significativos en áreas como el aprendizaje automático y la robótica.
==Arte==
El arte abstracto surgió a principios del siglo XX como una forma de expresión que busca representar las emociones y conceptos abstractos a través de formas y colores.
==Música==
La música clásica ha sido una forma de expresión cultural durante siglos, con compositores como Beethoven, Mozart y Bach dejando un legado duradero en la historia de la música.
==Ahora que máquina==
==Literatura==
La literatura moderna abarca una amplia variedad de géneros y estilos, desde la narrativa realista hasta la ciencia ficción y la fantasía épica.
==Industria del videojuego==
Creo que la industria en el videjuego mola ,no sé
--Plataformas--
Los distintos tipos de dispositivo en los que se ejecutan los videojuegos se conocen como ...
--G´eneros--
Los videojuegos se pueden clasificar en g´eneros atendiendo a factores ...
--Ayuda por favor--
Me estoy volviendo loco
--Otra prueba--
Para ver si me estoy volviendo loco
--Multijugador--
En muchos juegos se puede encontrar la opci´on de multijugador, es decir, que varias personas ...
==Arte==
El arte abstracto surgió a principios del siglo XX como una forma de expresión que busca representar las emociones y conceptos abstractos a través de formas y colores.
==Comedia==
Si lees esto es que estás haciendo debugging porque algo no cuadra con lo que Guillem ha hecho, pido perdón
Que pasó amigo, te estas confundiendo?
--subcomedia--
prueba
--LaPruebaFinal--
que nervios
--Otro problema--
lo estoy pasando mal
==Golpear==
Ayuda
'''

url = "mi_url"

texto_caca = '''simisimiyey\n==que==hola'''
crawler = SAR_Wiki_Crawler()
print(crawler.parse_wikipedia_textual_content(text,url))