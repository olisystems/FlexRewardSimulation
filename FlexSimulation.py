from datetime import timedelta, datetime
from typing import List
from CarSpecs import CarSpecs
from FlexibilityRequest import AvailableFlexibilityRequest
from FlexibilityCalculator import FlexibilityCalculator
from ChargingPoint import ChargingPoint
from multiprocessing import Process, Manager


class FlexibilitySimulation:
    def __init__(self, total_electricity, lock, power_supply: float, nominal_power_cp: float, time_step: int, connectors):
        self.lock = lock
        self.total_electricity = total_electricity
        self.power_supply = power_supply
        self.nominal_power_cp = nominal_power_cp
        self.time_step = time_step
        self.connector_available = connectors  # Shared list of connectors
        self.pending_requests = []
        self.charging_finished = []
        self.current_time = datetime.now()

    def handle_request(self, request: AvailableFlexibilityRequest):
        """ Handle the incoming flexibility request with constraints """
        # Constraint 1: Check if the request exceeds the power grid capacity
        if request.requested_energy > self.power_supply:
            print(f"Request from {request.session_id} rejected: exceeds power grid capacity.")
            return False, None

        # Constraint 2: Check if connector's charging capacity * duration < requested energy
        charging_duration = (request.requested_leave_time - request.charging_start_time).total_seconds() / 3600  # in hours
        if (self.nominal_power_cp * charging_duration) < request.requested_energy:
            print(f"Request from {request.session_id} rejected: requested energy exceeds connector's capability.")
            return False, None

        # Constraint 3: Check if the request can be fulfilled now or in the future
        projected_energy = self.total_electricity.value + request.requested_energy + sum(r.requested_energy for r in self.pending_requests)
        if projected_energy > self.power_supply:
            print(f"Request from {request.session_id} rejected: energy requirements cannot be fulfilled.")
            return False, None

        # Check if any connector is available, if so start charging
        available_connector_index = self.find_available_connector()

        if available_connector_index is not None:
            print(f"Request from {request.session_id} accepted for charging on connector {self.connector_available[available_connector_index].id}.")
            return True, available_connector_index
        else:
            self.pending_requests.append(request)
            print(f"Request from {request.session_id} is pending due to no available connectors.")
            return False, None

    def find_available_connector(self):
        """Find an available connector if any"""
        with self.lock:  # Locking to ensure safe access
            for i in range(len(self.connector_available)):
                if self.connector_available[i].isAvailable():
                    return i
        return None

    def simulate_charging(self, request: AvailableFlexibilityRequest, connector_index: int):
        with self.lock:  # Locking before modifying the connector
            if self.connector_available[connector_index].isAvailable():
                self.connector_available[connector_index].assign_request(request)
            else:
                print(f"Connector {connector_index} is not available for {request.session_id}.")
                return

        remaining_energy = request.requested_energy
        total_charging_time = (remaining_energy / self.nominal_power_cp) * 60  # in minutes

        while total_charging_time > 0 and remaining_energy > 0:
            charging_duration = min(self.time_step, total_charging_time)
            energy_charged = (charging_duration / 60) * self.nominal_power_cp

            if remaining_energy < energy_charged:
                energy_charged = remaining_energy
            remaining_energy -= energy_charged

            with self.lock:  # Locking shared resource
                self.total_electricity.value += energy_charged

            # Calculate current SOC
            charged_soc = (energy_charged / request.car_specs.battery_capacity_in_kwh) * 100
            request.current_soc += charged_soc

            # Print log with current SOC and power grid energy
            print(f"Charging session for {request.session_id} on connector {self.connector_available[connector_index].id}: {energy_charged:.2f} kWh charged.")
            print(f"Current SOC: {request.current_soc:.2f}%, Battery Power at Current Time: {(request.current_soc/100)*request.car_specs.battery_capacity_in_kwh}")
            print(f"Current Power Grid Energy Used: {self.total_electricity.value:.2f} kWh\n")

            total_charging_time -= charging_duration
            self.current_time += timedelta(minutes=charging_duration)

            if self.total_electricity.value > self.power_supply:
                print("Exceeded power supply. Stopping charging.")
                break

        with self.lock:  # Locking before finishing charging
            self.charging_finished.append(request)
            self.connector_available[connector_index].finish_charging()

            if request in self.pending_requests:
                self.pending_requests.remove(request)
                print(f"Request from {request.session_id} has been removed from the pending queue after completion.")

    def process_pending_requests(self):
        if self.pending_requests:
            self.pending_requests.sort(key=lambda x: FlexibilityCalculator.calculate_flexibility_contribution(x), reverse=True)
            next_request = self.pending_requests.pop(0)
            self.handle_request(next_request)

    def run_simulation(self, requests: List[AvailableFlexibilityRequest]):
        processes = []
        for request in requests:
            accepted, connector_index = self.handle_request(request)
            # Ensure that the request can be accepted based on constraints
            if accepted is True:
                p = Process(target=self.simulate_charging, args=(request, connector_index))
                processes.append(p)
                p.start()

        for p in processes:
            p.join()

if __name__ == '__main__':
    with Manager() as manager:
        total_electricity = manager.Value('d', 0.0)  # Shared total electricity value
        lock = manager.Lock()  # Shared lock for synchronizing access to shared resources
        num_connectors = 3

        # Create shared list of connectors
        connectors = manager.list([ChargingPoint(i + 1) for i in range(num_connectors)])  # Shared list of connectors
        power_supply = 30.0  # Total available power supply in kWh
        nominal_power_cp = 11.0  # Nominal charging power in kWh
        time_step = 10  # Time step in minutes

        # Example simulation usage
        car1 = CarSpecs(make="Tesla", model="Model S", year=2022, battery_capacity_in_kwh=75.5)
        request1 = AvailableFlexibilityRequest(
            session_id="user1",
            evse_id="EVSE001",
            requested_energy=20.0,
            requested_leave_time=datetime.now() + timedelta(hours=3),
            charging_start_time=datetime.now(),
            current_soc=50.0,  # Starting SOC in percentage
            car_specs=car1,
        )

        car2 = CarSpecs(make="Tesla", model="Model X", year=2022, battery_capacity_in_kwh=100)
        request2 = AvailableFlexibilityRequest(
            session_id="user2",
            evse_id="EVSE001",
            requested_energy=10.0,
            requested_leave_time=datetime.now() + timedelta(hours=3),
            charging_start_time=datetime.now(),
            current_soc=75,  # Starting SOC in percentage
            car_specs=car2,
        )

        requests = [request1, request2]
        simulation = FlexibilitySimulation(total_electricity, lock, power_supply, nominal_power_cp, time_step, connectors)
        simulation.run_simulation(requests)
