import matplotlib.pyplot as plt
from datetime import timedelta, datetime
from typing import List
from CarSpecs import CarSpecs
from FlexibilityRequest import AvailableFlexibilityRequest
from FlexibilityCalculator import FlexibilityCalculator
from ChargingPoint import ChargingPoint

class FlexibilitySimulation:
    def __init__(self, power_supply: float, time_step: int, connectors, connectors_in_use):
        self.power_supply = power_supply
        self.time_step = time_step
        self.queued_requests: List[AvailableFlexibilityRequest] = []  # List of pending requests
        self.current_time = datetime.now()

    def flexibility_demand(self):       
        total_power_demand = 0.0
        
        for request in self.queued_requests:
            charged_time_in_minutes = request.charged_time
            charged_time_delta = timedelta(minutes=charged_time_in_minutes)
            if charged_time_delta >= (request.requested_leave_time - request.arrival_time):
                continue
            required_power = (request.requested_energy - request.charged_energy) / ((request.requested_leave_time - request.arrival_time - charged_time_delta).total_seconds() / 3600)
            total_power_demand += required_power
        
        flexibility_demand = total_power_demand - self.power_supply
        return max(0.0, flexibility_demand)
    
    def flexibility_supply(self):
        total_flexibility_supply = 0.0
        for request in self.queued_requests:
            request: AvailableFlexibilityRequest
            power_flex = FlexibilityCalculator.calculate_power_flexibility(request, request.evse_id.nominal_power_cp)
            total_flexibility_supply += power_flex
        return max(0, total_flexibility_supply)

    def add_request(self, request: AvailableFlexibilityRequest):
        """Add a new request to the queue and initialize the power log list"""
        request.power_supplied_per_timestep = []  # Track power supplied at each time step
        self.queued_requests.append(request)
        
    def reject_new_request(self):
        """Reject new charging requests if flexibility demand exceeds supply"""
        if self.queued_requests:
            print(f'Rejecting new request due to insufficient flexibility supply: {self.queued_requests[-1].session_id}')
            self.queued_requests.pop()

    def allocate_flexibility_and_load_management(self):
        """Allocates power to each EV based on their charging demand, flexibility, and available power.
        Performs load management to ensure the total power usage does not exceed the power supply."""

        active_requests = [r for r in self.queued_requests if r.arrival_time <= self.current_time <= r.requested_leave_time]
        total_power_demand = 0.0
        for request in active_requests:
            charged_time_in_minutes = request.charged_time
            charged_time_delta = timedelta(minutes=charged_time_in_minutes)
            remaining_time = (request.requested_leave_time - request.arrival_time - charged_time_delta).total_seconds() / 3600
            if remaining_time > 0:
                requested_power = (request.requested_energy - request.charged_energy) / remaining_time
                total_power_demand += requested_power

        if total_power_demand <= self.power_supply:
            for request in active_requests:
                charged_time_in_minutes = request.charged_time
                charged_time_delta = timedelta(minutes=charged_time_in_minutes)
                remaining_time = (request.requested_leave_time - request.arrival_time - charged_time_delta).total_seconds() / 3600
                if remaining_time > 0:
                    requested_power = (request.requested_energy - request.charged_energy) / remaining_time
                    allocated_power = min(requested_power, request.evse_id.nominal_power_cp)
                    energy_charged = allocated_power * (self.time_step / 60)  # Energy charged in this time step
                    request.charged_energy += energy_charged
                    request.power_supplied_per_timestep.append(allocated_power)  # Log the power supplied
                    print(f"Allocated {allocated_power:.2f} kW to {request.session_id} (normal allocation)")

                    if request.charged_energy >= request.requested_energy:
                        print(f"{request.session_id} is fully charged with {request.charged_energy:.2f} kWh.")
        else:
            print("Power demand exceeds supply, applying flexibility and load management.")
            flexibility_supply = self.flexibility_supply()

            if flexibility_supply > 0:
                reduction_factor = (total_power_demand - self.power_supply) / flexibility_supply
            else:
                reduction_factor = 1.0

            total_allocated_power = 0.0
            for request in active_requests:
                remaining_time = (request.requested_leave_time - self.current_time).total_seconds() / 3600
                if remaining_time > 0:
                    requested_power = (request.requested_energy - request.charged_energy) / remaining_time
                    power_flex = FlexibilityCalculator.calculate_power_flexibility(request, request.evse_id.nominal_power_cp)
                    allocated_power = max(0, requested_power - (reduction_factor * power_flex))
                    if total_allocated_power + allocated_power > self.power_supply:
                        allocated_power = self.power_supply - total_allocated_power
                    
                    energy_charged = allocated_power * (self.time_step / 60)
                    request.charged_energy += energy_charged
                    request.power_supplied_per_timestep.append(allocated_power)  # Log the power supplied
                    total_allocated_power += allocated_power
                    print(f"Allocated {allocated_power:.2f} kW to {request.session_id} with flexibility applied")

    def update_for_next_timestep(self):
        """Updates the simulation time and logs results."""
        self.current_time += timedelta(minutes=self.time_step)
        for request in self.queued_requests:
            request.charged_time += self.time_step

        flex_demand = self.flexibility_demand()
        flex_supply = self.flexibility_supply()

        print(f"Time: {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Flexibility Demand: {flex_demand:.2f} kW")
        print(f"Flexibility Supply: {flex_supply:.2f} kW")
        print("-----")

    def run_simulation(self, requests: List[AvailableFlexibilityRequest]):
        """Runs the simulation and collects the power supplied at each time step"""
        for request in requests:
            self.add_request(request)
        
        while self.queued_requests:
            active_requests = [r for r in self.queued_requests if r.arrival_time <= self.current_time <= r.requested_leave_time]
            if not active_requests:
                print("No active charging requests. Simulation end.")
                break
            
            internal_flexibility_required = self.flexibility_demand() > 0
            external_flexibility_required = False  

            if internal_flexibility_required or external_flexibility_required:
                flexibility_demand = self.flexibility_demand()
                flexibility_supply = self.flexibility_supply()

                if flexibility_demand > flexibility_supply:
                    self.reject_new_request()
                    continue
                else:
                    self.allocate_flexibility_and_load_management()
            else:
                self.allocate_flexibility_and_load_management()

            self.update_for_next_timestep()

        # At the end of the simulation, plot the results
        self.plot_power_supplied()

    def plot_power_supplied(self):
        """Generates a graph showing power supplied at each time step for each EV"""
        plt.figure(figsize=(10, 6))
        for request in self.queued_requests:
            total_steps = len(request.power_supplied_per_timestep)
            plt.plot(range(total_steps), request.power_supplied_per_timestep, label=request.session_id)

        plt.xlabel('Time Step')
        plt.ylabel('Power Supplied (kW)')
        plt.title('Power Supplied to Each EV at Each Time Step')
        plt.legend()
        plt.grid(True)
        plt.show()

if __name__ == '__main__': 
    num_connectors = 4
    connectors = [ChargingPoint(i + 1) for i in range(num_connectors)]  
    connectors_in_use = []  
    power_supply = 40.0  
    time_step = 15  

    # Example simulation usage
    car1 = CarSpecs(make="Tesla", model="Model S", year=2022, battery_capacity_in_kwh=100, initial_soc=50 )
    request1 = AvailableFlexibilityRequest(
        session_id="user1",
        evse_id=connectors[0],
        requested_energy=11.0,
        requested_leave_time=datetime.now() + timedelta(hours=1.5),
        arrival_time=datetime.now(),
        car_specs=car1,
        charged_energy=0,
        charged_time=0
    )

    car2 = CarSpecs(make="Tesla", model="Model X", year=2022, battery_capacity_in_kwh=100, initial_soc=50)
    request2 = AvailableFlexibilityRequest(
        session_id="user2",
        evse_id=connectors[1],
        requested_energy=11.0,
        requested_leave_time=datetime.now() + timedelta(hours=1),
        arrival_time=datetime.now(),
        car_specs=car2,
        charged_energy=0,
        charged_time=0
    )
    
    car3 = CarSpecs(make="Tesla", model="Model Z", year=2022, battery_capacity_in_kwh=100, initial_soc=50)
    request3 = AvailableFlexibilityRequest(
        session_id="user3",
        evse_id=connectors[2],
        requested_energy=11.0,
        requested_leave_time=datetime.now() + timedelta(hours=1),
        arrival_time=datetime.now(),
        car_specs=car3,
        charged_energy=0,
        charged_time=0
    )
    
    car4 = CarSpecs(make="Tesla", model="Model A", year=2022, battery_capacity_in_kwh=100, initial_soc=50)
    request4 = AvailableFlexibilityRequest(
        session_id="user4",
        evse_id=connectors[3],
        requested_energy=11.0,
        requested_leave_time=datetime.now() + timedelta(hours=1),
        arrival_time=datetime.now(),
        car_specs=car4,
        charged_energy=0,
        charged_time=0
    )
    
    requests = [request1, request2, request3, request4]
    simulation = FlexibilitySimulation(power_supply, time_step, connectors, connectors_in_use)
    simulation.run_simulation(requests)
