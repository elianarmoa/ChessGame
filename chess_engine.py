# chess_engine.py

# Clase para representar un movimiento en ajedrez.
class Movimiento:
    # Mapeo de columnas a notación de ajedrez (a-h)
    ranks_a_filas = {"1": 7, "2": 6, "3": 5, "4": 4,
                     "5": 3, "6": 2, "7": 1, "8": 0}
    filas_a_ranks = {v: k for k, v in ranks_a_filas.items()} # Invertir el diccionario

    files_a_cols = {"a": 0, "b": 1, "c": 2, "d": 3,
                    "e": 4, "f": 5, "g": 6, "h": 7}
    cols_a_files = {v: k for k, v in files_a_cols.items()} # Invertir el diccionario

    def __init__(self, start_sq, end_sq, tablero, en_passant_posible=False, enroque_movimiento=False):
        # start_sq y end_sq son tuplas (fila, columna)
        self.fila_inicial = start_sq[0]
        self.col_inicial = start_sq[1]
        self.fila_final = end_sq[0]
        self.col_final = end_sq[1]
        # Obtenemos la pieza movida y la pieza capturada (si la hay)
        self.pieza_movida = tablero[self.fila_inicial][self.col_inicial]
        self.pieza_capturada = tablero[self.fila_final][self.col_final] # Podría ser "--" si no hay captura

        # Manejo de movimientos especiales
        self.es_promocion_peon = (self.pieza_movida[1] == 'p' and
                                  ((self.pieza_movida[0] == 'w' and self.fila_final == 0) or
                                   (self.pieza_movida[0] == 'b' and self.fila_final == 7)))
        self.es_en_passant_movimiento = en_passant_posible
        if self.es_en_passant_movimiento:
            # Si es en passant, la pieza capturada es el peón que pasó por la casilla adyacente
            # Asumimos que la pieza capturada es un peón del color opuesto
            self.pieza_capturada = "wp" if self.pieza_movida[0] == 'b' else "bp"

        self.es_movimiento_enroque = enroque_movimiento

        # Identificador único para el movimiento (útil para historial y evitar repeticiones)
        self.move_ID = self.fila_inicial * 1000 + self.col_inicial * 100 + \
                         self.fila_final * 10 + self.col_final

    # Sobreescribimos el método __eq__ para poder comparar objetos Movimiento
    def __eq__(self, other):
        if isinstance(other, Movimiento):
            return self.move_ID == other.move_ID
        return False

    def __hash__(self): # Importante para usar Movimiento en sets o como claves de diccionario
        return hash(self.move_ID)

    # Para imprimir el movimiento en notación estándar de ajedrez (e.g., "e2e4")
    def get_chess_notation(self):
        if self.es_movimiento_enroque:
            if self.col_final == 6: # Enroque corto
                return "O-O"
            elif self.col_final == 2: # Enroque largo
                return "O-O-O"

        notacion = self.get_rank_file(self.fila_inicial, self.col_inicial) + \
                     self.get_rank_file(self.fila_final, self.col_final)
        if self.es_promocion_peon:
            notacion += "=Q" # Por defecto promocionamos a Reina. Se puede hacer más flexible.
        return notacion

    def get_rank_file(self, r, c):
        return self.cols_a_files[c] + self.filas_a_ranks[r]

    def __str__(self): # Representación en string para depuración
        return f"({self.fila_inicial},{self.col_inicial})->({self.fila_final},{self.col_final})" \
               f" (Captura: {self.pieza_capturada})"


# Clase para rastrear el estado de los derechos de enroque.
class DerechosEnroque:
    def __init__(self, wks, wqs, bks, bqs):
        self.wks = wks # Rey blanco lado corto (King side)
        self.wqs = wqs # Rey blanco lado largo (Queen side)
        self.bks = bks # Rey negro lado corto
        self.bqs = bqs # Rey negro lado largo

    def copiar(self):
        return DerechosEnroque(self.wks, self.wqs, self.bks, self.bqs)

    def __eq__(self, other):
        if isinstance(other, DerechosEnroque):
            return self.wks == other.wks and self.wqs == other.wqs and \
                   self.bks == other.bks and self.bqs == other.bqs
        return False


# Clase que representa el estado actual del juego de ajedrez.
class EstadoJuego:
    def __init__(self):
        self.tablero = [
            ["br", "bn", "bb", "bq", "bk", "bb", "bn", "br"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wr", "wn", "wb", "wq", "wk", "wb", "wn", "wr"]
        ]
        self.turno_blancas = True # True si es el turno de las blancas, False si es el de las negras.
        self.historial_movimientos = [] # Para almacenar los movimientos que se realizan
        self.pos_en_passant_posible = () # Coordenadas de la casilla donde es posible el en passant
                                         # (fila, col) donde un peón puede capturar en passant.

        self.derechos_enroque_actuales = DerechosEnroque(True, True, True, True)
        self.historial_derechos_enroque = [self.derechos_enroque_actuales.copiar()] # Historial de derechos de enroque

        self.pos_rey_blanco = (7, 4)
        self.pos_rey_negro = (0, 4)
        self.jaque = False       # True si el rey actual está en jaque
        self.jaque_mate = False  # True si el juego terminó por jaque mate
        self.ahogado = False     # True si el juego terminó por ahogado (stalemate)
        self.pins = []           # Lista de piezas que están "clavadas" (pinned)
        self.checks = []         # Lista de casillas desde donde el rey está siendo atacado (check)

        # Al inicio del juego, calcula el estado inicial del jaque, pins y checks.
        # Es importante llamar a esto para que self.jaque esté correcto desde el principio
        # antes de que se obtengan los movimientos legales.
        self.actualizar_pins_y_checks()


    '''
    Toma un objeto Movimiento como parámetro y lo ejecuta (mueve la pieza).
    No se encarga de la validación del movimiento (si es legal o no).
    '''
    def hacer_movimiento(self, movimiento):
        """
        Realiza un movimiento en el tablero, actualizando el estado del juego.
        """
        self.tablero[movimiento.fila_inicial][movimiento.col_inicial] = "--"
        self.tablero[movimiento.fila_final][movimiento.col_final] = movimiento.pieza_movida
        self.historial_movimientos.append(movimiento) # Guarda el movimiento en el historial
        self.turno_blancas = not self.turno_blancas # Cambia el turno al siguiente jugador

        # Actualizar la posición del rey si se movió
        if movimiento.pieza_movida == 'wk':
            self.pos_rey_blanco = (movimiento.fila_final, movimiento.col_final)
        elif movimiento.pieza_movida == 'bk':
            self.pos_rey_negro = (movimiento.fila_final, movimiento.col_final)

        # Promoción de peón
        if movimiento.es_promocion_peon:
            # Por defecto, promocionamos a Reina. Se podría pedir al usuario elegir.
            self.tablero[movimiento.fila_final][movimiento.col_final] = movimiento.pieza_movida[0] + 'q'

        # Movimiento en passant
        if movimiento.es_en_passant_movimiento:
            # Eliminar el peón capturado en en passant
            # El peón capturado está en la fila inicial del peón que se movió, y en la columna final
            self.tablero[movimiento.fila_inicial][movimiento.col_final] = "--"

        # Actualizar pos_en_passant_posible
        if movimiento.pieza_movida[1] == 'p' and abs(movimiento.fila_inicial - movimiento.fila_final) == 2:
            self.pos_en_passant_posible = ((movimiento.fila_inicial + movimiento.fila_final) // 2, movimiento.col_inicial)
        else:
            self.pos_en_passant_posible = () # Resetear si el movimiento no es un avance de peón de dos casillas

        # Actualizar derechos de enroque
        self.actualizar_derechos_enroque(movimiento)
        self.historial_derechos_enroque.append(self.derechos_enroque_actuales.copiar())

        # Enroque
        if movimiento.es_movimiento_enroque:
            if movimiento.col_final == 6: # Enroque corto (King side)
                # Mover la torre: de (r,7) a (r,5)
                self.tablero[movimiento.fila_final][5] = self.tablero[movimiento.fila_final][7]
                self.tablero[movimiento.fila_final][7] = "--"
            else: # Enroque largo (Queen side)
                # Mover la torre: de (r,0) a (r,3)
                self.tablero[movimiento.fila_final][3] = self.tablero[movimiento.fila_final][0]
                self.tablero[movimiento.fila_final][0] = "--"

        # Al final de hacer_movimiento, siempre recalcular los pins y checks para el *nuevo* estado del tablero.
        # Esto es crucial para que self.jaque esté correcto para la siguiente verificación.
        self.actualizar_pins_y_checks()
        # jaque_mate y ahogado deben ser calculados DESPUÉS de obtener_movimientos_legales,
        # no aquí directamente. Se ponen en False para que se recalcule.
        self.jaque_mate = False 
        self.ahogado = False


    '''
    Deshace el último movimiento hecho.
    '''
    def deshacer_movimiento(self):
        if len(self.historial_movimientos) != 0: # Asegura que haya un movimiento para deshacer
            movimiento = self.historial_movimientos.pop() # Quita el último movimiento del historial
            self.tablero[movimiento.fila_inicial][movimiento.col_inicial] = movimiento.pieza_movida
            self.tablero[movimiento.fila_final][movimiento.col_final] = movimiento.pieza_capturada
            self.turno_blancas = not self.turno_blancas # Vuelve al turno del jugador anterior

            # Actualizar la posición del rey si se deshizo su movimiento
            if movimiento.pieza_movida == 'wk':
                self.pos_rey_blanco = (movimiento.fila_inicial, movimiento.col_inicial)
            elif movimiento.pieza_movida == 'bk':
                self.pos_rey_negro = (movimiento.fila_inicial, movimiento.col_inicial)

            # Deshacer en passant
            if movimiento.es_en_passant_movimiento:
                # El peón capturado en en passant se restaura en la fila inicial del peón que se movió, y en la columna final
                self.tablero[movimiento.fila_final][movimiento.col_final] = "--" # La casilla de destino del peón capturador ahora está vacía
                self.tablero[movimiento.fila_inicial][movimiento.col_final] = movimiento.pieza_capturada # Reponer el peón capturado

            # Deshacer promoción de peón (volver a peón)
            if movimiento.es_promocion_peon:
                self.tablero[movimiento.fila_final][movimiento.col_final] = movimiento.pieza_movida # Vuelve a ser un peón

            # Deshacer derechos de enroque
            self.historial_derechos_enroque.pop() # Eliminar los derechos de enroque actuales
            # Asegurarse de que no esté vacío antes de acceder
            if len(self.historial_derechos_enroque) > 0:
                self.derechos_enroque_actuales = self.historial_derechos_enroque[-1].copiar() # Restaurar los anteriores
            else: # Caso borde: deshaciendo el primer movimiento
                self.derechos_enroque_actuales = DerechosEnroque(True, True, True, True) # Resetear a los valores iniciales

            # Deshacer enroque
            if movimiento.es_movimiento_enroque:
                if movimiento.col_final == 6: # Enroque corto
                    self.tablero[movimiento.fila_final][7] = self.tablero[movimiento.fila_final][5] # Mover torre de vuelta
                    self.tablero[movimiento.fila_final][5] = "--"
                else: # Enroque largo
                    self.tablero[movimiento.fila_final][0] = self.tablero[movimiento.fila_final][3] # Mover torre de vuelta
                    self.tablero[movimiento.fila_final][3] = "--"

            # Resetear pos_en_passant_posible al estado correcto después de deshacer
            # Se debe basar en el movimiento *anterior* al que se acaba de deshacer
            if len(self.historial_movimientos) == 0:
                self.pos_en_passant_posible = ()
            else:
                ultimo_movimiento = self.historial_movimientos[-1]
                if ultimo_movimiento.pieza_movida[1] == 'p' and abs(ultimo_movimiento.fila_inicial - ultimo_movimiento.fila_final) == 2:
                    self.pos_en_passant_posible = ((ultimo_movimiento.fila_inicial + ultimo_movimiento.fila_final) // 2, ultimo_movimiento.col_inicial)
                else:
                    self.pos_en_passant_posible = ()

            # --- Después de deshacer el movimiento, recalcular el estado de jaque/mate/ahogado ---
            self.jaque_mate = False # Reseteamos al deshacer
            self.ahogado = False    # Reseteamos al deshacer
            self.actualizar_pins_y_checks() # Recalcular jaques y pins para el TURNO ACTUAL (que se acaba de restaurar)


    '''
    Actualiza los derechos de enroque basados en el movimiento.
    '''
    def actualizar_derechos_enroque(self, movimiento):
        # Si el rey blanco se mueve, pierde ambos derechos de enroque
        if movimiento.pieza_movida == 'wk':
            self.derechos_enroque_actuales.wks = False
            self.derechos_enroque_actuales.wqs = False
        # Si el rey negro se mueve, pierde ambos derechos de enroque
        elif movimiento.pieza_movida == 'bk':
            self.derechos_enroque_actuales.bks = False
            self.derechos_enroque_actuales.bqs = False
        # Si una torre se mueve de su posición inicial, pierde su derecho de enroque
        elif movimiento.pieza_movida == 'wr':
            if movimiento.fila_inicial == 7:
                if movimiento.col_inicial == 7: # Torre de rey blanco
                    self.derechos_enroque_actuales.wks = False
                elif movimiento.col_inicial == 0: # Torre de reina blanca
                    self.derechos_enroque_actuales.wqs = False
        elif movimiento.pieza_movida == 'br':
            if movimiento.fila_inicial == 0:
                if movimiento.col_inicial == 7: # Torre de rey negro
                    self.derechos_enroque_actuales.bks = False
                elif movimiento.col_inicial == 0: # Torre de reina negro
                    self.derechos_enroque_actuales.bqs = False

        # Si una torre es capturada en su posición inicial, el oponente pierde el derecho de enroque con esa torre
        # Nota: La pieza_capturada puede ser "--" si no hay captura
        if movimiento.pieza_capturada == 'wr':
            if movimiento.fila_final == 7:
                if movimiento.col_final == 7:
                    self.derechos_enroque_actuales.wks = False
                elif movimiento.col_final == 0:
                    self.derechos_enroque_actuales.wqs = False
        elif movimiento.pieza_capturada == 'br':
            if movimiento.fila_final == 0:
                if movimiento.col_final == 7:
                    self.derechos_enroque_actuales.bks = False
                elif movimiento.col_final == 0:
                    self.derechos_enroque_actuales.bqs = False

    '''
    Determina si el rey del jugador actual está en jaque, y qué piezas lo están atacando (checks)
    o clavando (pins). Esto es crucial para la validación de movimientos.
    '''
    def actualizar_pins_y_checks(self):
        # Reiniciar las listas de pins y checks
        self.pins = []
        self.checks = []
        self.jaque = False # Asumimos que no hay jaque al principio de la verificación

        # Determinar la posición del rey actual y su color
        if self.turno_blancas:
            fila_rey, col_rey = self.pos_rey_blanco
            color_propio = 'w'
            color_oponente = 'b'
        else:
            fila_rey, col_rey = self.pos_rey_negro
            color_propio = 'b'
            color_oponente = 'w'

        # Direcciones de ataque (lineales y diagonales)
        direcciones = ((-1, 0), (0, -1), (1, 0), (0, 1), # Arriba, izquierda, abajo, derecha (Torres/Reinas)
                       (-1, -1), (-1, 1), (1, -1), (1, 1)) # Diagonales (Alfiles/Reinas)
        
        # Recorrer las 8 direcciones para buscar atacantes lineales y diagonales
        for i, (dr, dc) in enumerate(direcciones):
            posible_pin = () # Almacena la ubicación de la pieza propia que podría estar clavada
            for j in range(1, 8): # Buscar hasta 7 casillas en cada dirección
                fila_final = fila_rey + dr * j
                col_final = col_rey + dc * j
                if 0 <= fila_final < 8 and 0 <= col_final < 8: # Dentro del tablero
                    pieza_en_casilla = self.tablero[fila_final][col_final]
                    if pieza_en_casilla == "--":
                        continue # Casilla vacía, sigue buscando
                    elif pieza_en_casilla[0] == color_propio: # Encontró una pieza propia
                        if posible_pin == (): # Si es la primera pieza propia encontrada en esta línea
                            posible_pin = (fila_final, col_final)
                        else: # Si ya encontramos una pieza propia, significa que hay dos, así que no puede haber un pin
                            break
                    else: # Encontró una pieza oponente
                        tipo_pieza_oponente = pieza_en_casilla[1]
                        
                        # Verifica si la pieza oponente ataca al rey
                        # 1. Atacantes lineales (Torre/Reina)
                        if i < 4 and (tipo_pieza_oponente == 'r' or tipo_pieza_oponente == 'q'):
                            if posible_pin == (): # No hay pieza propia intermedia, es un jaque directo
                                self.jaque = True
                                self.checks.append((fila_final, col_final))
                            else: # Hay una pieza propia intermedia, es un pin
                                self.pins.append(posible_pin)
                            break # Encontró un atacante, no seguir en esta dirección
                        
                        # 2. Atacantes diagonales (Alfil/Reina)
                        elif i >= 4 and (tipo_pieza_oponente == 'b' or tipo_pieza_oponente == 'q'):
                            if posible_pin == (): # Jaque directo
                                self.jaque = True
                                self.checks.append((fila_final, col_final))
                            else: # Pin
                                self.pins.append(posible_pin)
                            break
                        
                        # 3. Peones (ataque diagonal)
                        elif tipo_pieza_oponente == 'p':
                            # Dirección del peón hacia el rey:
                            # Peón blanco ataca hacia arriba (-1, -1) o (-1, 1)
                            # Peón negro ataca hacia abajo (1, -1) o (1, 1)
                            # Además, el peón solo ataca a una distancia de 1 casilla (j == 1)
                            if (color_propio == 'w' and dr == 1 and abs(dc) == 1 and j == 1) or \
                               (color_propio == 'b' and dr == -1 and abs(dc) == 1 and j == 1):
                                if posible_pin == (): # Peón no puede dar pin, solo jaque directo (y solo si está adyacente)
                                    self.jaque = True
                                    self.checks.append((fila_final, col_final))
                                break # Jaque de peón encontrado, no seguir en esta dirección
                            else: # Si es un peón que no está atacando en la dirección correcta o está lejos
                                break # Romper para evitar que un peón bloquee una línea de ataque de otra pieza
                        
                        # 4. Rey (ataque a distancia de 1, para detectar colisión de reyes)
                        elif tipo_pieza_oponente == 'k':
                            if j == 1: # Si el rey enemigo está a 1 casilla de distancia
                                # Esto es para evitar que un rey se mueva a una casilla adyacente al otro rey
                                # No resulta en jaque/pin en self.jaque/self.pins, es para validación de movimiento de rey
                                # Se detectará en cuadrado_bajo_ataque, pero aquí bloquea la línea de visión
                                pass # No añadimos a checks/pins, solo bloquea la línea
                            break # El rey bloquea la línea
                        
                        else: # Cualquier otra pieza oponente (Caballo) o pieza que no ataca linealmente/diagonalmente
                            break # Si no es un atacante relevante en esta dirección, bloquea la línea y rompemos

                else: # Fuera del tablero
                    break
        
        # --- Buscar ataques de caballo ---
        movimientos_caballo_l = ((-2, -1), (-2, 1), (-1, -2), (-1, 2),
                                 (1, -2), (1, 2), (2, -1), (2, 1))
        for dr, dc in movimientos_caballo_l:
            fila_final = fila_rey + dr
            col_final = col_rey + dc
            if 0 <= fila_final < 8 and 0 <= col_final < 8:
                pieza_en_casilla = self.tablero[fila_final][col_final]
                if pieza_en_casilla != "--" and pieza_en_casilla[0] == color_oponente and pieza_en_casilla[1] == 'n':
                    self.jaque = True
                    self.checks.append((fila_final, col_final))
    
    # Esta función modificada de la que tenías para no usar obtener_movimientos_legales
    def cuadrado_bajo_ataque(self, fila, col):
        """
        Determina si el cuadrado (fila, col) está bajo ataque por una pieza enemiga.
        Esta función NO debe modificar el estado del juego (ej. self.turno_blancas).
        Verifica ataques del oponente del turno actual.
        """
        # El color de las piezas que estamos comprobando si atacan es el color del jugador OPUESTO al turno actual
        color_atacante = 'b' if self.turno_blancas else 'w' 
        
        # 1. Ataques de peones
        # Los peones blancos ('w') atacan en (r-1, c-1) y (r-1, c+1)
        # Los peones negros ('b') atacan en (r+1, c-1) y (r+1, c+1)
        if color_atacante == 'w':
            if fila > 0: # Si no estamos en la fila 0 (borde superior)
                if col > 0 and self.tablero[fila - 1][col - 1] == 'wp': 
                    return True
                if col < 7 and self.tablero[fila - 1][col + 1] == 'wp': 
                    return True
        else: # color_atacante == 'b'
            if fila < 7: # Si no estamos en la fila 7 (borde inferior)
                if col > 0 and self.tablero[fila + 1][col - 1] == 'bp': 
                    return True
                if col < 7 and self.tablero[fila + 1][col + 1] == 'bp': 
                    return True

        # 2. Ataques de caballos
        movimientos_caballo_l = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        for dr, dc in movimientos_caballo_l:
            r_destino, c_destino = fila + dr, col + dc
            if 0 <= r_destino < 8 and 0 <= c_destino < 8:
                pieza_destino = self.tablero[r_destino][c_destino]
                if pieza_destino[0] == color_atacante and pieza_destino[1] == 'n':
                    return True
        
        # 3. Ataques de torres, alfiles y reinas (deslizantes)
        direcciones = ((-1, 0), (1, 0), (0, -1), (0, 1), # Ortogonales (Torre, Reina)
                       (-1, -1), (-1, 1), (1, -1), (1, 1)) # Diagonales (Alfil, Reina)
        
        for i, (dr, dc) in enumerate(direcciones):
            for j in range(1, 8): # Recorrer hasta el borde del tablero
                r_destino, c_destino = fila + dr * j, col + dc * j
                if 0 <= r_destino < 8 and 0 <= c_destino < 8:
                    pieza_destino = self.tablero[r_destino][c_destino]
                    if pieza_destino == "--":
                        continue # Casilla vacía, sigue buscando
                    elif pieza_destino[0] == color_atacante:
                        tipo_pieza_atacante = pieza_destino[1]
                        # Ortogonal (Torre o Reina)
                        if i < 4 and (tipo_pieza_atacante == 'r' or tipo_pieza_atacante == 'q'):
                            return True
                        # Diagonal (Alfil o Reina)
                        elif i >= 4 and (tipo_pieza_atacante == 'b' or tipo_pieza_atacante == 'q'):
                            return True
                        else: # Pieza del atacante que no amenaza en esta dirección (por ejemplo, un peón en una línea recta)
                            break # Esta pieza bloquea la línea, pero no ataca la casilla
                    else: # Pieza propia del rey que se está defendiendo o bloqueada por otra pieza enemiga
                        break # Esta pieza bloquea la línea
                else: # Fuera del tablero
                    break
        
        # 4. Ataques de rey (para verificar si el rey se mueve a una casilla adyacente al rey enemigo)
        movimientos_rey_adyacentes = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
        for dr, dc in movimientos_rey_adyacentes:
            r_destino, c_destino = fila + dr, col + dc
            if 0 <= r_destino < 8 and 0 <= c_destino < 8:
                pieza_destino = self.tablero[r_destino][c_destino]
                if pieza_destino[0] == color_atacante and pieza_destino[1] == 'k':
                    return True

        return False

    '''
    Todos los movimientos válidos considerando jaques, pins y checks.
    '''
    def obtener_movimientos_legales(self):
        # NOTA IMPORTANTE: self.actualizar_pins_y_checks() debe ser llamado
        # ANTES de obtener_movimientos_legales para que self.jaque, self.pins y self.checks
        # estén actualizados para el turno actual. Esto ya se hace en __init__ y hacer_movimiento.

        movimientos_legales_actuales = []
        
        # Guardar el estado actual del turno para restaurarlo si es necesario
        turno_original = self.turno_blancas

        # Si el rey está en jaque
        if self.jaque:
            if len(self.checks) == 1: # Un solo jaque
                # Obtener todos los movimientos posibles (brutos)
                movimientos_posibles = self.obtener_todos_los_movimientos_posibles()
                
                # Iterar sobre los movimientos posibles y verificar si son legales
                for mov in movimientos_posibles:
                    self.hacer_movimiento(mov)
                    # Después de hacer_movimiento, self.turno_blancas está invertido.
                    # Para verificar el jaque del REY QUE ACABA DE MOVER, necesitamos
                    # que self.turno_blancas esté como estaba antes del movimiento simulado.
                    self.turno_blancas = not self.turno_blancas # Temporalmente restauramos el turno original para la verificación
                    
                    self.actualizar_pins_y_checks() # Recalculamos jaque/pins/checks para el rey del jugador que acaba de mover
                                                    # self.jaque ahora refleja si el rey del jugador original está en jaque.

                    if not self.jaque: # Si el rey NO está en jaque después del movimiento simulado
                        movimientos_legales_actuales.append(mov)
                    
                    self.turno_blancas = not self.turno_blancas # Volvemos a invertir el turno para que deshacer_movimiento lo restaure correctamente
                    self.deshacer_movimiento() # Deshacer el movimiento simulado
            else: # Doble jaque: La única forma de salir es mover el rey
                # Obtener solo los movimientos del rey
                movimientos_posibles_rey = []
                if self.turno_blancas:
                    self.get_movimientos_rey(self.pos_rey_blanco[0], self.pos_rey_blanco[1], movimientos_posibles_rey)
                else:
                    self.get_movimientos_rey(self.pos_rey_negro[0], self.pos_rey_negro[1], movimientos_posibles_rey)
                
                for mov in movimientos_posibles_rey:
                    self.hacer_movimiento(mov)
                    self.turno_blancas = not self.turno_blancas # Temporalmente restauramos el turno original
                    self.actualizar_pins_y_checks() # Recalculamos
                    if not self.jaque: # Si el rey NO está en jaque después de mover
                        movimientos_legales_actuales.append(mov)
                    self.turno_blancas = not self.turno_blancas # Volvemos a invertir el turno
                    self.deshacer_movimiento()
        
        else: # El rey no está en jaque (puede haber pins)
            movimientos_posibles = self.obtener_todos_los_movimientos_posibles()
            
            # Filtrar movimientos que dejarían el rey en jaque (esto cubre los pins)
            for mov in movimientos_posibles:
                self.hacer_movimiento(mov) # Simular el movimiento
                
                # Después de hacer_movimiento, self.turno_blancas está invertido.
                # Para verificar el jaque del REY QUE ACABA DE MOVER, necesitamos
                # que self.turno_blancas esté como estaba antes del movimiento simulado.
                self.turno_blancas = not self.turno_blancas # Temporalmente restauramos el turno original para la verificación
                
                self.actualizar_pins_y_checks() # Recalculamos jaque/pins/checks para el rey del jugador que acaba de mover
                                                # self.jaque ahora refleja si el rey del jugador original está en jaque.
                
                if not self.jaque: # Si el rey NO está en jaque después del movimiento simulado
                    movimientos_legales_actuales.append(mov)
                
                self.turno_blancas = not self.turno_blancas # Volvemos a invertir el turno para que deshacer_movimiento lo restaure correctamente
                self.deshacer_movimiento() # Deshacer el movimiento para restaurar el tablero
            
            # Generar movimientos de enroque (solo si no está en jaque, que ya se verificó)
            # Y si no hay piezas en medio o casillas atacadas.
            # Se llama aquí y no en obtener_todos_los_movimientos_posibles porque requiere
            # la verificación de casillas bajo ataque (que dependen de la legalidad del movimiento).
            # Esta llamada NO DEBE MODIFICAR self.turno_blancas, por lo que lo restauramos si se cambia
            # temporalmente en este bloque.
            self.turno_blancas = turno_original # Aseguramos que el turno sea el correcto para get_movimientos_enroque
            if self.turno_blancas: 
                self.get_movimientos_enroque(self.pos_rey_blanco[0], self.pos_rey_blanco[1], movimientos_legales_actuales)
            else: 
                self.get_movimientos_enroque(self.pos_rey_negro[0], self.pos_rey_negro[1], movimientos_legales_actuales)
            self.turno_blancas = turno_original # Restaurar el turno original después de get_movimientos_enroque

        # Verificar Jaque Mate / Ahogado
        # Estos se verifican DESPUÉS de haber calculado TODOS los movimientos legales.
        if len(movimientos_legales_actuales) == 0:
            if self.jaque:
                self.jaque_mate = True
                self.ahogado = False # No puede ser ahogado si hay jaque
            else:
                self.ahogado = True
                self.jaque_mate = False # No puede ser jaque mate si no hay jaque
        else: # Si hay movimientos legales, no hay jaque mate ni ahogado
            self.jaque_mate = False
            self.ahogado = False

        return movimientos_legales_actuales

    '''
    Todos los movimientos posibles sin considerar jaques.
    '''
    def obtener_todos_los_movimientos_posibles(self): 
        """
        Genera todos los movimientos posibles (brutos) en el tablero para el jugador actual,
        sin considerar si dejan al rey en jaque.
        """
        movimientos = []
        for fila in range(len(self.tablero)):
            for col in range(len(self.tablero[fila])):
                pieza = self.tablero[fila][col]
                if pieza == "--": # Si la casilla está vacía, continuar
                    continue

                turno = pieza[0] # 'w' o 'b'
                if (turno == 'w' and self.turno_blancas) or \
                   (turno == 'b' and not self.turno_blancas):
                    tipo_pieza = pieza[1] # 'p', 'r', 'n', 'b', 'q', 'k'
                    
                    # Llamamos a la función específica para cada tipo de pieza
                    if tipo_pieza == 'p':
                        self.get_movimientos_peon(fila, col, movimientos)
                    elif tipo_pieza == 'r':
                        self.get_movimientos_torre(fila, col, movimientos)
                    elif tipo_pieza == 'n':
                        self.get_movimientos_caballo(fila, col, movimientos)
                    elif tipo_pieza == 'b':
                        self.get_movimientos_alfil(fila, col, movimientos)
                    elif tipo_pieza == 'q':
                        self.get_movimientos_reina(fila, col, movimientos)
                    elif tipo_pieza == 'k':
                        self.get_movimientos_rey(fila, col, movimientos) 
        return movimientos

    # --- Funciones para generar movimientos de cada pieza (brutos) ---

    def get_movimientos_peon(self, r, c, movimientos):
        pieza_color = self.tablero[r][c][0]
        
        if pieza_color == 'w': # Peones blancos
            # Avance de una casilla
            if r - 1 >= 0 and self.tablero[r - 1][c] == "--":
                movimientos.append(Movimiento((r, c), (r - 1, c), self.tablero))
                # Avance de dos casillas (solo desde la fila inicial)
                if r == 6 and self.tablero[r - 2][c] == "--": # Check the square in front of it as well
                    movimientos.append(Movimiento((r, c), (r - 2, c), self.tablero))
            
            # Capturas diagonales
            # Captura a la izquierda
            if c - 1 >= 0: 
                if r - 1 >= 0 and self.tablero[r - 1][c - 1][0] == 'b': # Pieza negra
                    movimientos.append(Movimiento((r, c), (r - 1, c - 1), self.tablero))
                elif (r - 1, c - 1) == self.pos_en_passant_posible: # En passant
                    movimientos.append(Movimiento((r, c), (r - 1, c - 1), self.tablero, en_passant_posible=True))
            # Captura a la derecha
            if c + 1 < 8:
                if r - 1 >= 0 and self.tablero[r - 1][c + 1][0] == 'b': # Pieza negra
                    movimientos.append(Movimiento((r, c), (r - 1, c + 1), self.tablero))
                elif (r - 1, c + 1) == self.pos_en_passant_posible: # En passant
                    movimientos.append(Movimiento((r, c), (r - 1, c + 1), self.tablero, en_passant_posible=True))

        else: # Peones negros
            # Avance de una casilla
            if r + 1 < 8 and self.tablero[r + 1][c] == "--":
                movimientos.append(Movimiento((r, c), (r + 1, c), self.tablero))
                # Avance de dos casillas (solo desde la fila inicial)
                if r == 1 and self.tablero[r + 2][c] == "--": # Check the square in front of it as well
                    movimientos.append(Movimiento((r, c), (r + 2, c), self.tablero))
            
            # Capturas diagonales
            # Captura a la izquierda
            if c - 1 >= 0:
                if r + 1 < 8 and self.tablero[r + 1][c - 1][0] == 'w': # Pieza blanca
                    movimientos.append(Movimiento((r, c), (r + 1, c - 1), self.tablero))
                elif (r + 1, c - 1) == self.pos_en_passant_posible: # En passant
                    movimientos.append(Movimiento((r, c), (r + 1, c - 1), self.tablero, en_passant_posible=True))
            # Captura a la derecha
            if c + 1 < 8:
                if r + 1 < 8 and self.tablero[r + 1][c + 1][0] == 'w': # Pieza blanca
                    movimientos.append(Movimiento((r, c), (r + 1, c + 1), self.tablero))
                elif (r + 1, c + 1) == self.pos_en_passant_posible: # En passant
                    movimientos.append(Movimiento((r, c), (r + 1, c + 1), self.tablero, en_passant_posible=True))

    def get_movimientos_torre(self, r, c, movimientos):
        direcciones = ((-1, 0), (0, -1), (1, 0), (0, 1)) # Arriba, izquierda, abajo, derecha
        color_propio = self.tablero[r][c][0]
        color_oponente = 'b' if color_propio == 'w' else 'w'
        for dr, dc in direcciones:
            for i in range(1, 8): # Puede moverse hasta 7 casillas en una dirección
                end_r, end_c = r + dr * i, c + dc * i
                if 0 <= end_r < 8 and 0 <= end_c < 8: # Dentro del tablero
                    pieza_final = self.tablero[end_r][end_c]
                    if pieza_final == "--": # Casilla vacía
                        movimientos.append(Movimiento((r, c), (end_r, end_c), self.tablero))
                    elif pieza_final[0] == color_oponente: # Pieza enemiga
                        movimientos.append(Movimiento((r, c), (end_r, end_c), self.tablero))
                        break # Se detiene al capturar
                    else: # Pieza amiga
                        break # Se detiene al chocar con una pieza propia
                else: # Fuera del tablero
                    break

    def get_movimientos_caballo(self, r, c, movimientos):
        movimientos_caballo_l = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        color_propio = self.tablero[r][c][0]
        for dr, dc in movimientos_caballo_l:
            end_r, end_c = r + dr, c + dc
            if 0 <= end_r < 8 and 0 <= end_c < 8: # Dentro del tablero
                pieza_final = self.tablero[end_r][end_c]
                if pieza_final[0] != color_propio: # No es una pieza amiga (puede ser vacía o enemiga)
                    movimientos.append(Movimiento((r, c), (end_r, end_c), self.tablero))

    def get_movimientos_alfil(self, r, c, movimientos):
        direcciones = ((-1, -1), (-1, 1), (1, -1), (1, 1)) # 4 diagonales
        color_propio = self.tablero[r][c][0]
        color_oponente = 'b' if color_propio == 'w' else 'w'
        for dr, dc in direcciones:
            for i in range(1, 8):
                end_r, end_c = r + dr * i, c + dc * i
                if 0 <= end_r < 8 and 0 <= end_c < 8:
                    pieza_final = self.tablero[end_r][end_c]
                    if pieza_final == "--":
                        movimientos.append(Movimiento((r, c), (end_r, end_c), self.tablero))
                    elif pieza_final[0] == color_oponente:
                        movimientos.append(Movimiento((r, c), (end_r, end_c), self.tablero))
                        break
                    else: # Pieza amiga
                        break
                else: # Fuera del tablero
                    break

    def get_movimientos_reina(self, r, c, movimientos):
        # La reina combina los movimientos de la torre y el alfil
        self.get_movimientos_torre(r, c, movimientos)
        self.get_movimientos_alfil(r, c, movimientos)

    def get_movimientos_rey(self, r, c, movimientos):
        movimientos_rey = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
        color_propio = self.tablero[r][c][0]
        for dr, dc in movimientos_rey:
            end_r, end_c = r + dr, c + dc
            if 0 <= end_r < 8 and 0 <= end_c < 8:
                pieza_final = self.tablero[end_r][end_c]
                if pieza_final[0] != color_propio: # No es una pieza amiga
                    # Los movimientos del rey se validan para no ir a una casilla atacada
                    # directamente en `obtener_movimientos_legales` llamando a `cuadrado_bajo_ataque`
                    # para cada movimiento posible del rey. Aquí solo generamos los movimientos "brutos".
                    movimientos.append(Movimiento((r, c), (end_r, end_c), self.tablero))

    def get_movimientos_enroque(self, r, c, movimientos):
        # El enroque solo es posible si el rey no está en jaque
        if self.jaque:
            return

        # Enroque corto (King side)
        if (self.turno_blancas and self.derechos_enroque_actuales.wks) or \
           (not self.turno_blancas and self.derechos_enroque_actuales.bks):
            # Cuidado: Asumo que c+1 y c+2 son las casillas por donde pasa el rey, es decir, el rey está en (r,c)
            # y se mueve a (r, c+2). Las casillas (r, c+1) y (r, c+2) deben estar vacías y no atacadas.
            if self.tablero[r][c + 1] == "--" and self.tablero[r][c + 2] == "--":
                # Las casillas por las que pasa el rey no deben estar bajo ataque
                if not self.cuadrado_bajo_ataque(r, c + 1) and not self.cuadrado_bajo_ataque(r, c + 2):
                    movimientos.append(Movimiento((r, c), (r, c + 2), self.tablero, enroque_movimiento=True))

        # Enroque largo (Queen side)
        if (self.turno_blancas and self.derechos_enroque_actuales.wqs) or \
           (not self.turno_blancas and self.derechos_enroque_actuales.bqs):
            # Rey se mueve a (r, c-2). Las casillas (r, c-1), (r, c-2) y (r, c-3) deben estar vacías.
            # Y (r, c-1), (r, c-2) no deben estar atacadas.
            if self.tablero[r][c - 1] == "--" and self.tablero[r][c - 2] == "--" and self.tablero[r][c - 3] == "--":
                # Las casillas por las que pasa el rey no deben estar bajo ataque
                if not self.cuadrado_bajo_ataque(r, c - 1) and not self.cuadrado_bajo_ataque(r, c - 2):
                    movimientos.append(Movimiento((r, c), (r, c - 2), self.tablero, enroque_movimiento=True))