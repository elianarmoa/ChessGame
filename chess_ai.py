# chess_ai.py

import random

# Valores de las piezas para la función de evaluación.
# Estos son valores heurísticos comunes.
PIECE_SCORES = {
    'p': 10,    # Peón
    'n': 30,    # Caballo
    'b': 30,    # Alfil
    'r': 50,    # Torre
    'q': 90,    # Reina
    'k': 0      # Rey (su valor es 0 porque es el objetivo, no una pieza a ganar)
}

# Variable global para almacenar el movimiento que la IA elegirá.
# Se inicializa a None y se actualiza en la llamada inicial de minimax.
PROXIMO_MOVIMIENTO_IA = None

# Constante para la profundidad de búsqueda de la IA.
# PROFUNDIDAD_BUSQUEDA se sugiere como 2 o 3 para un rendimiento razonable.
# Valores más altos hacen la IA más fuerte pero más lenta.
PROFUNDIDAD_BUSQUEDA = 3 # Se ajusta según el rendimiento deseado de la IA.

# --- Función de Evaluación ---
def evaluar_tablero(estado_juego):
    """
    Evalúa la "bondad" de una posición del tablero desde la perspectiva de las blancas.
    Un valor positivo significa una mejor posición para las blancas.
    Un valor negativo significa una mejor posición para las negras.

    :param estado_juego: Un objeto EstadoJuego actual.
    :return: Puntuación numérica de la posición.
    """
    # Si hay jaque mate, devolver una puntuación extrema.
    # El jugador cuyo turno es (estado_juego.turno_blancas) es el que ha sido jaque mateado.
    if estado_juego.jaque_mate:
        # Si las blancas están en jaque mate, las negras ganan, es una puntuación muy negativa para blancas.
        # Si las negras están en jaque mate, las blancas ganan, es una puntuación muy positiva para blancas.
        if estado_juego.turno_blancas: # Si las blancas están en jaque mate, significa que el turno era de las blancas
            return -1000000000 # Jaque mate para blancas (pierden)
        else: # Si las negras están en jaque mate
            return 1000000000 # Jaque mate para negras (pierden)
    elif estado_juego.ahogado:
        return 0 # Tablas por ahogado

    score = 0
    for fila in range(8):
        for col in range(8):
            pieza = estado_juego.tablero[fila][col]
            if pieza != "--":
                # Determinar el valor de la pieza
                valor_pieza = PIECE_SCORES[pieza[1]] # 'p', 'n', 'b', etc.

                # Sumar o restar según el color de la pieza
                if pieza[0] == 'w': # Si es pieza blanca
                    score += valor_pieza
                elif pieza[0] == 'b': # Si es pieza negra
                    score -= valor_pieza
    return score

# --- Implementación de Minimax con Poda Alpha-Beta (Optimización) ---
# La poda Alpha-Beta es una mejora de Minimax que elimina ramas de búsqueda
# que no afectarán la decisión final, haciendo que el algoritmo sea mucho más eficiente.

def encontrar_movimiento_minimax_ab(estado_juego, movimientos_legales, profundidad, alpha, beta, turno_maximizador):
    """
    Implementación del algoritmo Minimax con poda Alpha-Beta.
    :param estado_juego: El estado actual del juego.
    :param movimientos_legales: Lista de movimientos legales para el estado actual.
    :param profundidad: La profundidad de búsqueda restante del algoritmo.
    :param alpha: El mejor valor que el jugador maximizador ha encontrado hasta ahora en la ruta.
    :param beta: El mejor valor que el jugador minimizador ha encontrado hasta ahora en la ruta.
    :param turno_maximizador: True si es el turno del jugador que maximiza (IA), False si es el turno del jugador que minimiza (oponente).
    :return: Puntuación óptima de la posición.
    """
    global PROXIMO_MOVIMIENTO_IA # Acceder a la variable global para guardar el mejor movimiento

    # Caso base de la recursión: si se alcanza la profundidad cero, o un estado final (jaque mate/ahogado)
    if profundidad == 0 or estado_juego.jaque_mate or estado_juego.ahogado:
        return evaluar_tablero(estado_juego)

    # Ordenar los movimientos aleatoriamente para introducir variedad en movimientos de igual valor
    # (También se pueden ordenar heurísticamente para mejorar la poda Alpha-Beta)
    # random.shuffle(movimientos_legales) 

    if turno_maximizador: # Jugador que maximiza (la IA si es su turno)
        max_puntuacion = -float('inf')
        for movimiento in movimientos_legales:
            estado_juego.hacer_movimiento(movimiento) # Simula el movimiento
            # Llamada recursiva para el siguiente turno (minimizador)
            puntuacion = encontrar_movimiento_minimax_ab(estado_juego, estado_juego.obtener_movimientos_legales(), profundidad - 1, alpha, beta, False)
            
            if puntuacion > max_puntuacion:
                max_puntuacion = puntuacion
                if profundidad == PROFUNDIDAD_BUSQUEDA: # Solo guarda el movimiento en la llamada inicial (profundidad original)
                    PROXIMO_MOVIMIENTO_IA = movimiento
            
            estado_juego.deshacer_movimiento() # Deshace el movimiento simulado para volver al estado original

            # Poda Alpha-Beta
            alpha = max(alpha, max_puntuacion)
            if beta <= alpha: # Si el minimizador ya tiene una opción mejor, no necesitamos seguir explorando esta rama
                break
        return max_puntuacion
    else: # Jugador que minimiza (el oponente de la IA)
        min_puntuacion = float('inf')
        for movimiento in movimientos_legales:
            estado_juego.hacer_movimiento(movimiento) # Simula el movimiento
            # Llamada recursiva para el siguiente turno (maximizador)
            puntuacion = encontrar_movimiento_minimax_ab(estado_juego, estado_juego.obtener_movimientos_legales(), profundidad - 1, alpha, beta, True)
            
            if puntuacion < min_puntuacion:
                min_puntuacion = puntuacion
                if profundidad == PROFUNDIDAD_BUSQUEDA: # Solo guarda el movimiento en la llamada inicial
                    PROXIMO_MOVIMIENTO_IA = movimiento # Esto es para asegurar que si la IA es minimizadora, también guarde su movimiento
            
            estado_juego.deshacer_movimiento() # Deshace el movimiento simulado

            # Poda Alpha-Beta
            beta = min(beta, min_puntuacion)
            if beta <= alpha: # Si el maximizador ya tiene una opción mejor, no necesitamos seguir explorando esta rama
                break
        return min_puntuacion

# --- Función principal para encontrar el mejor movimiento de la IA ---
def find_best_move(gs):
    """
    Función principal para que la IA elija su mejor movimiento.
    Utiliza el algoritmo Minimax con poda Alpha-Beta.
    """
    global PROXIMO_MOVIMIENTO_IA # Asegura que estamos modificando la variable global
    PROXIMO_MOVIMIENTO_IA = None # Reiniciar para cada nueva búsqueda

    # Obtener los movimientos legales para el turno actual
    movimientos_legales = gs.obtener_movimientos_legales()

    if not movimientos_legales:
        return None # No hay movimientos legales, esto indica jaque mate o ahogado

    # Llamar a Minimax. `turno_maximizador` depende de si la IA es el jugador blanco o negro.
    # Asumimos que la IA es el jugador cuyo turno es `gs.turno_blancas`.
    # Si es el turno de las blancas, queremos maximizar la puntuación.
    # Si es el turno de las negras, queremos minimizar la puntuación (que es equivalente a maximizar la puntuación negativa).
    # La función `encontrar_movimiento_minimax_ab` ya maneja esto.

    # Es importante pasar los movimientos_legales calculados antes,
    # ya que la primera llamada a la función no los recalcula.
    # Las llamadas recursivas sí los recalcularán para cada nuevo estado.
    encontrar_movimiento_minimax_ab(gs, movimientos_legales, PROFUNDIDAD_BUSQUEDA, -float('inf'), float('inf'), gs.turno_blancas)
    
    return PROXIMO_MOVIMIENTO_IA