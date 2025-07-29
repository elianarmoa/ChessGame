import os
import pygame
import chess_engine  # Importa tu motor de ajedrez, que contiene la lógica del juego.
import chess_ai  # Importa el módulo de inteligencia artificial.
import sys

def obtener_ruta_recurso(rel_path):
    """Devuelve la ruta absoluta, compatible con PyInstaller."""
    try:
        base_path = sys._MEIPASS  # carpeta temporal de PyInstaller
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, rel_path)

# --- Configuración de la Ventana y Tablero ---
ANCHO_PANTALLA = ALTO_PANTALLA = 800  # Dimensiones de la ventana del juego (cuadrada).
DIMENSION = 8  # El tablero de ajedrez es de 8x8 casillas.
TAMANIO_CASILLA = ALTO_PANTALLA // DIMENSION  # Calcula el tamaño de cada casilla en píxeles (512 / 8 = 64px).
IMAGENES = {}  # Diccionario global para almacenar las imágenes de las piezas, cargadas una vez al inicio.
FPS_MAX = 60  # Límite de fotogramas por segundo para la actualización de la pantalla.

# Definición de colores para el tablero y elementos de la interfaz de usuario.
# Colores de tablero de ajedrez modernos y suaves (tonos de madera/grisáceos)
COLOR_CLARO = (238, 238, 210)         # Un beige claro cálido (similar a la madera clara)
COLOR_OSCURO = (118, 150, 86)         # Un verde oscuro/oliva (similar a la madera oscura o un tablero temático)

# Colores de resaltado con transparencia para una estética más pulida
COLOR_RESALTE = (255, 255, 0, 100)    # Amarillo brillante semitransparente para la casilla seleccionada
COLOR_MOVIMIENTO_NORMAL = (100, 100, 255, 120)  # Azul claro semitransparente para movimientos normales
COLOR_MOVIMIENTO_CAPTURAS = (255, 50, 50, 120)  # Rojo ligeramente menos intenso semitransparente para capturas
COLOR_JAQUE = (255, 50, 50)           # Rojo intenso para resaltar el rey en jaque (sin transparencia para mayor impacto)

# Colores adicionales para el menú y fondo general
COLOR_TEXTO_MENU = (255, 255, 255)    # Blanco para el texto del menú
COLOR_FONDO_MENU = (30, 30, 30)       # Gris muy oscuro, casi negro, para un fondo elegante
COLOR_BOTON_NORMAL = (70, 70, 70)     # Gris intermedio para los botones
COLOR_BOTON_HOVER = (120, 120, 120)   # Gris más claro para el efecto hover del botón
COLOR_FONDO_ETIQUETA = (0, 0, 0, 100) # Negro semitransparente para el fondo de las etiquetas (nueva constante)


# --- Estados del Juego ---
MENU_STATE = 0
GAME_STATE = 1

# --- Variables de Configuración de la IA ---
JUGADOR_HUMANO_BLANCAS = True
JUGADOR_HUMANO_NEGRAS = False


def cargar_imagenes():
    """
    Carga todas las imágenes de las piezas de ajedrez y las escala al tamaño de la casilla.
    Las imágenes deben estar en una carpeta 'images/' dentro del directorio del script.
    Las imágenes se almacenan en el diccionario global IMAGENES para acceso rápido.
    """
    piezas = ['wp', 'wr', 'wn', 'wb', 'wq', 'wk', 'bp', 'br', 'bn', 'bb', 'bq', 'bk']
    for pieza in piezas:
        try:
            IMAGENES[pieza] = pygame.transform.scale(
                pygame.image.load(obtener_ruta_recurso("images/" + pieza + ".png")),
                (TAMANIO_CASILLA, TAMANIO_CASILLA)
            )
        except pygame.error as e:
            print(f"Error cargando imagen de pieza {pieza}: {e}")
            IMAGENES[pieza] = pygame.Surface((TAMANIO_CASILLA, TAMANIO_CASILLA), pygame.SRCALPHA)
            IMAGENES[pieza].fill((255, 0, 255)) # Color magenta para indicar pieza faltante

def dibujar_menu(pantalla):
    """
    Dibuja el menú principal del juego en la pantalla con un estilo mejorado.
    Muestra el título del juego y botones interactivos para "Jugar" y "Salir".
    """
    pantalla.fill(COLOR_FONDO_MENU)
    # Usamos una fuente predeterminada de Pygame con un tamaño generoso para el título
    fuente_titulo = pygame.font.SysFont("Arial", 72, True, False) # Arial como opción común
    fuente_boton = pygame.font.SysFont("Arial", 36, True, False) # Arial para botones

    # Dibuja el título del juego con un ligero borde o sombra (simulado con dos textos)
    titulo_obj = fuente_titulo.render("A J E D R E Z", True, (200, 200, 200)) # Un gris más claro para el título
    titulo_rect = titulo_obj.get_rect(center=(ANCHO_PANTALLA // 2, ALTO_PANTALLA // 4))
    # Sombra ligera
    pantalla.blit(fuente_titulo.render("A J E D R E Z", True, (50, 50, 50)), (titulo_rect.x + 2, titulo_rect.y + 2))
    pantalla.blit(titulo_obj, titulo_rect)


    # Define las propiedades de los botones.
    # Los botones son más grandes para una mejor interacción táctil o con el ratón.
    botones = {
        "Jugar": pygame.Rect(ANCHO_PANTALLA // 2 - 120, ALTO_PANTALLA // 2 - 40, 240, 70),
        "Salir": pygame.Rect(ANCHO_PANTALLA // 2 - 120, ALTO_PANTALLA // 2 + 60, 240, 70)
    }

    pos_mouse = pygame.mouse.get_pos()

    for texto, rect in botones.items():
        color_boton = COLOR_BOTON_NORMAL
        if rect.collidepoint(pos_mouse):
            color_boton = COLOR_BOTON_HOVER
        pygame.draw.rect(pantalla, color_boton, rect, border_radius=15) # Bordes más redondeados

        texto_obj = fuente_boton.render(texto, True, COLOR_TEXTO_MENU)
        texto_rect = texto_obj.get_rect(center=rect.center)
        pantalla.blit(texto_obj, texto_rect)

    pygame.display.flip()


def manejar_clicks_menu(pos_mouse):
    """
    Maneja los clicks del ratón en el menú principal.
    Determina qué botón fue clickeado y retorna el nuevo estado del juego o una señal de salida.
    Args:
        pos_mouse (tuple): Coordenadas (x, y) del click del ratón.
    Returns:
        int or str or None: El nuevo estado del juego (GAME_STATE), "QUIT" para salir, o None si no hay cambio.
    """
    botones = {
        "Jugar": pygame.Rect(ANCHO_PANTALLA // 2 - 120, ALTO_PANTALLA // 2 - 40, 240, 70),
        "Salir": pygame.Rect(ANCHO_PANTALLA // 2 - 120, ALTO_PANTALLA // 2 + 60, 240, 70)
    }

    if botones["Jugar"].collidepoint(pos_mouse):
        return GAME_STATE
    elif botones["Salir"].collidepoint(pos_mouse):
        return "QUIT"
    return None


def main():
    """
    Función principal que inicializa Pygame y ejecuta el bucle principal del juego de ajedrez.
    Gestiona el flujo entre el menú y el juego, la interacción del usuario, la IA y el renderizado.
    """
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO_PANTALLA, ALTO_PANTALLA))
    pygame.display.set_caption("Ajedrez Definitivo") # Nuevo título para la ventana
    reloj = pygame.time.Clock()

    cargar_imagenes()

    estado_juego_actual = MENU_STATE

    juego_actual = None
    movimientos_legales = []
    movimiento_hecho = False
    sq_seleccionado = ()
    clicks_jugador = []
    pieza_arrastrando = None
    pos_original_arrastrando = ()

    corriendo = True

    while corriendo:
        turno_ia = (juego_actual and juego_actual.turno_blancas and not JUGADOR_HUMANO_BLANCAS) or \
                   (juego_actual and not juego_actual.turno_blancas and not JUGADOR_HUMANO_NEGRAS)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                corriendo = False

            if estado_juego_actual == MENU_STATE:
                if evento.type == pygame.MOUSEBUTTONDOWN:
                    if evento.button == 1:
                        nuevo_estado = manejar_clicks_menu(pygame.mouse.get_pos())
                        if nuevo_estado == GAME_STATE:
                            estado_juego_actual = GAME_STATE
                            juego_actual = chess_engine.EstadoJuego()
                            movimientos_legales = juego_actual.obtener_movimientos_legales()
                            juego_actual.actualizar_pins_y_checks()

                            # --- DEBUGGING: Mensajes iniciales más limpios ---
                            print("\n--- INICIO DE JUEGO ---")
                            print(f"Juego iniciado. Turno de las {'Blancas' if juego_actual.turno_blancas else 'Negras'}.")
                            # --- FIN DEBUGGING ---

                            movimiento_hecho = False
                            sq_seleccionado = ()
                            clicks_jugador = []
                            pieza_arrastrando = None
                            pos_original_arrastrando = ()
                        elif nuevo_estado == "QUIT":
                            corriendo = False

            elif estado_juego_actual == GAME_STATE:
                if not juego_actual.jaque_mate and not juego_actual.ahogado and not turno_ia:
                    if evento.type == pygame.MOUSEBUTTONDOWN:
                        if evento.button == 1:
                            pos_raton = pygame.mouse.get_pos()
                            col_seleccionada = pos_raton[0] // TAMANIO_CASILLA
                            fila_seleccionada = pos_raton[1] // TAMANIO_CASILLA

                            # Asegúrate de que la casilla esté dentro de los límites del tablero
                            if 0 <= fila_seleccionada < DIMENSION and 0 <= col_seleccionada < DIMENSION:
                                pieza_a_mover = juego_actual.tablero[fila_seleccionada][col_seleccionada]
                                if (juego_actual.turno_blancas and pieza_a_mover[0] == 'w') or \
                                   (not juego_actual.turno_blancas and pieza_a_mover[0] == 'b'):
                                    sq_seleccionado = (fila_seleccionada, col_seleccionada)
                                    pieza_arrastrando = IMAGENES.get(pieza_a_mover) # Usa .get para evitar KeyError si la imagen no se cargó
                                    pos_original_arrastrando = (col_seleccionada * TAMANIO_CASILLA, fila_seleccionada * TAMANIO_CASILLA)
                                    clicks_jugador = [sq_seleccionado]

                    elif evento.type == pygame.MOUSEBUTTONUP:
                        if evento.button == 1:
                            if pieza_arrastrando:
                                pos_raton = pygame.mouse.get_pos()
                                col_destino = pos_raton[0] // TAMANIO_CASILLA
                                fila_destino = pos_raton[1] // TAMANIO_CASILLA

                                # Asegúrate de que la casilla de destino esté dentro de los límites del tablero
                                if 0 <= fila_destino < DIMENSION and 0 <= col_destino < DIMENSION:
                                    if sq_seleccionado != (fila_destino, col_destino):
                                        clicks_jugador.append((fila_destino, col_destino))
                                        movimiento = chess_engine.Movimiento(clicks_jugador[0], clicks_jugador[1], juego_actual.tablero)

                                        # --- DEBUGGING: Imprimir movimiento intentado ---
                                        # print(f"Intento de movimiento: {movimiento}")
                                        if movimiento in movimientos_legales:
                                            # print(f"Movimiento {movimiento} ES legal.")
                                            juego_actual.hacer_movimiento(movimiento)
                                            movimiento_hecho = True
                                        else:
                                            # print(f"Movimiento {movimiento} NO ES legal.")
                                            pass # No es necesario imprimir para cada movimiento ilegal
                                else:
                                    # Si el click final está fuera del tablero, considerar como un intento de cancelar el arrastre
                                    pass

                                sq_seleccionado = ()
                                clicks_jugador = []
                                pieza_arrastrando = None
                                pos_original_arrastrando = ()
                            else:
                                pos_raton = pygame.mouse.get_pos()
                                col_clic = pos_raton[0] // TAMANIO_CASILLA
                                fila_clic = pos_raton[1] // TAMANIO_CASILLA

                                # Asegúrate de que la casilla clickeada esté dentro de los límites del tablero
                                if 0 <= fila_clic < DIMENSION and 0 <= col_clic < DIMENSION:
                                    if sq_seleccionado == (fila_clic, col_clic):
                                        sq_seleccionado = ()
                                        clicks_jugador = []
                                    else:
                                        sq_seleccionado = (fila_clic, col_clic)
                                        clicks_jugador = [sq_seleccionado]
                                # --- DEBUGGING: Imprimir movimientos legales de la pieza seleccionada (opcional) ---
                                # if sq_seleccionado != ():
                                #     pieza_en_sq = juego_actual.tablero[sq_seleccionado[0]][sq_seleccionado[1]]
                                #     print(f"Casilla seleccionada: {sq_seleccionado}, Pieza: {pieza_en_sq}")
                                #     movs_para_pieza_seleccionada = [
                                #         mov for mov in movimientos_legales
                                #         if mov.fila_inicial == sq_seleccionado[0] and mov.col_inicial == sq_seleccionado[1]
                                #     ]
                                #     print(f"Movimientos legales para {pieza_en_sq} en {sq_seleccionado}: {len(movs_para_pieza_seleccionada)}")
                                # --- FIN DEBUGGING ---

                    elif evento.type == pygame.MOUSEMOTION:
                        if pieza_arrastrando:
                            # No se necesita lógica adicional aquí, el dibujo se encarga.
                            pass

                    elif evento.type == pygame.KEYDOWN:
                        if evento.key == pygame.K_z:
                            juego_actual.deshacer_movimiento()
                            movimiento_hecho = True
                            sq_seleccionado = ()
                            clicks_jugador = []
                            pieza_arrastrando = None
                            pos_original_arrastrando = ()
                            print("Movimiento deshecho.")
                        if evento.key == pygame.K_r:
                            juego_actual = chess_engine.EstadoJuego()
                            movimientos_legales = juego_actual.obtener_movimientos_legales()
                            juego_actual.actualizar_pins_y_checks()
                            sq_seleccionado = ()
                            clicks_jugador = []
                            movimiento_hecho = False
                            pieza_arrastrando = None
                            pos_original_arrastrando = ()
                            print("Juego reiniciado.")
                        if evento.key == pygame.K_ESCAPE:
                            estado_juego_actual = MENU_STATE
                            juego_actual = None
                            movimientos_legales = []
                            movimiento_hecho = False
                            sq_seleccionado = ()
                            clicks_jugador = []
                            pieza_arrastrando = None
                            pos_original_arrastrando = ()
                            print("Volviendo al menú principal.")

        # --- LÓGICA DE LA IA ---
        if estado_juego_actual == GAME_STATE and not juego_actual.jaque_mate and not juego_actual.ahogado and turno_ia:
            print("IA pensando...")

            movimiento_ia = chess_ai.find_best_move(juego_actual)

            if movimiento_ia:
                print(f"La IA hará el movimiento: {movimiento_ia}")
                juego_actual.hacer_movimiento(movimiento_ia)
                movimiento_hecho = True
            else:
                print("IA no encontró movimientos válidos o el juego terminó (inesperado).")

            print("IA terminó de pensar.")

        # --- Lógica de Dibujo según el estado del juego ---
        if estado_juego_actual == MENU_STATE:
            dibujar_menu(pantalla)
        elif estado_juego_actual == GAME_STATE:
            if movimiento_hecho:
                movimientos_legales = juego_actual.obtener_movimientos_legales()
                movimiento_hecho = False
                juego_actual.actualizar_pins_y_checks()

                # --- DEBUGGING: Mensajes de turno más limpios ---
                print(f"Turno de las {'Blancas' if juego_actual.turno_blancas else 'Negras'}.")
                # --- FIN DEBUGGING ---

                if len(movimientos_legales) == 0:
                    if juego_actual.jaque:
                        juego_actual.jaque_mate = True
                    else:
                        juego_actual.ahogado = True

            dibujar_estado_juego(pantalla, juego_actual, sq_seleccionado, movimientos_legales, pieza_arrastrando, pos_original_arrastrando)

            if juego_actual.jaque_mate:
                texto_jaque_mate = "JAQUE MATE! " + ("Blancas Ganan" if not juego_actual.turno_blancas else "Negras Ganan")
                dibujar_texto_centro(pantalla, texto_jaque_mate, color_texto=pygame.Color('Red')) # Texto rojo para jaque mate
            elif juego_actual.ahogado:
                dibujar_texto_centro(pantalla, "TABLAS por AHOGADO!", color_texto=pygame.Color('Blue')) # Texto azul para ahogado
            elif juego_actual.jaque:
                dibujar_texto_centro(pantalla, "¡JAQUE!", color_texto=pygame.Color('Orange')) # Texto naranja para jaque

            pygame.display.flip()

        reloj.tick(FPS_MAX)


def dibujar_estado_juego(pantalla, juego, sq_seleccionado, movimientos_legales, pieza_arrastrando, pos_original_arrastrando):
    """
    Coordina el dibujo de todos los elementos visuales del tablero de ajedrez.
    Args:
        pantalla (pygame.Surface): La superficie de Pygame donde se dibujará.
        juego (chess_engine.EstadoJuego): El objeto que contiene el estado actual del juego.
        sq_seleccionado (tuple): Casilla (fila, col) seleccionada por el jugador.
        movimientos_legales (list): Lista de objetos Movimiento que son legales para el turno actual.
        pieza_arrastrando (pygame.Surface): La imagen de la pieza que se está arrastrando (None si no hay).
        pos_original_arrastrando (tuple): Posición (x, y) original de la pieza que se arrastra.
    """
    dibujar_tablero(pantalla)
    resaltar_casillas(pantalla, juego, sq_seleccionado, movimientos_legales)
    dibujar_piezas(pantalla, juego.tablero, pieza_arrastrando, sq_seleccionado, pos_original_arrastrando)
    dibujar_etiquetas_filas_columnas(pantalla) # Dibujar etiquetas al final para que estén por encima de todo


def dibujar_tablero(pantalla):
    """
    Dibuja las casillas alternadas del tablero de ajedrez.
    Args:
        pantalla (pygame.Surface): La superficie de Pygame donde se dibujará.
    """
    for fila in range(DIMENSION):
        for col in range(DIMENSION):
            color = COLOR_CLARO if (fila + col) % 2 == 0 else COLOR_OSCURO
            pygame.draw.rect(pantalla, color, pygame.Rect(col * TAMANIO_CASILLA, fila * TAMANIO_CASILLA, TAMANIO_CASILLA, TAMANIO_CASILLA))


def dibujar_etiquetas_filas_columnas(pantalla):
    """
    Dibuja las etiquetas numéricas (1-8) y alfabéticas (a-h) alrededor del tablero.
    Incluye un fondo semitransparente para mayor legibilidad.
    Args:
        pantalla (pygame.Surface): La superficie de Pygame donde se dibujará.
    """
    fuente = pygame.font.SysFont("Arial", 14, bold=True) # Fuente un poco más moderna para las etiquetas

    # Crea una superficie para el fondo de las etiquetas (para dibujar una sola vez y usarla)
    # Suponemos que el tamaño máximo de una etiqueta será de 20x20 píxeles, ajusta si es necesario
    fondo_etiqueta_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
    fondo_etiqueta_surf.fill(COLOR_FONDO_ETIQUETA) # Color de fondo semi-transparente


    # Etiquetas de columnas (a-h)
    for col in range(DIMENSION):
        letra = chr(ord('a') + col)
        texto_obj = fuente.render(letra, True, (240, 240, 240)) # Blanco grisáceo para mejor contraste

        # Inferior (para blancas)
        pos_x_inferior = col * TAMANIO_CASILLA + TAMANIO_CASILLA // 2
        pos_y_inferior = ALTO_PANTALLA - 15 # Más cerca del borde inferior
        rect_inferior = texto_obj.get_rect(center=(pos_x_inferior, pos_y_inferior))
        pantalla.blit(texto_obj, rect_inferior)

        # Superior (para negras)
        pos_x_superior = col * TAMANIO_CASILLA + TAMANIO_CASILLA // 2
        pos_y_superior = 15 # Más cerca del borde superior
        rect_superior = texto_obj.get_rect(center=(pos_x_superior, pos_y_superior))
        pantalla.blit(texto_obj, rect_superior)


    # Etiquetas de filas (1-8)
    for fila in range(DIMENSION):
        numero = str(8 - fila)
        texto_obj = fuente.render(numero, True, (240, 240, 240)) # Blanco grisáceo

        # Derecha (para blancas)
        pos_x_derecha = ANCHO_PANTALLA - 15
        pos_y_derecha = fila * TAMANIO_CASILLA + TAMANIO_CASILLA // 2
        rect_derecha = texto_obj.get_rect(center=(pos_x_derecha, pos_y_derecha))
        pantalla.blit(texto_obj, rect_derecha)

        # Izquierda (para negras)
        pos_x_izquierda = 15
        pos_y_izquierda = fila * TAMANIO_CASILLA + TAMANIO_CASILLA // 2
        rect_izquierda = texto_obj.get_rect(center=(pos_x_izquierda, pos_y_izquierda))
        pantalla.blit(texto_obj, rect_izquierda)


def resaltar_casillas(pantalla, juego, sq_seleccionado, movimientos_legales):
    """
    Resalta la casilla actualmente seleccionada por el jugador y las casillas
    a las que la pieza seleccionada puede moverse legalmente.
    También resalta el rey si está en jaque.
    Args:
        pantalla (pygame.Surface): La superficie de Pygame donde se dibujará.
        juego (chess_engine.EstadoJuego): El objeto que contiene el estado actual del juego.
        sq_seleccionado (tuple): Casilla (fila, col) seleccionada por el jugador.
        movimientos_legales (list): Lista de objetos Movimiento que son legales para el turno actual.
    """
    # Resaltar la casilla seleccionada.
    if sq_seleccionado != ():
        fila, col = sq_seleccionado
        # Asegúrate de que la casilla seleccionada esté dentro de los límites y contenga una pieza
        if 0 <= fila < DIMENSION and 0 <= col < DIMENSION:
            pieza_seleccionada = juego.tablero[fila][col]
            if (juego.turno_blancas and pieza_seleccionada[0] == 'w') or \
               (not juego.turno_blancas and pieza_seleccionada[0] == 'b'):
                s = pygame.Surface((TAMANIO_CASILLA, TAMANIO_CASILLA), pygame.SRCALPHA)
                s.fill(COLOR_RESALTE)
                pantalla.blit(s, (col * TAMANIO_CASILLA, fila * TAMANIO_CASILLA))

                # Resaltar movimientos legales posibles desde la casilla seleccionada.
                for movimiento in movimientos_legales:
                    if movimiento.fila_inicial == fila and movimiento.col_inicial == col:
                        color_indicador_actual = COLOR_MOVIMIENTO_NORMAL
                        if juego.tablero[movimiento.fila_final][movimiento.col_final] != "--":
                            color_indicador_actual = COLOR_MOVIMIENTO_CAPTURAS

                        s_mov = pygame.Surface((TAMANIO_CASILLA, TAMANIO_CASILLA), pygame.SRCALPHA)
                        s_mov.fill(color_indicador_actual)
                        pantalla.blit(s_mov, (movimiento.col_final * TAMANIO_CASILLA, movimiento.fila_final * TAMANIO_CASILLA))

    # Resaltar el rey si está en jaque.
    if juego.jaque:
        # Asegúrate de que la posición del rey sea válida antes de intentar dibujarla
        if juego.turno_blancas and juego.pos_rey_blanco != (-1, -1): # Asumiendo -1,-1 como valor inválido
            fila_rey, col_rey = juego.pos_rey_blanco
        elif not juego.turno_blancas and juego.pos_rey_negro != (-1, -1):
            fila_rey, col_rey = juego.pos_rey_negro
        else: # Si no hay rey válido o no está en jaque, no hacer nada
            return

        s_jaque = pygame.Surface((TAMANIO_CASILLA, TAMANIO_CASILLA), pygame.SRCALPHA)
        s_jaque.fill(COLOR_JAQUE)
        pantalla.blit(s_jaque, (col_rey * TAMANIO_CASILLA, fila_rey * TAMANIO_CASILLA))


def dibujar_piezas(pantalla, tablero, pieza_arrastrando, sq_seleccionado, pos_original_arrastrando):
    """
    Dibuja todas las piezas en el tablero.
    Maneja el arrastre visual de una pieza si el jugador está moviendo una.
    Args:
        pantalla (pygame.Surface): La superficie de Pygame donde se dibujará.
        tablero (list): La representación 2D del tablero de ajedrez.
        pieza_arrastrando (pygame.Surface): La imagen de la pieza que se está arrastrando (None si no hay).
        sq_seleccionado (tuple): La casilla (fila, col) de la pieza que se está arrastrando.
        pos_original_arrastrando (tuple): La posición (x, y) en píxeles de la casilla de origen de la pieza arrastrada.
    """
    for fila in range(DIMENSION):
        for col in range(DIMENSION):
            pieza = tablero[fila][col]
            if pieza != "--":
                # No dibujamos la pieza en su posición original si se está arrastrando,
                # ya que se dibujará por separado sobre el cursor del ratón.
                if pieza_arrastrando and sq_seleccionado == (fila, col):
                    continue
                # Asegúrate de que la imagen exista en IMAGENES antes de intentar dibujarla
                if pieza in IMAGENES:
                    pantalla.blit(IMAGENES[pieza], pygame.Rect(col * TAMANIO_CASILLA, fila * TAMANIO_CASILLA, TAMANIO_CASILLA, TAMANIO_CASILLA))

    # Dibujar la pieza que se está arrastrando por encima de todas las demás.
    if pieza_arrastrando:
        pos_raton = pygame.mouse.get_pos()
        # Ajusta la posición de dibujo para que el centro de la pieza esté en el cursor.
        pantalla.blit(pieza_arrastrando, (pos_raton[0] - TAMANIO_CASILLA // 2, pos_raton[1] - TAMANIO_CASILLA // 2))


def dibujar_texto_centro(pantalla, texto, color_texto=None):
    """
    Dibuja texto centrado en la pantalla con un fondo semitransparente.
    Útil para mensajes de "Jaque Mate", "Ahogado", "Jaque".
    Args:
        pantalla (pygame.Surface): La superficie de Pygame donde se dibujará.
        texto (str): El texto a mostrar.
        color_texto (pygame.Color, optional): Color del texto. Por defecto, blanco.
    """
    if color_texto is None:
        color_texto = pygame.Color('White') # Color de texto predeterminado si no se especifica

    fuente = pygame.font.SysFont("Arial", 40, True, False) # Fuente más grande y moderna para mensajes
    texto_obj = fuente.render(texto, True, color_texto)
    texto_rect = texto_obj.get_rect(center=(ANCHO_PANTALLA // 2, ALTO_PANTALLA // 2))

    # Dibuja un fondo semitransparente y ligeramente más grande que el texto
    s = pygame.Surface((texto_rect.width + 40, texto_rect.height + 30), pygame.SRCALPHA) # Más padding
    s.fill((0, 0, 0, 180))  # Fondo negro con mayor opacidad

    # Dibuja el fondo centrado y luego el texto
    pantalla.blit(s, (texto_rect.left - 20, texto_rect.top - 15)) # Ajusta para el padding
    pantalla.blit(texto_obj, texto_rect)


# Ejecutar el juego si este archivo es el script principal.
if __name__ == "__main__":
    main()