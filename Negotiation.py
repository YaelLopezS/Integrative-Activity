# ------------------------ Nuestra negociacion ----------------
import random

class Negotiation:
    """Clase para manejar la negociación entre dos vehículos basada en la teoría de juegos."""

    payoff_matrix = {
        ("cede", "cede"): (2, 2),
        ("cede", "compite"): (3, 1),
        ("compite", "cede"): (1, 3),
        ("compite", "compite"): (0, 0),
    }

    @staticmethod
    def negotiate(vehicle_a, vehicle_b):
        """
        Realiza una negociación entre dos vehículos.
        
        Args:
            vehicle_a (Vehicle): Primer vehículo.
            vehicle_b (Vehicle): Segundo vehículo.

        Returns:
            tuple: Acciones seleccionadas por ambos vehículos ("cede" o "compite").
        """
        # Los vehículos eligen una estrategia (por ahora, aleatoria)
        choice_a = random.choice(["cede", "compite"])
        choice_b = random.choice(["cede", "compite"])

        # Obtener las recompensas de la matriz de pagos
        reward_a, reward_b = Negotiation.payoff_matrix[(choice_a, choice_b)]

        # Actualizar la felicidad de los vehículos con base en la recompensa obtenida
        vehicle_a.happiness += reward_a
        vehicle_b.happiness += reward_b

        print(f"Vehículo {vehicle_a.unique_id} ({choice_a}) vs Vehículo {vehicle_b.unique_id} ({choice_b}): "
              f"Recompensas -> A: {reward_a}, B: {reward_b}")

        return choice_a, choice_b
