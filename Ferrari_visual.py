import matplotlib.pyplot as plt
import matplotlib.patches as patches
from Semaforo import TrafficLight
from Ferrari import Vehicle
from Ferrari_model import TrafficSimulation
from Mapa import Building, Parking, Roundabout

# Configura el modelo
model = TrafficSimulation(width=25, height=25, num_vehicles=5)

# Configura la figura de Matplotlib
fig, ax = plt.subplots(figsize=(8, 8))

# Función de renderizado
def render_model(model, ax):
    ax.clear()  # Con esto se limpia el gráfico actual
    
    ax.set_xlim(1, model.grid.width) 
    ax.set_ylim(1, model.grid.height) 
    
    # Configuramos las marcas de los ejes para que vayan desde 1 hasta el tamaño del grid
    ax.set_xticks(range(1, model.grid.width )) 
    ax.set_yticks(range(1, model.grid.height )) 

    # Invertimos el eje Y para que vaya de 24 a 1
    #ax.invert_yaxis()
    
    ax.grid(True, which='both', color='gray', linestyle='--', linewidth=0.5)

     # Dibujamos los carriles como líneas delgadas naranjas
    for lane in model.lanes_positions:
        x_values = [coord[0] + 0.5 for coord in lane.positions]  # Ajusta la posición en X para centrar la línea
        y_values = [coord[1] + 0.5 for coord in lane.positions]  # Ajusta la posición en Y para centrar la línea
        ax.plot(x_values, y_values, color="orange", linewidth=2)  # Dibuja la línea delgada

    # Dibuja agentes según su tipo
    for (content, pos) in model.grid.coord_iter():
        x, y = pos
        for agent in content:
            if isinstance(agent, TrafficLight):
                color = "green" if agent.state == "GREEN" else "red" if agent.state == "RED" else "yellow"
                rect = patches.Rectangle((x, y), 1, 1, color=color, ec="black")  
                ax.add_patch(rect)
            elif isinstance(agent, Vehicle):
                color = "blue" if agent.state == "NORMAL" else "yellow"
                circle = patches.Circle((x + 0.5, y + 0.5), radius=0.4, color=color, ec="black")  
                ax.add_patch(circle)
            elif isinstance(agent, Building):
                rect = patches.Rectangle((x, y), 1, 1, color="blue")
                ax.add_patch(rect)
            elif isinstance(agent, Parking):
                rect = patches.Rectangle((x, y), 1, 1, color="yellow")  
                ax.add_patch(rect)
            elif isinstance(agent, Roundabout):
                rect = patches.Rectangle((x, y), 1, 1, color="brown")  
                ax.add_patch(rect)

# Bucle de simulación
for i in range(100):  # Máximo de pasos
    model.step()
    
    # Renderizar el modelo en cada paso
    render_model(model, ax)
    plt.pause(0.1)  # Pausa para visualizar el paso
    
    # Si todos los vehiculos se estacionaron, se detiene
    if not model.running:
        break  # Detener el bucle si la simulación ha terminado
    if i == 99:
        print("Se acabaron los pasos de la simulación")

plt.show()
