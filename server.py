from flask import Flask, jsonify, request
from mesa.visualization.modules import CanvasGrid
from Ferrari_model import TrafficSimulation
from Ferrari import Vehicle
from Microbus import Microbus
from Jeep import Jeeps
from Toyota import Toyota
from Moto import Moto
from Semaforo import TrafficLight

app = Flask(__name__)

# Inicializa la simulación con parámetros deseados
simulation = TrafficSimulation(width=25, height=25, num_vehicles=4, num_microbus=4, num_moto=4, num_jeeps=4, num_toyota=4)

@app.route("/")
def index():
    return jsonify({"Message": "Bienvenido a la Simulación de Tráfico!"})

@app.route("/positions", methods=['GET'])
def positions():
    """
    Endpoint para obtener las posiciones actuales de todos los vehículos.
    """
    simulation.step()  # Avanza un paso en la simulación
    positions = get_vehicle_positions()
    return jsonify({"vehicles": positions})

@app.route("/lights_positions", methods=['GET'])
def lights_positions():
    """
    Endpoint para obtener las posiciones y estados de los semáforos.
    """
    lights = get_lights_positions()
    return jsonify({"traffic_lights": lights})

def get_vehicle_positions():
    """
    Obtiene las posiciones actuales de los vehículos en la simulación.
    
    Returns:
        Listado de posiciones de vehículos como diccionarios.
    """
    vehicle_positions = []
    for agent in simulation.schedule.agents:
        if isinstance(agent, Vehicle):  # Verifica si el agente es un vehículo
            x, z = agent.pos  # Obtiene la posición del vehículo
            vehicle_positions.append({"x": x, "z": z})  # Agrega la posición a la lista
        elif isinstance(agent, Microbus):  # Verifica si el agente es un microbús
            x, z = agent.pos  # Obtiene la posición del vehículo
            vehicle_positions.append({"x": x, "z": z})  # Agrega la posición a la lista
        elif isinstance(agent, Jeeps):  # Verifica si el agente es un vehículo
            x, z = agent.pos  # Obtiene la posición del vehículo
            vehicle_positions.append({"x": x, "z": z})  # Agrega la posición a la lista
        elif isinstance(agent, Toyota):  # Verifica si el agente es un vehículo
            x, z = agent.pos  # Obtiene la posición del vehículo
            vehicle_positions.append({"x": x, "z": z})  # Agrega la posición a la lista
        elif isinstance(agent, Moto):  # Verifica si el agente es un vehículo
            x, z = agent.pos  # Obtiene la posición del vehículo
            vehicle_positions.append({"x": x, "z": z})  # Agrega la posición a la lista
    return vehicle_positions

def get_lights_positions():
    """
    Obtiene las posiciones y estados actuales de los semáforos en la simulación.
    Los datos provienen de los agentes en el modelo.
    
    Returns:
        Listado de semáforos como diccionarios con posición, estado y ID.
    """
    semaforo_positions = []
    for agent in simulation.schedule.agents:
        if isinstance(agent, TrafficLight):  # Verifica si el agente es un semáforo
            x, y = agent.pos  # Obtiene la posición del semáforo
            state = agent.state if hasattr(agent, 'state') else "UNKNOWN"  # Estado actual
            semaforo_positions.append({
                "id": agent.unique_id,  # ID único del semáforo
                "position": [x, y],  # Posición del semáforo
                "state": state  # Estado actual (verde, rojo, amarillo)
            })
    return semaforo_positions


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)