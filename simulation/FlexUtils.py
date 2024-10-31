from datetime import timedelta, datetime
import random
from typing import List
from CarSpecs import CarSpecs
from FlexibilityRequest import AvailableFlexibilityRequest
from ChargingPoint import ChargingPoint

# List of random car models and battery capacities
car_models = [
    ("Tesla", "Model S", 100),
    ("Tesla", "Model X", 100),
    ("Tesla", "Model 3", 75),
    ("Nissan", "Leaf", 40),
    ("Chevrolet", "Bolt", 66),
    ("BMW", "i3", 42),
    ("Audi", "e-tron", 95)
]

def generate_random_car() -> CarSpecs:
    """Generates a random car from the available models with random battery SOC."""
    make, model, battery_capacity = random.choice(car_models)
    initial_soc = random.uniform(20, 80)  # Random initial state of charge between 20% and 80%
    return CarSpecs(make=make, model=model, year=2022, battery_capacity_in_kwh=battery_capacity, initial_soc=initial_soc)

def generate_random_request(id:int, connector: ChargingPoint, car: CarSpecs) -> AvailableFlexibilityRequest:
    """Generates a random charging request for a given car and charging connector."""
    current_time = datetime.now()
    arrival_time = current_time + timedelta(minutes=random.randint(0, 60))  # Random arrival time within next 60 minutes
    requested_leave_time = random.uniform(1, 6) * 60 # Random leave time 1-6 hours after arrival
    requested_energy = random.uniform(10, 30)  # Random energy request between 10kWh and 30kWh

    # Generate a session ID (can be based on the current timestamp and a random number)
    session_id = f"user_{id}"

    return AvailableFlexibilityRequest(
        session_id=session_id,
        evse_id=connector,
        requested_energy=requested_energy,
        requested_leave_time=requested_leave_time,
        arrival_time=arrival_time,
        car_specs=car,
        charged_time=0,
        charged_energy=0
    )

def generate_random_requests(num_requests: int, connectors: List[ChargingPoint]) -> List[AvailableFlexibilityRequest]:
    """Generates a list of random charging requests based on the number of requests and available connectors."""
    requests = []
    for i in range(num_requests):
        car = generate_random_car()  # Create a random car
        connector = connectors[i % len(connectors)]  # Assign connectors in a round-robin fashion
        request = generate_random_request(i+1,connector, car)
        requests.append(request)
    return requests

