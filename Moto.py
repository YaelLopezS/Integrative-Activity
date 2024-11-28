from mesa import Agent
import heapq
from Mapa import Parking
from Negotiation import Negotiation

class Moto(Agent):
    NORMAL_SPEED = 1
    ANGRY_SPEED = 2

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = "NORMAL"  # Estados: NORMAL, ANGRY
        self.happiness = 100  # Métrica de felicidad inicial
        self.path = None
        self.target = None  # Estacionamiento objetivo
        self.request_light = False  # Solicita un semáforo
        self.light_granted = False  # Indica si el semáforo le otorgó paso
        self.parked = False

    def step(self):
        if self.parked:
            return

        # Actualizar estado y felicidad
        self._update_state()

        # Velocidad según estado emocional
        speed = self.ANGRY_SPEED if self.state == "ANGRY" else self.NORMAL_SPEED

        # Verificar si hay otros vehículos cercanos para negociar
        neighbors = self.model.grid.get_neighbors(self.pos, moore=False, radius=1)
        vehicles_nearby = [agent for agent in neighbors if isinstance(agent, Moto) and not agent.parked]

        for other_vehicle in vehicles_nearby:
            action_self, action_other = Negotiation.negotiate(self, other_vehicle)
            if action_self == "cede" and action_other == "compite":
                print(f"Moto {self.unique_id} cede el paso al moto {other_vehicle.unique_id}.")
                return
            elif action_self == "compite" and action_other == "cede":
                print(f"Moto {self.unique_id} avanza sobre el moto {other_vehicle.unique_id}.")
                break
            elif action_self == "cede" and action_other == "cede":
                print(f"Moto {self.unique_id} y {other_vehicle.unique_id} cooperan para evitar conflicto.")
                return
            elif action_self == "compite" and action_other == "compite":
                print(f"Moto {self.unique_id} y {other_vehicle.unique_id} están bloqueados. Buscando alternativas.")
                self.happiness -= 5
                other_vehicle.happiness -= 5

        self.request_light = self._approaching_light()

        # Semáforo según estado
        if self.request_light:
            if self.state == "ANGRY" and not self._other_cars_at_light():
                print(f"Vehículo {self.unique_id} se salta el semáforo.")
                self.light_granted = True

        if self.light_granted or not self.request_light:
            if not self.path or self.pos == self.target:
                self._calculate_path()
            if self.path:
                self.move(speed)

    def _update_state(self):
        """Actualiza el estado emocional del vehículo según su felicidad."""
        if self.happiness < 50 and self.state != "ANGRY":
            self.state = "ANGRY"
        elif self.happiness >= 50 and self.state != "NORMAL":
            self.state = "NORMAL"

    def _approaching_light(self):
        """Verifica si el vehículo se acerca a un semáforo."""
        from Semaforo import TrafficLight
        for agent in self.model.grid.get_neighbors(self.pos, moore=False, radius=2):
            if isinstance(agent, TrafficLight):
                return True
        return False

    def _other_cars_at_light(self):
        """Verifica si hay otros coches en el semáforo."""
        from Semaforo import TrafficLight
        return any(isinstance(agent, Moto) for agent in self.model.grid.get_neighbors(self.pos, moore=False, radius=1) if isinstance(agent, TrafficLight))

    def _calculate_path(self):
        """Calcula el camino más corto a un estacionamiento usando Dijkstra."""
        lanes_positions = self.model.get_lanes_positions()
        graph = {}
        for lane, direction in lanes_positions:
            for i in range(len(lane) - 1):
                graph.setdefault(lane[i], []).append((lane[i+1], 1))

        start = self.pos
        parkings = [
            agent.pos
            for content, pos in self.model.grid.coord_iter()
            for agent in content
            if isinstance(agent, Parking) and not agent.is_occupied
        ]

        if not parkings:
            print(f"Vehículo {self.unique_id}: No hay estacionamientos disponibles.")
            self.path = None
            return

        closest_parking = None
        shortest_path = None
        shortest_distance = float('inf')

        for parking in parkings:
            path = self._dijkstra(graph, start, parking)
            if path and len(path) < shortest_distance:
                closest_parking = parking
                shortest_path = path
                shortest_distance = len(path)

        if closest_parking and shortest_path:
            self.target = closest_parking
            self.path = shortest_path
        else:
            print(f"Vehículo {self.unique_id}: No hay camino a un estacionamiento.")
            self.path = None

    def _dijkstra(self, graph, start, goal):
        queue = [(0, start)]
        distances = {start: 0}
        previous_nodes = {start: None}

        while queue:
            current_distance, current_node = heapq.heappop(queue)

            if current_node == goal:
                path = []
                while previous_nodes[current_node] is not None:
                    path.append(current_node)
                    current_node = previous_nodes[current_node]
                path.append(start)
                return path[::-1]

            for neighbor, weight in graph.get(current_node, []):
                distance = current_distance + weight
                if neighbor not in distances or distance < distances[neighbor]:
                    distances[neighbor] = distance
                    heapq.heappush(queue, (distance, neighbor))
                    previous_nodes[neighbor] = current_node

        return []

    def move(self, speed):
        """Mueve el vehículo al siguiente paso en el camino calculado."""
        for _ in range(speed):
            if self.path:
                next_position = self.path[0]
                if next_position == self.target:
                    parking_spot = self.model.grid.get_cell_list_contents([next_position])
                    parking_agent = next((agent for agent in parking_spot if isinstance(agent, Parking)), None)
                    if parking_agent and not parking_agent.is_occupied:
                        parking_agent.occupy()
                        print(f"Vehículo {self.unique_id}: Se ha estacionado en {next_position}.")
                        self.model.grid.move_agent(self, next_position)
                        self.parked = True
                        return
                if self.model.grid.is_cell_empty(next_position):
                    self.model.grid.move_agent(self, next_position)
                    self.path.pop(0)
                else:
                    self.happiness -= 10
                    if self.state == "ANGRY":
                        self._attempt_lane_change()
            else:
                break

    def _attempt_lane_change(self):
        """Intenta cambiar de carril o meterse entre vehículos si está bloqueado."""
        neighbors = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
        for neighbor in neighbors:
            if self.model.grid.is_cell_empty(neighbor):
                print(f"Vehículo {self.unique_id}: Cambiando de carril a {neighbor}.")
                self.model.grid.move_agent(self, neighbor)
                return

        ahead_positions = self.model.grid.get_neighborhood(self.pos, moore=False, radius=1)
        vehicles_ahead = [agent for pos in ahead_positions for agent in self.model.grid.get_cell_list_contents([pos])
                          if isinstance(agent, Moto) and not agent.parked]

        if vehicles_ahead:
            possible_positions = [
                pos for pos in ahead_positions
                if self.model.grid.is_cell_empty(pos) or all(
                    isinstance(agent, Moto) and agent.state == "NORMAL" for agent in self.model.grid.get_cell_list_contents([pos]))
            ]
            if possible_positions:
                chosen_position = possible_positions[0]
                print(f"Vehículo {self.unique_id}: Intentando meterse entre vehículos hacia {chosen_position}.")
                self.model.grid.move_agent(self, chosen_position)
                self.happiness -= 5
            else:
                print(f"Vehículo {self.unique_id}: No hay espacio para meterse entre los vehículos.")
                self.happiness -= 10