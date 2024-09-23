"""
    PROYECTO JUEGO EN PHYTON PARA SGE:
    Juego: TETRIS
    Título: PYNATRIX
    Autor: Ignacio Martínez de Carvajal Andrés
    Última modificación: 10/01/2022 - 00:40
"""

import pygame
from pygame import Rect  # objeto que se usa para almacenar y manipular áreas rectangulares
import random  # para poder obtener aleatorios
from collections import OrderedDict  # permite recordar el orden en el que se agregan elementos a un diccionario
import numpy as np
'''
liberia para representar cada uno de los bloques del juego como una matriz (lo hace internamente) 
y deja rotar y voltear las figuras
'''

PAN_WIDTH, PAN_HEIGHT = 500, 601  # constantes para definir el tamaño de la pantalla (anchura, altura)
CUAD_WIDTH, CUAD_HEIGHT = 300, 600  # constantes para el tamaño de la cuadricula (anchura, altura)
TIT_SIZE = 30  # constante para el tamaño de un espacio


# CLASES EXCEPCIONES PARA VER SI TOCA ARRIBA O ABAJO
class AbajoAlcanzado(Exception):
    pass


class ArribaAlcanzado(Exception):
    pass


# CLASE PARA DEFINIR EL BLOQUE
class Bloque(pygame.sprite.Sprite):

    def __init__(self):  # parametro especial que sirve como autorreferencia
        super().__init__()  # porque hereda del main y a su vez va a tener herencia (herencia multiple)
        # indicamos el color del bloque (random)
        self.color = random.choice((
            (0, 255, 255),
            (255, 127, 80),
            (255, 20, 147),
            (255, 215, 0),
            (127, 255, 0),
            (255, 0, 0)
        ))
        self.actual = True  # bloque actual
        self.struct = np.array(self.struct)  # definimos la estructura
        self.velocidad = 1

        # hacemos la rotacion random inicial y el volteo
        if random.randint(0, 1):
            self.struct = np.rot90(self.struct)
        if random.randint(0, 1):
            self.struct = np.flip(self.struct, 0)  # se voltea en el eje x

        self._dibujar()

    @property
    def group(self):
        return self.groups()[0]

    @property  # hace que el método se convierta en una propiedad
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        self.rect.left = value * TIT_SIZE

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
        self.rect.top = value * TIT_SIZE

    @staticmethod
    def colision(bloque, group):
        for otro_block in group:
            if bloque == otro_block:
                continue

            if pygame.sprite.collide_mask(bloque, otro_block) is not None:
                return True

        return False

    def _dibujar(self, x=4, y=0):
        ancho = len(self.struct[0]) * TIT_SIZE  # mirar que hace
        alto = len(self.struct) * TIT_SIZE

        self.image = pygame.surface.Surface([ancho, alto])
        # creamos la imagen con la superficie y las variables creadas
        self.image.set_colorkey((0, 0, 0))  # definimos el color

        # posicion y tamaño
        self.rect = Rect(0, 0, ancho, alto)
        self.x = x
        self.y = y

        for y, row in enumerate(self.struct):
            for x, col in enumerate(row):
                if col:
                    pygame.draw.rect(
                        self.image, self.color, Rect(x*TIT_SIZE + 1, y*TIT_SIZE + 1, TIT_SIZE - 2, TIT_SIZE - 2))

        self._mascara()

    def redibujar(self):
        self._dibujar(self.x, self.y)

    # METODO PARA COMPROBAR LAS COLISIONES
    def _mascara(self):
        self.mask = pygame.mask.from_surface(self.image)  # crea un objeto que comprueba a la perfeccion las colisiones

    def mover_izquierda(self, group):
        self.x -= 1

        # comprobamos si llega al margen izquierdo
        if self.x < 0 or Bloque.colision(self, group):
            self.x += 1

    def mover_derecha(self, group):
        self.x += 1

        if self.rect.right > CUAD_WIDTH or Bloque.colision(self, group):
            self.x -= 1

    def mover_abajo(self, group):
        self.y += self.velocidad

        if self.rect.bottom > CUAD_HEIGHT or Bloque.colision(self, group):
            self.y -= 1
            self.actual = False
            raise AbajoAlcanzado

    def rotar(self, group):
        self.image = pygame.transform.rotate(self.image, 90)

        # una vez rotados, necesitamos actualizar el tamaño y la posicion
        self.rect.width = self.image.get_width()
        self.rect.height = self.image.get_height()
        self._mascara()

        # miramos que la nueva posicion no exceda limites ni choque con otros bloques
        while self.rect.right > CUAD_WIDTH:
            self.x -= 1

        while self.rect.left < 0:
            self.x += 1

        while self.rect.bottom > CUAD_HEIGHT:
            self.y -= 1

        while True:
            if not Bloque.colision(self, group):
                break
            self.y -= 1

        self.struct = np.rot90(self.struct)

    def update(self):
        if self.actual:
            self.mover_abajo()


# CLASES HIJA PARA DEFINIR LOS DIFERENTES BLOQUES QUE HAY
class BloqueCuadrado(Bloque):
    struct = (
        (1, 1),
        (1, 1)
    )


class BloqueT(Bloque):
    struct = (
        (1, 1, 1),
        (0, 1, 0)
    )


class BloqueLinea(Bloque):
    struct = (
        (1,),
        (1,),
        (1,),
        (1,)
    )


class BloqueL(Bloque):
    struct = (
        (1, 1),
        (1, 0),
        (1, 0),
    )


class BloqueZ(Bloque):
    struct = (
        (0, 1),
        (1, 1),
        (1, 0),
    )


# METODO PARA QUITAR LAS COLUMNAS VACIAS
def borrar_columnas_vacias(arr, _x_offset=0, _seguir_contando=True):

    """
    Elimina las columnas que vacias (que tienen 0) el valor de retorno es arr, _x_offset
    cuando _x_offset es cuanto es necesario aumentar la coordenada X para mantener la posicion original
    """

    for columna, col in enumerate(arr.T):
        if col.max() == 0:
            if _seguir_contando:
                _x_offset += 1
            # borramos la columna actual y se vuelve a intentar
            arr, _x_offset = borrar_columnas_vacias(np.delete(arr, columna, 1), _x_offset, _seguir_contando)
            break
        else:
            _seguir_contando = False
    return arr, _x_offset


# CLASE PARA AGRUPAR LOS BLOQUES
class GrupoBloques(pygame.sprite.OrderedUpdates):

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        '''
        *args: es una lista de argumentos, como argumentos posicionales. Permite pasar cualquier argumento
        **kwargs: es un diccionario cuyas claves se convierten en parámetros 
        y sus valores en los argumentos de los parámetros. Permite pasar cualquier parámetro
        '''
        self._reset_cuadricula()

        self._ignorar = False
        self.puntuacion = 0
        self.bloque_siguiente = None  # objeto que denota falta de valor

        self.parar_moviviento_bloque_actual()  # ahora mismo no se mueve, se hace para inicializarlo
        self._crear_bloque()  # creamos el primer bloque

    @property
    def bloque_actual(self):
        return self.sprites()[-1]

    @staticmethod
    def coger_random():
        return random.choice((BloqueCuadrado, BloqueLinea, BloqueT, BloqueZ, BloqueL))()

    def _chequea_linea(self):
        # chequea la linea y la resetea si esta completa
        for i, row in enumerate(self.cuad[::-1]):  # truco para obtener una cadena o lista del reves [inicio:fin:paso]
            if all(row):
                self.puntuacion += 5  # si se completa la linea se puntua 5 puntos
                # se cogen los bloques afectados y se eliminan los duplicados
                bloques_afectados = list(OrderedDict.fromkeys(self.cuad[-1 - i]))

                for bloque, y_offset in bloques_afectados:
                    # se elimina los espacios de los bloques que pertenecen a la línea completada
                    bloque.struct = np.delete(bloque.struct, y_offset, 0)

                    if bloque.struct.any():
                        # una vez eliminado, comprobar si hay columnas vacias para eliminarlas si las hay
                        bloque.struct, x_offset = \
                            borrar_columnas_vacias(bloque.struct)
                        # compensamos el espacio quitado con las columnas para tener la posicion original del bloque
                        bloque.x += x_offset
                        # actuaizamos
                        bloque.redibujar()
                    else:
                        # si el struc esta vacion, el bloque desaparece
                        self.remove(bloque)

                # cuando se complete una línea, se desplazan todos los bloques
                for bloque in self:
                    if bloque.actual:
                        continue
                        # se llevan abajo los demas bloques
                    while True:
                        try:
                            bloque.mover_abajo(self)
                        except AbajoAlcanzado:
                            break

                self.actualizar_cuad()
                # se comprueba si hay más líneas completadas
                self._chequea_linea()
                break

    def actualizar_cuad(self):
        self._reset_cuadricula()

        for bloque in self:
            for y_offset, row in enumerate(bloque.struct):
                for x_offset, numero in enumerate(row):
                    # evitamos que el remplazo de bloques anteriores
                    if numero == 0:
                        continue
                    fila = bloque.y + y_offset
                    colum = bloque.x + x_offset
                    self.cuad[fila][colum] = (bloque, y_offset)

    def _reset_cuadricula(self):
        self.cuad = [[0 for _ in range(10)] for _ in range(20)]

    def _crear_bloque(self):
        bloque_nuevo = self.bloque_siguiente or GrupoBloques.coger_random()

        if Bloque.colision(bloque_nuevo, self):
            raise ArribaAlcanzado

        self.add(bloque_nuevo)
        self.bloque_siguiente = GrupoBloques.coger_random()

        self.actualizar_cuad()
        self._chequea_linea()

    def actualizar_bloque_actual(self):
        try:
            self.bloque_actual.mover_abajo(self)
        except AbajoAlcanzado:
            self.parar_moviviento_bloque_actual()
            self._crear_bloque()
        else:
            self.actualizar_cuad()

    def mover_bloque_actual(self):
        # se mira si hay algo que mover
        if self._rumbo_bloque_actual is None:
            return
        action = {
            pygame.K_DOWN: self.bloque_actual.mover_abajo,
            pygame.K_LEFT: self.bloque_actual.mover_izquierda,
            pygame.K_RIGHT: self.bloque_actual.mover_derecha
        }

        try:
            # todas las funciones necesitan el group como primer argumento para comprobar la colision
            action[self._rumbo_bloque_actual](self)
        except AbajoAlcanzado:
            self.parar_moviviento_bloque_actual()
            self._crear_bloque()
        else:
            self.actualizar_cuad()

    def iniciar_movimiento_bloque_actual(self, key):
        if self._rumbo_bloque_actual is not None:
            self._ignorar = True
        self._rumbo_bloque_actual = key

    def parar_moviviento_bloque_actual(self):
        if self._ignorar:
            self._ignorar = False
        else:
            self._rumbo_bloque_actual = None

    def rotar_bloque_actual(self):
        # mirar si es un cuadrado
        if not isinstance(self.bloque_actual, BloqueCuadrado):
            self.bloque_actual.rotar(self)
            self.actualizar_cuad()

    def aumentar_velocidad(self):
        self.bloque_actual.velocidad = 2


# METODO PARA DIBUJAR LA CUADRICULA DEL FONDO
def dibuja_cuadricula(fondo):
    color = (50, 50, 50)

    # lineas verticules:
    for i in range(11):
        x = TIT_SIZE * i
        pygame.draw.line(fondo, color, (x, 0), (x, CUAD_HEIGHT))
        # (fondo, color, posicion de inicio(vector), posicion final(vector))

    # lineas horizontales
    for i in range(21):
        y = TIT_SIZE * i
        pygame.draw.line(fondo, color, (0, y), (CUAD_WIDTH, y))


# METODO PARA ACTUALIZAR EL FONDO
def dibujar_superficies(pantalla, surface, y):
    pantalla.blit(surface, (400 - surface.get_width()/2, y))  # va dibujando el fondo (va actualizando la superficie)


# METODO PARA CREAR UN MENU DE INICIO
def crea_otra_pantalla():

    pantalla_inicial = pygame.display.set_mode((PAN_WIDTH, PAN_HEIGHT))
    iniciar = False  # variable para iniciar el juego
    salir = False  # variable para salir

    # fondo inicial
    fondo_inicial = pygame.Surface(pantalla_inicial.get_size())
    pygame.Surface.convert(fondo_inicial)
    color_fondo_inicial = (255, 230, 50)
    fondo_inicial.fill(color_fondo_inicial)

    try:
        font = pygame.font.Font("Action_Man.ttf", 20)
    except OSError:
        pass

    try:
        font_titulo = pygame.font.Font("Action_Man.ttf", 50)  # font especifico para ampliar el título
    except OSError:
        pass
    titulo = font_titulo.render(
        "PYNATRIX", True, (0, 152, 70), color_fondo_inicial)
    texto_iniciar = font.render(
        "Para comenzar pulsa ", True, (0, 0, 0), color_fondo_inicial)
    texto_controles = font.render(
        "Controles:", True, (0, 0, 0), color_fondo_inicial)
    texto_salir = font.render(
        "Para salir pulsa ", True, (0, 0, 0), color_fondo_inicial)
    texto_uno = font.render(
        "mueven la pieza", True, (0, 0, 0), color_fondo_inicial)
    texto_dos = font.render(
        "rota la pieza", True, (0, 0, 0), color_fondo_inicial)
    texto_tres = font.render(
        "termina el juego", True, (0, 0, 0), color_fondo_inicial)
    texto_cuatro = font.render(
        "pausa el juego", True, (0, 0, 0), color_fondo_inicial)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                salir = not salir
                break
            elif event.type == pygame.KEYUP:
                if not iniciar and not salir:
                    if event.key == pygame.K_i:  # si se usa I se inicia
                        iniciar = not iniciar
                    elif event.key == pygame.K_s:  # si se usa S se sale
                        salir = not salir

        # lista con todas las imagenes que apareceran en pantalla
        img = []
        img.append(pygame.image.load("imagenes/izquierda.png"))
        img.append(pygame.image.load("imagenes/derecha.png"))
        img.append(pygame.image.load("imagenes/arriba.png"))
        img.append(pygame.image.load("imagenes/abajo.png"))
        img.append(pygame.image.load("imagenes/s.png"))
        img.append(pygame.image.load("imagenes/i.png"))
        img.append(pygame.image.load("imagenes/q.png"))
        img.append(pygame.image.load("imagenes/p.png"))

        pantalla_inicial.blit(fondo_inicial, (0, 0))

        pantalla_inicial.blit(titulo, (150, 50))

        pantalla_inicial.blit(texto_iniciar, (100, 200))

        tux = img[5]
        picture = pygame.transform.scale(tux, (30, 30))  # redimensiona la imagen
        pantalla_inicial.blit(picture, (300, 200))

        pantalla_inicial.blit(texto_salir, (100, 250))

        tux = img[4]
        picture = pygame.transform.scale(tux, (30, 30))
        pantalla_inicial.blit(picture, (260, 250))

        pantalla_inicial.blit(texto_controles, (5, 350))

        tux = img[0]
        picture = pygame.transform.scale(tux, (30, 30))
        pantalla_inicial.blit(picture, (5, 400))
        tux = img[1]
        picture = pygame.transform.scale(tux, (30, 30))
        pantalla_inicial.blit(picture, (35, 400))
        tux = img[3]
        picture = pygame.transform.scale(tux, (30, 30))
        pantalla_inicial.blit(picture, (65, 400))

        pantalla_inicial.blit(texto_uno, (105, 400))

        tux = img[2]
        picture = pygame.transform.scale(tux, (30, 30))
        pantalla_inicial.blit(picture, (5, 450))

        pantalla_inicial.blit(texto_dos, (45, 450))

        tux = img[6]
        picture = pygame.transform.scale(tux, (30, 30))
        pantalla_inicial.blit(picture, (5, 500))

        pantalla_inicial.blit(texto_tres, (45, 500))

        tux = img[7]
        picture = pygame.transform.scale(tux, (30, 30))
        pantalla_inicial.blit(picture, (5, 550))

        pantalla_inicial.blit(texto_cuatro, (45, 550))

        pygame.display.flip()

        if iniciar:
            return 'i'

        if salir:
            return 's'


def main():
    pygame.init()

    pygame.display.set_caption("PYNATRIX")

    # 1º MEJORA
    opcion = crea_otra_pantalla()

    if opcion == 's':
        pygame.quit()
    elif opcion == 'i':
        pantalla = pygame.display.set_mode((PAN_WIDTH, PAN_HEIGHT))  # variable para definir el tamaño de la pantalla
        run = True  # variable para correr el programa
        pausa = False  # variable para pausar el programa
        end_game = False  # variable para finalizar el programa

        # FONDO
        fondo = pygame.Surface(pantalla.get_size())  # definimos el tamaño del fondo (creamos la superficie)
        color_fondo = (0, 0, 0)  # variable para guardar el color del fondo
        fondo.fill(color_fondo)  # definimos el color del fondo

        # CUADRICULA PARA EL FONDO
        dibuja_cuadricula(fondo)

        try:
            font = pygame.font.Font("Action_Man.ttf", 20)
        except OSError:
            pass  # hace que el programa ignore eso y siga leyendo el código

        try:
            font_dos = pygame.font.Font("Action_Man.ttf", 30)
        except OSError:
            pass
        titulo = font_dos.render(
            "PYNATRIX", True, (0, 152, 70), color_fondo)
        texto_fig_sig = font.render(
            "Siguiente figura:", True, (255, 230, 50), color_fondo)
        texto_punt = font.render(
            "Puntuación:", True, (255, 230, 50), color_fondo)
        texto_game_over = font_dos.render(
            "¡GAME OVER!", True, (255, 0, 0), color_fondo)
        texto_pausa = font.render(
            "Juego pausado", True, (255, 220, 0), color_fondo)
        texto_velocidad = font.render(
            "Nivel avanzado", True, (255, 220, 0), color_fondo)

        # variables de evento
        keys_movimientos = pygame.K_LEFT, pygame.K_RIGHT, pygame.K_DOWN
        evento_actualizar_bloque_actual = pygame.USEREVENT + 1
        evento_mover_bloque_actual = pygame.USEREVENT + 2
        pygame.time.set_timer(evento_actualizar_bloque_actual, 1000)
        pygame.time.set_timer(evento_mover_bloque_actual, 100)

        bloques = GrupoBloques()  # variable para sacar los bloques

        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    break
                elif event.type == pygame.KEYUP:
                    if not pausa and not end_game:
                        if event.key in keys_movimientos:  # si se usa las teclas seleccionadas para mover la pieza
                            bloques.parar_moviviento_bloque_actual()
                        elif event.key == pygame.K_UP:  # si se la flecha hacia arriba se rota
                            bloques.rotar_bloque_actual()

                    if event.key == pygame.K_p:  # si se usa P se pausa
                        pausa = not pausa

                    if event.key == pygame.K_q:  # si se usa Q se acaba
                        end_game = True
                        break

                if end_game or pausa:
                    continue

                if event.type == pygame.KEYDOWN:
                    if event.key in keys_movimientos:
                        bloques.iniciar_movimiento_bloque_actual(event.key)

                try:
                    if event.type == evento_actualizar_bloque_actual:
                        bloques.actualizar_bloque_actual()
                    elif event.type == evento_mover_bloque_actual:
                        bloques.mover_bloque_actual()
                except ArribaAlcanzado:
                    end_game = True

            # dibujamos el fondo y la cuadricula
            pantalla.blit(fondo, (0, 0))
            # bloques
            bloques.draw(pantalla)
            # barra lateral
            dibujar_superficies(pantalla, titulo, 60)
            dibujar_superficies(pantalla, texto_fig_sig, 200)
            dibujar_superficies(pantalla, bloques.bloque_siguiente.image, 250)
            dibujar_superficies(pantalla, texto_punt, 470)
            puntuacion = font_dos.render(str(bloques.puntuacion), True, (255, 230, 50), color_fondo)
            dibujar_superficies(pantalla, puntuacion, 500)

            # 2º MEJORA
            '''
            if bloques.puntuacion > 5:
                bloques.aumentar_velocidad()
                dibujar_superficies(pantalla, texto_velocidad, 400)
            '''

            if pausa:
                dibujar_superficies(pantalla, texto_pausa, 400)

            if end_game:
                dibujar_superficies(pantalla, texto_game_over, 400)

            # actualizamos
            pygame.display.flip()

        pygame.quit()


if __name__ == '__main__':
    main()
