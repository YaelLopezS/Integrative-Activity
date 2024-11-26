from mesa import Agent
from Ferrari import Vehicle

def get_distance(pos1, pos2):
    """Calcula la distancia Manhattan entre dos posiciones."""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

class TrafficLight(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = "YELLOW"  # Estados iniciales: YELLOW, GREEN, RED
        self.time_remaining = 0
        self.queue = []  # Cola de vehículos

    def step(self):
        # Actualizar estado de las luces
        if self.time_remaining > 0:
            self.time_remaining -= 1
        else:
            if self.state == "GREEN":
                self.state = "RED"
                self.time_remaining = 3  # Luz roja para otros vehículos
            elif self.state == "RED":
                self.state = "YELLOW"
            else:  # Luz amarilla
                self._process_vehicle_requests()

    def _process_vehicle_requests(self):
        """Procesa las solicitudes de los vehículos cercanos."""
        requesting_vehicles = [
            agent for agent in self.model.schedule.agents
            if isinstance(agent, Vehicle) and agent.request_light
        ]

        # Procesar vehículos cercanos al semáforo (distancia <= 2)
        for vehicle in requesting_vehicles:
            distance = get_distance(self.pos, vehicle.pos)
            if distance <= 2:
                self.queue.append((distance, vehicle))
        
        # Ordenar vehículos por proximidad
        self.queue.sort(key=lambda x: x[0])

        # Otorgar luz verde al vehículo más cercano
        if self.queue:
            _, vehicle = self.queue.pop(0)
            self.state = "GREEN"
            self.time_remaining = 3  # Luz verde durante 3 segundos
            vehicle.light_granted = True
            # Los demás vehículos verán la luz roja
            for _, v in self.queue:
                v.light_granted = False

