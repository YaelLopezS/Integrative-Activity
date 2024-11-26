from flask import Flask, jsonify
from Ferrari_model import TrafficSimulation
from Ferrari import Vehicle

app = Flask(__name__)

# Inicializa la simulación con parámetros deseados
simulation = TrafficSimulation(width=25, height=25, num_vehicles=10)

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

def get_vehicle_positions():
    """
    Obtiene las posiciones actuales de los vehículos en la simulación.
    
    Returns:
        Listado de posiciones de vehículos como diccionarios.
    """
    vehicle_positions = []
    for agent in simulation.schedule.agents:
        if isinstance(agent, Vehicle):  # Verifica si el agente es un vehículo
            x, y = agent.pos  # Obtiene la posición del vehículo
            vehicle_positions.append({"x": x, "y": y})  # Agrega la posición a la lista
    return vehicle_positions

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)