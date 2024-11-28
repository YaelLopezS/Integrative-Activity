from mesa import Agent
import heapq
from Mapa import Parking
from Negotiation import Negotiation
import time

class Microbus(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = "NORMAL"  # Estados: NORMAL, ANGRY
        self.happiness = 100  # Métrica de felicidad inicial
        self.path = None
        self.target = None  # Objetivo, puede ser una parada o un estacionamiento
        self.request_light = False  # Solicita un semáforo
        self.light_granted = False  # Indica si el semáforo le otorgó paso
        self.parked = False
        self.passengers = 0  # Número de pasajeros actuales
        self.max_passengers = 5  # Capacidad máxima de pasajeros
        self.collecting_passengers = True
        self.visited_stops = set()  # Estado de recolección de pasajeros
        self.blocked_steps = 0  # Contador de pasos bloqueados
        self.last_attempt_time = time.time()  # Tiempo del último intento de moverse

    def step(self):
        if self.parked:
            return

        # Actualizar estado y felicidad
        self._update_state()

        # Imprimir estado actual
        print(f"Microbús {self.unique_id}: Estado actual - {self.state}")

        # Verificar si hay otros microbuses cercanos para negociar
        neighbors = self.model.grid.get_neighbors(self.pos, moore=False, radius=1)
        vehicles_nearby = [agent for agent in neighbors if isinstance(agent, Microbus) and not agent.parked]

        for other_vehicle in vehicles_nearby:
            # Realizar negociación si hay un conflicto
            action_self, action_other = Negotiation.negotiate(self, other_vehicle)

            # Resolver conflicto según el resultado de la negociación
            if action_self == "cede" and action_other == "compite":
                print(f"Microbús {self.unique_id} cede el paso al microbús {other_vehicle.unique_id}.")
                return
            elif action_self == "compite" and action_other == "cede":
                print(f"Microbús {self.unique_id} avanza sobre el microbús {other_vehicle.unique_id}.")
                break
            elif action_self == "cede" and action_other == "cede":
                print(f"Microbús {self.unique_id} y {other_vehicle.unique_id} cooperan para evitar conflicto.")
                return
            elif action_self == "compite" and action_other == "compite":
                print(f"Microbús {self.unique_id} y {other_vehicle.unique_id} están bloqueados. Buscando alternativas.")
                self.happiness -= 5  # Penalización por competencia inútil
                other_vehicle.happiness -= 5
                self.blocked_steps += 1
                other_vehicle.blocked_steps += 1

                # Si el microbús está bloqueado durante más de 3 pasos, recalcula la ruta
                if self.blocked_steps > 3:
                    print(f"Microbús {self.unique_id}: Recalculando ruta debido a bloqueo prolongado.")
                    self._calculate_path()
                    self.blocked_steps = 0

        # Solicitar semáforo si se acerca a uno
        self.request_light = self._approaching_light()

        # Moverse si tiene luz verde o no está cerca de semáforos
        if self.light_granted or not self.request_light:
            if not self.path or self.pos == self.target:
                self._calculate_path()
            if self.path:
                self.move()

    def _approaching_light(self):
        """Verifica si el microbús se acerca a un semáforo"""
        from Semaforo import TrafficLight
        for agent in self.model.grid.get_neighbors(self.pos, moore=False, radius=2):
            if isinstance(agent, TrafficLight):
                return True
        return False

    def _update_state(self):
        """Actualiza el estado emocional del microbús según su felicidad."""
        if self.happiness < 50 and self.state != "ANGRY":
            self.state = "ANGRY"
        elif self.happiness >= 50 and self.state != "NORMAL":
            self.state = "NORMAL"

    def _calculate_path(self):
        """Calcula el camino más corto a una parada o un estacionamiento usando A*."""
        # Definimos los carriles con sus coordenadas y direcciones
        lanes_positions = self.model.get_lanes_positions()

        # Creamos el grafo dirigido a partir de las posiciones de los carriles
        graph = {}
        for lane, direction in lanes_positions:
            for i in range(len(lane) - 1):
                if direction == "right_to_left":
                    graph.setdefault(lane[i], []).append((lane[i+1], 1))
                elif direction == "left_to_right":
                    graph.setdefault(lane[i], []).append((lane[i+1], 1))
                elif direction == "down":
                    graph.setdefault(lane[i], []).append((lane[i+1], 1))
                elif direction == "up":
                    graph.setdefault(lane[i], []).append((lane[i+1], 1))

        start = self.pos
        if self.collecting_passengers:
            stops = [
                (21, 16), (22, 2), (21, 23), (22, 8),
                (12, 23), (12, 19), (2, 3), (3, 13), (9, 13), (7, 12)
            ]
            target_points = [stop for stop in stops if stop not in self.visited_stops]
        else:
            parkings = [
                agent.pos
                for content, pos in self.model.grid.coord_iter()
                for agent in content
                if isinstance(agent, Parking) and not agent.is_occupied
            ]
            target_points = parkings

        if not target_points:
            print(f"Microbús {self.unique_id}: No hay destinos disponibles.")
            self.path = None
            return

        closest_target = None
        shortest_path = None
        shortest_distance = float('inf')

        for target in target_points:
            path = self._a_star(graph, start, target)
            if path and len(path) < shortest_distance:
                closest_target = target
                shortest_path = path
                shortest_distance = len(path)

        if closest_target and shortest_path:
            self.target = closest_target
            self.path = shortest_path
        else:
            print(f"Microbús {self.unique_id}: No hay camino al destino.")
            self.path = None

    def _a_star(self, graph, start, goal):
        # Algoritmo A* para encontrar la ruta más corta
        open_set = [(0, start)]
        g_costs = {start: 0}
        f_costs = {start: self._heuristic(start, goal)}
        previous_nodes = {start: None}

        while open_set:
            _, current_node = heapq.heappop(open_set)

            if current_node == goal:
                path = []
                while previous_nodes[current_node] is not None:
                    path.append(current_node)
                    current_node = previous_nodes[current_node]
                path.append(start)
                return path[::-1]

            for neighbor, weight in graph.get(current_node, []):
                g_cost = g_costs[current_node] + weight
                if neighbor not in g_costs or g_cost < g_costs[neighbor]:
                    g_costs[neighbor] = g_cost
                    f_cost = g_cost + self._heuristic(neighbor, goal)
                    f_costs[neighbor] = f_cost
                    heapq.heappush(open_set, (f_cost, neighbor))
                    previous_nodes[neighbor] = current_node

        return []

    def _heuristic(self, node, goal):
        # Heurística de Manhattan para el cálculo de A*
        return abs(node[0] - goal[0]) + abs(node[1] - goal[1])

    def move(self):
        """Mueve el microbús al siguiente paso en el camino calculado."""
        if self.path:
            next_position = self.path[0]

            # Verificar si el próximo espacio es una parada de recogida de pasajeros
            if self.collecting_passengers and next_position in set([(21, 16), (22, 2), (21, 23), (22, 8), (12, 23), (12, 19), (2, 3), (3, 13), (9, 13), (7, 12)]) and next_position not in getattr(self, 'visited_stops', set()):
                self.passengers += 1
                self.visited_stops.add(next_position)  # Sumar un pasajero al llegar a una parada
                if self.passengers >= self.max_passengers:
                    self.collecting_passengers = False  # Cambiar a buscar estacionamiento
                print(f"Microbús {self.unique_id}: Recogió pasajeros en {next_position}. Pasajeros actuales: {self.passengers}/{self.max_passengers}")

            # Verificar si el próximo espacio es un estacionamiento
            if not self.collecting_passengers and next_position == self.target:
                # Obtener el contenido de la celda del estacionamiento
                parking_spot = self.model.grid.get_cell_list_contents([next_position])
                parking_agent = next((agent for agent in parking_spot if isinstance(agent, Parking)), None)

                if parking_agent and parking_agent.is_occupied:
                    self._calculate_path()  # Recalcular la ruta hacia otro estacionamiento
                    return

                # Si el espacio está libre, marcarlo como ocupado
                if parking_agent:
                    parking_agent.occupy()

                print(f"Microbús {self.unique_id}: Se ha estacionado en {next_position}.")
                self.model.grid.move_agent(self, next_position)
                self.parked = True  # Marcar el microbús como estacionado
                return  # Detenerse aquí al llegar al estacionamiento

            # Si no es un estacionamiento, mover hacia la siguiente posición
            from Semaforo import TrafficLight
            if self.model.grid.is_cell_empty(next_position) or any(isinstance(agent, TrafficLight) for agent in self.model.grid.get_cell_list_contents([next_position])):
                self.model.grid.move_agent(self, next_position)
                self.path.pop(0)
            else:
                # Si está bloqueado por un obstáculo no permitido
                self.happiness -= 10
                self.blocked_steps += 1
                if self.state == "ANGRY" and self.blocked_steps > 3:
                    print(f"Microbús {self.unique_id}: Intentando cambiar de carril debido a bloqueo prolongado.")
                    self._attempt_lane_change()
                    self.blocked_steps = 0

    def _attempt_lane_change(self):
        """Intenta cambiar de carril si está bloqueado."""
        neighbors = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)

        for neighbor in neighbors:
            if self.model.grid.is_cell_empty(neighbor) and neighbor[0] > 0 and neighbor[1] > 0:
                self.model.grid.move_agent(self, neighbor)
                return
