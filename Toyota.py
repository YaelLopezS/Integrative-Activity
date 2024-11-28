from mesa import Agent
import heapq
from Mapa import Parking, Building, Lane
from Negotiation import Negotiation
from Semaforo import TrafficLight
from Ferrari import Vehicle  # Asegúrate de que esta clase exista o ajústala según tu modelo

class Toyota(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = "FELIZ"  # Estados emocionales: FELIZ, ENOJADO
        self.happiness = 100  # Nivel inicial de felicidad
        self.path = None      # Ruta actual calculada con A*
        self.target = None    # Estacionamiento objetivo
        self.request_light = False   # Solicita paso al semáforo
        self.light_granted = False   # Indica si el semáforo le otorgó paso
        self.parked = False          # Indica si está estacionado
        self.blocked_counter = 0     # Contador para detectar bloqueos

    def step(self):
        if self.parked:
            print(f"Toyota {self.unique_id} está estacionado.")
            return

        # Actualizar estado y felicidad
        self._update_state()

        # Verificar si hay otros vehículos cercanos para negociar
        neighbors = self.model.grid.get_neighbors(self.pos, moore=False, radius=1)
        vehicle_classes = (Toyota, Vehicle)  # Asegúrate de incluir todas las clases de vehículos relevantes
        vehicles_nearby = [agent for agent in neighbors if isinstance(agent, vehicle_classes) and not agent.parked]

        for other_vehicle in vehicles_nearby:
            # Realizar negociación si hay un conflicto
            action_self, action_other = Negotiation.negotiate(self, other_vehicle)

            # Resolver conflicto según el resultado de la negociación
            if action_self == "cede" and action_other == "compite":
                print(f"Toyota {self.unique_id} cede el paso al vehículo {other_vehicle.unique_id}.")
                return
            elif action_self == "compite" and action_other == "cede":
                print(f"Toyota {self.unique_id} avanza sobre el vehículo {other_vehicle.unique_id}.")
                break
            elif action_self == "cede" and action_other == "cede":
                print(f"Toyota {self.unique_id} y {other_vehicle.unique_id} cooperan para evitar conflicto.")
                continue  # Ambos cooperan, seguir intentando moverse
            elif action_self == "compite" and action_other == "compite":
                print(f"Toyota {self.unique_id} y {other_vehicle.unique_id} están bloqueados. Buscando alternativas.")
                self.happiness -= 5  # Penalización por competencia inútil
                if hasattr(other_vehicle, 'happiness'):
                    other_vehicle.happiness -= 5
                self.blocked_counter += 1
                if self.blocked_counter > 3:
                    self._calculate_path()  # Recalcular ruta si está bloqueado muchas veces
                    self.blocked_counter = 0
                continue

        # Solicitar semáforo si se acerca a uno
        self.request_light = self._approaching_light()

        # Intentar cambiar de carril si hay un bloqueo enfrente
        if self._attempt_lane_change():
            return

        # Moverse si tiene luz verde o no está cerca de semáforos
        if self.light_granted or not self.request_light:
            if not self.path or self.pos == self.target:
                self._calculate_path()
                if not self.path:
                    print(f"Toyota {self.unique_id}: No se encontró una ruta al objetivo.")
                    return
            if self.path:
                self.move()
        elif self.request_light:
            # Si está esperando un semáforo en amarillo, intentar avanzar después
            self.light_granted = True  # Simplificación para la simulación

    def _approaching_light(self):
        """Verifica si el Toyota se acerca a un semáforo."""
        for agent in self.model.grid.get_neighbors(self.pos, moore=False, radius=2):
            if isinstance(agent, TrafficLight):
                # Verificar el estado del semáforo
                if agent.state == "RED":
                    print(f"Toyota {self.unique_id}: Se detiene en semáforo rojo en {agent.pos}.")
                    return True
                elif agent.state == "GREEN":
                    print(f"Toyota {self.unique_id}: Semáforo en verde en {agent.pos}. Puede avanzar.")
                    self.light_granted = True
                elif agent.state == "YELLOW":
                    print(f"Toyota {self.unique_id}: Semáforo en amarillo en {agent.pos}. Preparándose para detenerse.")
                    self.light_granted = False
        return False

    def _attempt_lane_change(self):
        """Intenta cambiar de carril si hay otro vehículo bloqueando el camino enfrente."""
        if not self.path or len(self.path) == 0:
            return False  # No hay ruta calculada

        # Determinar la posición frente a la dirección de movimiento
        next_position = self.path[0]
        dx = next_position[0] - self.pos[0]
        dy = next_position[1] - self.pos[1]
        front_position = (self.pos[0] + dx, self.pos[1] + dy)

        for agent in self.model.grid.get_cell_list_contents(front_position):
            if isinstance(agent, (Toyota, Vehicle)) and not agent.parked:
                # Detecta un vehículo bloqueando, intenta cambiar de carril
                lane_change_candidates = [
                    (self.pos[0] + dy, self.pos[1] - dx),  # Desplazamiento perpendicular a la derecha
                    (self.pos[0] - dy, self.pos[1] + dx),  # Desplazamiento perpendicular a la izquierda
                ]
                for candidate in lane_change_candidates:
                    # Verificar límites del grid y si la celda está vacía
                    if (0 <= candidate[0] < self.model.grid.width and 0 <= candidate[1] < self.model.grid.height
                            and self.model.grid.is_cell_empty(candidate)):
                        self.model.grid.move_agent(self, candidate)
                        print(f"Toyota {self.unique_id}: Cambió de carril a {candidate}.")
                        return True
                print(f"Toyota {self.unique_id}: No pudo cambiar de carril, sigue bloqueado.")
                return False
        return False

    def move(self):
        """Mueve el Toyota al siguiente paso en el camino calculado."""
        if not self.path:
            return  # No hay ruta calculada

        next_position = self.path.pop(0)

        # Verificar si el próximo movimiento es el objetivo y si el estacionamiento está disponible
        if next_position == self.target:
            cell_contents = self.model.grid.get_cell_list_contents([next_position])
            parking_agent = next((agent for agent in cell_contents if isinstance(agent, Parking)), None)

            if parking_agent and parking_agent.is_occupied:
                print(f"Toyota {self.unique_id}: Estacionamiento en {next_position} está ocupado. Recalculando ruta.")
                self._calculate_path()  # Recalcular la ruta hacia otro estacionamiento
                return

            if parking_agent:
                parking_agent.occupy()

            self.model.grid.move_agent(self, next_position)
            self.parked = True
            print(f"Toyota {self.unique_id}: Se ha estacionado en {next_position}.")
            return

        # Verificar si el siguiente espacio está ocupado por un edificio u obstáculo fijo
        cell_contents = self.model.grid.get_cell_list_contents([next_position])
        if any(isinstance(agent, Building) for agent in cell_contents):
            print(f"Toyota {self.unique_id}: No puede pasar por un edificio en {next_position}. Recalculando ruta.")
            self._calculate_path()
            return

        # Mover hacia la siguiente posición si está libre
        if self.model.grid.is_cell_empty(next_position):
            self.model.grid.move_agent(self, next_position)
        else:
            # Si está bloqueado por un obstáculo temporal
            self.happiness -= 10
            if self.state == "ENOJADO":
                self._attempt_lane_change()

    def _calculate_path(self):
        """Calcula el camino más largo a un estacionamiento disponible usando A* evitando celdas ocupadas."""
        # Obtener las posiciones de los carriles y direcciones
        lanes_positions = self.model.get_lanes_positions()

        # Crear el grafo dirigido a partir de las posiciones de los carriles
        graph = {}
        for lane, direction in lanes_positions:
            for i in range(len(lane) - 1):
                graph.setdefault(lane[i], []).append((lane[i+1], 1))

        start = self.pos

        # Buscar los estacionamientos disponibles
        parkings = [
            agent.pos
            for content, pos in self.model.grid.coord_iter()
            for agent in content
            if isinstance(agent, Parking) and not agent.is_occupied
        ]

        if not parkings:
            print(f"Toyota {self.unique_id}: No hay estacionamientos disponibles.")
            self.path = None
            return

        paths = []
        for target in parkings:
            path = self._a_star(graph, start, target)
            if path:
                paths.append((len(path), path, target))

        if paths:
            # Seleccionar el camino más largo (estacionamiento más lejano)
            paths.sort(key=lambda x: x[0], reverse=True)
            longest_path = paths[0][1]
            farthest_target = paths[0][2]
            print(f"Toyota {self.unique_id}: Calculó ruta al estacionamiento más lejano en {farthest_target}")
            self.target = farthest_target
            self.path = longest_path
        else:
            print(f"Toyota {self.unique_id}: No hay camino disponible a ningún estacionamiento.")
            self.path = None

    def _a_star(self, graph, start, goal):
        # Algoritmo A* para encontrar la ruta más corta evitando celdas ocupadas
        open_set = [(0, start)]
        g_costs = {start: 0}
        previous_nodes = {start: None}
        closed_set = set()

        while open_set:
            _, current_node = heapq.heappop(open_set)

            if current_node == goal:
                path = []
                while current_node is not None:
                    path.append(current_node)
                    current_node = previous_nodes[current_node]
                return path[::-1]

            closed_set.add(current_node)

            for neighbor, weight in graph.get(current_node, []):
                if neighbor in closed_set:
                    continue

                # Verificar si la celda está ocupada por un obstáculo fijo (Building) o vehículo estacionado
                cell_contents = self.model.grid.get_cell_list_contents([neighbor])
                cell_occupied = any(
                    isinstance(agent, Building) or
                    (hasattr(agent, 'parked') and agent.parked and agent != self)
                    for agent in cell_contents
                )

                if cell_occupied and neighbor != goal:
                    continue  # Saltar celdas ocupadas, excepto si es el objetivo

                tentative_g_cost = g_costs[current_node] + weight
                if neighbor not in g_costs or tentative_g_cost < g_costs[neighbor]:
                    previous_nodes[neighbor] = current_node
                    g_costs[neighbor] = tentative_g_cost
                    f_cost = tentative_g_cost + self._heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_cost, neighbor))

        return []

    def _heuristic(self, node, goal):
        """Heurística de distancia de Manhattan."""
        return abs(node[0] - goal[0]) + abs(node[1] - goal[1])

    def _update_state(self):
        """Actualiza el estado emocional del Toyota según su felicidad."""
        if self.happiness < 50 and self.state != "ENOJADO":
            self.state = "ENOJADO"
        elif self.happiness >= 50 and self.state != "FELIZ":
            self.state = "FELIZ"

    def has_pending_tasks(self):
        """Verifica si el Toyota tiene tareas pendientes (buscar estacionamiento)."""
        return not self.parked
