from mesa import Agent

class Building(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class Parking(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.is_occupied = False  # Estado inicial del estacionamiento

    def occupy(self):
        """Marca el espacio como ocupado."""
        self.is_occupied = True

    def vacate(self):
        """Marca el espacio como desocupado."""
        self.is_occupied = False

class Roundabout(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class Lane:
    def __init__(self, positions, direction):
        self.positions = positions
        self.direction = direction
