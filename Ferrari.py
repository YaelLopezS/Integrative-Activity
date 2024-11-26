from mesa import Agent
import heapq
from Mapa import Parking
from Negotiation import Negotiation

class Vehicle(Agent):
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

        # Verificar si hay otros vehículos cercanos para negociar
        neighbors = self.model.grid.get_neighbors(self.pos, moore=False, radius=1)
        vehicles_nearby = [agent for agent in neighbors if isinstance(agent, Vehicle) and not agent.parked]

        for other_vehicle in vehicles_nearby:
            # Realizar negociación si hay un conflicto
            action_self, action_other = Negotiation.negotiate(self, other_vehicle)

            # Resolver conflicto según el resultado de la negociación
            if action_self == "cede" and action_other == "compite":
                print(f"Vehículo {self.unique_id} cede el paso al vehículo {other_vehicle.unique_id}.")
                return
            elif action_self == "compite" and action_other == "cede":
                print(f"Vehículo {self.unique_id} avanza sobre el vehículo {other_vehicle.unique_id}.")
                break
            elif action_self == "cede" and action_other == "cede":
                print(f"Vehículo {self.unique_id} y {other_vehicle.unique_id} cooperan para evitar conflicto.")
                return
            elif action_self == "compite" and action_other == "compite":
                print(f"Vehículo {self.unique_id} y {other_vehicle.unique_id} están bloqueados. Buscando alternativas.")
                self.happiness -= 5  # Penalización por competencia inútil
                other_vehicle.happiness -= 5

        # Solicitar semáforo si se acerca a uno
        self.request_light = self._approaching_light()

        # Moverse si tiene luz verde o no está cerca de semáforos
        if self.light_granted or not self.request_light:
            if not self.path or self.pos == self.target:
                self._calculate_path()
            if self.path:
                self.move()

    def _approaching_light(self):
        """Verifica si el vehículo se acerca a un semáforo"""
        from Semaforo import TrafficLight
        for agent in self.model.grid.get_neighbors(self.pos, moore=False, radius=2):
            if isinstance(agent, TrafficLight):
                return True
        return False

    def _update_state(self):
        """Actualiza el estado emocional del vehículo según su felicidad."""
        if self.happiness < 50 and self.state != "ANGRY":
            self.state = "ANGRY"
        elif self.happiness >= 50 and self.state != "NORMAL":
            self.state = "NORMAL"

    def _calculate_path(self):
        """Calcula el camino más corto a un estacionamiento usando Dijkstra."""
    
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
        parkings = [
            agent.pos
            for content, pos in self.model.grid.coord_iter()
            for agent in content
            if isinstance(agent, Parking) and not agent.is_occupied
        ]
    
        #print(f"Vehículo {self.unique_id}: Estacionamientos detectados: {parkings}")

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

    def _dijkstra(self,graph, start, goal):
        # Algoritmo de Dijkstra para encontrar la ruta más corta
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

    def move(self):
        """Mueve el vehículo al siguiente paso en el camino calculado."""
        if self.path:
            next_position = self.path[0]

            # Verificar si el próximo espacio es un estacionamiento
            if next_position == self.target:
                # Obtener el contenido de la celda del estacionamiento
                parking_spot = self.model.grid.get_cell_list_contents([next_position])
                parking_agent = next((agent for agent in parking_spot if isinstance(agent, Parking)), None)

                if parking_agent and parking_agent.is_occupied:
                    #print(f"Vehículo {self.unique_id}: Estacionamiento ocupado en {next_position}. Buscando otro.")
                    self._calculate_path()  # Recalcular la ruta hacia otro estacionamiento
                    return

                # Si el espacio está libre, marcarlo como ocupado
                if parking_agent:
                    parking_agent.occupy()

                print(f"Vehículo {self.unique_id}: Se ha estacionado en {next_position}.")
                self.model.grid.move_agent(self, next_position)
                self.parked = True  # Marcar el vehículo como estacionado
                return  # Detenerse aquí al llegar al estacionamiento

            # Si no es un estacionamiento, mover hacia la siguiente posición
            from Semaforo import TrafficLight
            if self.model.grid.is_cell_empty(next_position) or any(isinstance(agent, TrafficLight) for agent in self.model.grid.get_cell_list_contents([next_position])):
                self.model.grid.move_agent(self, next_position)
                self.path.pop(0)
            else:
                # Si está bloqueado por un obstáculo no permitido
                self.happiness -= 10
                if self.state == "ANGRY":
                    self._attempt_lane_change()

    def _attempt_lane_change(self):
        """Intenta cambiar de carril si está bloqueado."""
        neighbors = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
        
        for neighbor in neighbors:
            if self.model.grid.is_cell_empty(neighbor) and neighbor[0] > 0 and neighbor[1] > 0:
                self.model.grid.move_agent(self, neighbor)
                #print(f"Vehículo {self.unique_id}: Cambió de carril a {neighbor}")
                return