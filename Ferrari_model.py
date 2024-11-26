from mesa import Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector
from Ferrari import Vehicle
from Semaforo import TrafficLight
from Mapa import Building, Parking, Roundabout, Lane

class TrafficSimulation(Model):
    def __init__(self, width, height, num_vehicles):
        super().__init__()
        
        # Crear espacio y activador
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = SimultaneousActivation(self)

        # Las posiciones de nuestros carriles con sus direcciones
        self.lanes_positions = [
            # --- CARRILES HORIZONTALES ---

            # --- De derecha a izquierda ---
            Lane([(x, 1) for x in range(24, 0, -1)], "right_to_left"),
            Lane([(x, 2) for x in range(24, 0, -1)], "right_to_left"),
            Lane([(x, 6) for x in range(13, 7, -1)], "right_to_left"),
            Lane([(x, 7) for x in range(13, 7, -1)], "right_to_left"),
            Lane([(x, 7) for x in range(23, 15, -1)], "right_to_left"),
            Lane([(x, 8) for x in range(23, 15, -1)], "right_to_left"),
            Lane([(x, 14) for x in range(13, 1, -1)], "right_to_left"),
            Lane([(x, 13) for x in range(23, 1, -1)], "right_to_left"),
            Lane([(x, 14) for x in range(23, 15, -1)], "right_to_left"),
            Lane([(x, 19) for x in range(7, 1, -1)], "right_to_left"),
            Lane([(x, 20) for x in range(7, 1, -1)], "right_to_left"),

            # --- De izquierda a derecha ---
            Lane([(x, 15) for x in range(2, 14)], "left_to_right"),
            Lane([(x, 16) for x in range(2, 24)], "left_to_right"),
            Lane([(x, 15) for x in range(16, 24)], "left_to_right"),
            Lane([(x, 19) for x in range(8, 14)], "left_to_right"),
            Lane([(x, 20) for x in range(8, 14)], "left_to_right"),
            Lane([(x, 23) for x in range(1, 25)], "left_to_right"),
            Lane([(x, 24) for x in range(1, 25)], "left_to_right"),


            # --- CARRILES VERTICALES ---

            # --- De arriba hacia abajo ---
            Lane([(1, y) for y in range(1, 25)], "down"),
            Lane([(2, y) for y in range(1, 25)], "down"),
            Lane([(7, y) for y in range(16, 24)], "down"),
            Lane([(8, y) for y in range(16, 24)], "down"),
            Lane([(13, y) for y in range(2, 24)], "down"),
            Lane([(14, y) for y in range(2, 14)], "down"),
            Lane([(14, y) for y in range(16, 24)], "down"),

            # --- De abajo hacia arriba ---
            Lane([(7, y) for y in range(13, 1, -1)], "up"),
            Lane([(8, y) for y in range(13, 1, -1)], "up"),
            Lane([(15, y) for y in range(13, 1, -1)], "up"),
            Lane([(15, y) for y in range(23, 15, -1)], "up"),
            Lane([(16, y) for y in range(23, 1, -1)], "up"),
            Lane([(19, y) for y in range(23, 15, -1)], "up"),
            Lane([(20, y) for y in range(23, 15, -1)], "up"),
            Lane([(23, y) for y in range(24, 0, -1)], "up"),
            Lane([(24, y) for y in range(24, 0, -1)], "up"),

            # --- CAMINOS PARA METERSE A LOS ESTACIONAMIENTOS ---
            Lane([(x, 10) for x in range(2, 4)], "left_to_right"), # Para meterse al 1
            Lane([(4, y) for y in range(2, 4)], "down"), # Para meterse al 2
            Lane([(4, y) for y in range(19, 17, -1)], "up"), # Para meterse al 3
            Lane([(5, y) for y in range(13, 11, -1)], "up"), # Para meterse al 4
            Lane([(5, y) for y in range(20, 22)], "down"), # Para meterse al 5
            Lane([(x, 7) for x in range(7, 5, -1)], "right_to_left"), # Para meterse al 6
            Lane([(x, 9) for x in range(8, 10)], "left_to_right"), # Para meterse al 7
            Lane([(10, y) for y in range(23, 21, -1)], "up"), # Para meterse al 8
            Lane([(11, y) for y in range(6, 4, -1)], "up"), # Para meterse al 9
            Lane([(11, y) for y in range(13, 11, -1)], "up"), # Para meterse al 10
            Lane([(11, y) for y in range(16, 18)], "down"), # Para meterse al 11
            Lane([(18, y) for y in range(2, 4)], "down"), # Para meterse al 12
            Lane([(x, 18) for x in range(19, 17, -1)], "right_to_left"), # Para meterse al 13
            Lane([(x, 20) for x in range(19, 17, -1)], "right_to_left"), # Para meterse al 14
            Lane([(21, y) for y in range(7, 5, -1)], "up"), # Para meterse al 15
            Lane([(21, y) for y in range(8, 10)], "down"), # Para meterse al 16
            Lane([(x, 20) for x in range(20, 22)], "left_to_right"), # Para meterse al 17

        ]

        # Elementos del entorno
        self._place_static_elements()
        
        # Creamos nuestros agentes de vehículo del Ferrari
        for i in range(num_vehicles):
            vehicle = Vehicle(self.next_id(), self)
            self.schedule.add(vehicle)
            x, y = self.random_empty_position()
            self.grid.place_agent(vehicle, (x, y))
        
        self.running = True
        self.datacollector = DataCollector(agent_reporters={"Happiness": "happiness"})

    def get_lanes_positions(self):
        """Devuelve las posiciones de los carriles"""
        return [(lane.positions, lane.direction) for lane in self.lanes_positions]

    def _place_static_elements(self):
        # Coordenadas específicas para los edificios
        building_positions = [
            # --- PRIMER CUADRANTE ---

            # ---- Primer edificio ---
            [(3, y) for y in range(3, 10)],  # Edificios en la columna 3 desde la fila 3 a la 9
            [(3, y) for y in range(11, 13)],  # Edificios en la columna 3 desde la fila 11 a la 12
            [(4, y) for y in range(4, 13)],  # Edificios en la columna 4 desde la fila 4 a la 12
            [(5, y) for y in range(3, 12)],   # Edificios en la columna 5 desde la fila 3 a la 11
            [(6, y) for y in range(3, 7)],   # Edificios en la columna 6 desde la fila 3 a la 6
            [(6, y) for y in range(8, 13)],   # Edificios en la columna 6 desde la fila 8 a la 13

            # ---- Segundo edificio ---
            [(9, y) for y in range(3, 6)],  # Edificios en la columna 9 desde la fila 3 a la 5
            [(9, y) for y in range(8, 9)],  # Edificios en la columna 9 desde la fila 8 a la 8
            [(9, y) for y in range(10, 13)],  # Edificios en la columna 9 desde la fila 10 a la 12
            [(10, y) for y in range(3, 6)],  # Edificios en la columna 10 desde la fila 3 a la 5
            [(10, y) for y in range(8, 13)],  # Edificios en la columna 10 desde la fila 8 a la 12
            [(11, y) for y in range(3, 5)],  # Edificios en la columna 11 desde la fila 3 a la 4
            [(11, y) for y in range(8, 12)],  # Edificios en la columna 11 desde la fila 8 a la 11
            [(12, y) for y in range(3, 6)],  # Edificios en la columna 12 desde la fila 3 a la 5
            [(12, y) for y in range(8, 13)],  # Edificios en la columna 12 desde la fila 8 a la 12


            # --- SEGUNDO CUADRANTE ---
            [(17, y) for y in range(3, 7)],  # Edificios en la columna 17 desde la fila 3 a la 6
            [(17, y) for y in range(9, 13)],  # Edificios en la columna 17 desde la fila 9 a la 12
            [(18, y) for y in range(4, 7)],  # Edificios en la columna 18 desde la fila 4 a la 6
            [(18, y) for y in range(9, 13)],  # Edificios en la columna 18 desde la fila 9 a la 12
            [(19, y) for y in range(3, 7)],  # Edificios en la columna 19 desde la fila 3 a la 6
            [(19, y) for y in range(9, 13)],  # Edificios en la columna 19 desde la fila 9 a la 12
            [(20, y) for y in range(3, 7)],  # Edificios en la columna 20 desde la fila 3 a la 6
            [(20, y) for y in range(9, 13)],  # Edificios en la columna 20 desde la fila 9 a la 12
            [(21, y) for y in range(3, 6)],  # Edificios en la columna 21 desde la fila 3 a la 5
            [(21, y) for y in range(10, 13)],  # Edificios en la columna 21 desde la fila 10 a la 12
            [(22, y) for y in range(3, 7)],  # Edificios en la columna 22 desde la fila 3 a la 6
            [(22, y) for y in range(9, 13)],  # Edificios en la columna 22 desde la fila 9 a la 12


            # --- TERCER CUADRANTE ---

            # ---- Primer edificio ---
            [(3, y) for y in range(17, 19)],  # Edificios en la columna 3 desde la fila 17 a la 18
            [(3, y) for y in range(21, 23)],  # Edificios en la columna 3 desde la fila 21 a la 22
            [(4, y) for y in range(17, 18)],  # Edificios en la columna 4 desde la fila 17 a la 17
            [(4, y) for y in range(21, 23)],  # Edificios en la columna 4 desde la fila 21 a la 22
            [(5, y) for y in range(17, 19)],  # Edificios en la columna 5 desde la fila 17 a la 18
            [(5, y) for y in range(22, 23)],  # Edificios en la columna 5 desde la fila 22 a la 22
            [(6, y) for y in range(17, 19)],  # Edificios en la columna 6 desde la fila 17 a la 18
            [(6, y) for y in range(21, 23)],  # Edificios en la columna 6 desde la fila 21 a la 22

            # ---- Segundo edificio ---
            [(9, y) for y in range(17, 19)],  # Edificios en la columna 9 desde la fila 17 a la 18
            [(9, y) for y in range(21, 23)],  # Edificios en la columna 9 desde la fila 21 a la 22
            [(10, y) for y in range(17, 19)],  # Edificios en la columna 10 desde la fila 17 a la 18
            [(10, y) for y in range(21, 22)],  # Edificios en la columna 10 desde la fila 21 a la 21
            [(11, y) for y in range(18, 19)],  # Edificios en la columna 11 desde la fila 18 a la 18
            [(11, y) for y in range(21, 23)],  # Edificios en la columna 11 desde la fila 21 a la 22
            [(12, y) for y in range(17, 19)],  # Edificios en la columna 12 desde la fila 17 a la 18
            [(12, y) for y in range(21, 23)],  # Edificios en la columna 12 desde la fila 21 a la 22


            # --- CUARTO CUADRANTE ---

            # ---- Primer edificio ---
            [(17, y) for y in range(17, 23)],  # Edificios en la columna 17 desde la fila 17 a la 22
            [(17, y) for y in range(17, 23)],  # Edificios en la columna 17 desde la fila 17 a la 22
            [(18, y) for y in range(17, 18)],  # Edificios en la columna 18 desde la fila 17 a la 17
            [(18, y) for y in range(19, 20)],  # Edificios en la columna 18 desde la fila 19 a la 19
            [(18, y) for y in range(21, 23)],  # Edificios en la columna 18 desde la fila 21 a la 22
            [(21, y) for y in range(17, 20)],  # Edificios en la columna 21 desde la fila 17 a la 19
            [(21, y) for y in range(21, 23)],  # Edificios en la columna 21 desde la fila 21 a la 22
            [(22, y) for y in range(17, 23)],  # Edificios en la columna 22 desde la fila 17 a la 22
        ]
    
        # Colocar edificios según las posiciones definidas
        for positions in building_positions:
            for pos in positions:
                if self.grid.is_cell_empty(pos):  # Verificar si la celda está vacía
                    building = Building(self.next_id(), self)
                    self.grid.place_agent(building, pos)
                    self.schedule.add(building)
    
        # Coordenadas específicas para los estacionamientos
        parking_positions = [
            [(3,10)],
            [(4,3)],
            [(5,12)],
            [(6,7)],
            [(9,9)],
            [(11,5)],
            [(11,12)],
            [(4,18)],
            [(5,21)],
            [(10,22)],
            [(11,17)],
            [(18,3)],
            [(21,6)],
            [(21,9)],
            [(18,18)],
            [(18,20)],
            [(21,20)],
        ]
        

        # Colocar estacionamientos según las posiciones definidas
        for positions in parking_positions:
            for pos in positions:
                if self.grid.is_cell_empty(pos):  # Verificar si la celda está vacía
                    parking = Parking(self.next_id(), self)
                    self.grid.place_agent(parking, pos)
                    self.schedule.add(parking)

        print(f"Estacionamientos colocados en: {parking_positions}")

        # Coordenadas específicas para los semaforos
        lights_positions = [
            # --- Semaforos horizontales ---
            [(x, 18) for x in range(1, 3)],
            [(x, 3) for x in range(7, 9)],
            [(x, 8) for x in range(7, 9)],
            [(x, 22) for x in range(7, 9)],
            [(x, 17) for x in range(19, 21)],

            # --- Semaforos verticales ---
            [(3, y) for y in range(19, 21)],
            [(6, y) for y in range(23, 25)],
            [(9, y) for y in range(1, 3)],
            [(9, y) for y in range(6, 8)],
            [(18, y) for y in range(15, 17)],
        ]

        # Colocar semaforos según las posiciones definidas
        for positions in lights_positions:
            for pos in positions:
                if self.grid.is_cell_empty(pos):  # Verificar si la celda está vacía
                    light = TrafficLight(self.next_id(), self)
                    self.grid.place_agent(light, pos)
                    self.schedule.add(light)
        

        # Coordenadas específicas para la glorieta
        roundabouts_positions = [
            [(14, y) for y in range(14, 16)],
            [(15, y) for y in range(14, 16)],
        ]

        # Colocar semaforos según las posiciones definidas
        for positions in roundabouts_positions:
            for pos in positions:
                if self.grid.is_cell_empty(pos):  # Verificar si la celda está vacía
                    roundabout = Roundabout(self.next_id(), self)
                    self.grid.place_agent(roundabout, pos)
                    self.schedule.add(roundabout)

    def random_empty_position(self):
        while True:
            x = self.random.randint(1, self.grid.width - 1)
            y = self.random.randint(1, self.grid.height - 1)
            if self.grid.is_cell_empty((x, y)):
                return (x, y)
    
    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)

        # Verificar si todos los vehículos están estacionados
        all_parked = all(agent.parked for agent in self.schedule.agents if isinstance(agent, Vehicle))
        if all_parked:
            print("Todos los vehículos están estacionados. Terminando simulación.")
            self.running = False
