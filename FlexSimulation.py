import matplotlib.pyplot as plt
from datetime import timedelta, datetime
from typing import List
from CarSpecs import CarSpecs
from FlexibilityRequest import AvailableFlexibilityRequest
from FlexibilityCalculator import FlexibilityCalculator
from ChargingPoint import ChargingPoint
import random
import math

class FlexibilitySimulation:
    def __init__(self, power_supply: float, time_step: int):
        self.power_supply = power_supply
        self.time_step = time_step
        self.queued_requests: List[AvailableFlexibilityRequest] = []
        self.pending_requests: List[AvailableFlexibilityRequest] = []  # Track requests that have not arrived yet
        self.completed_requests: List[AvailableFlexibilityRequest] = []  # Track requests that have been fully charged
        self.current_time = datetime.now()

    def flexibility_demand(self):       
        """Calculates total flexibility demand based on queued requests."""
        total_power_demand = 0.0
        for request in self.queued_requests:
            charged_time_in_minutes = request.charged_time
            charged_time_delta = timedelta(minutes=charged_time_in_minutes)
            if charged_time_delta >= (request.requested_leave_time - request.arrival_time) or request.requested_energy <= request.charged_energy: 
                continue
            remaining_time = (request.requested_leave_time - request.arrival_time - charged_time_delta).total_seconds() / 60
            if remaining_time <= 15: 
                required_power = min(request.evse_id.nominal_power_cp, (request.requested_energy - request.charged_energy) / ((request.requested_leave_time - request.arrival_time - charged_time_delta).total_seconds() / 3600))
            else:
                required_power = request.evse_id.nominal_power_cp
            total_power_demand += required_power
        flexibility_demand = total_power_demand - self.power_supply
        return max(0.0, flexibility_demand)

    def flexibility_supply(self):
        """Calculates total flexibility supply available from queued requests."""
        return sum(
            FlexibilityCalculator.calculate_power_flexibility(request, request.evse_id.nominal_power_cp)
            for request in self.queued_requests
        )
    
    def can_fulfill_requests(self,requests, power_supply):
        total_power_demand = 0.0
        total_flexible_energy = 0.0
        
        for request in requests:
            # Calculate required energy and power demand
            required_energy = request.requested_energy
            charging_time_hours = (request.requested_leave_time - request.arrival_time).total_seconds() / 3600
            power_demand = required_energy / charging_time_hours
            
            total_power_demand += power_demand
            
            # Calculate flexibility
            if charging_time_hours > 1:  # Assuming nominal power can be utilized for 1 hour
                flexible_time = charging_time_hours - 1
                flexible_power = flexible_time * request.evse_id.nominal_power_cp
                total_flexible_energy += flexible_power

        # Adjust available power
        available_energy = power_supply + total_flexible_energy
        
        # Compare total demand with available energy
        if available_energy >= total_power_demand:
            return True  # Requests can be fulfilled
        else:
            return False  # Requests cannot be fulfilled
    
    def add_request(self, request: AvailableFlexibilityRequest):
        """Adds a new charging request to the queue."""
        request.power_supplied_per_timestep = []
        self.queued_requests.append(request)
        print(f"Request {request.session_id} has been accepted.")
        

    def reject_new_request(self):
        """Rejects the latest charging request in the queue."""
        if self.queued_requests:
            print(f"Rejecting request due to insufficient flexibility: {self.queued_requests[-1].session_id}")
            print(f"It has been charged with : {self.queued_requests[-1].charged_energy} kW energy. However the requested energy was : {self.queued_requests[-1].requested_energy} kW")
            self.queued_requests.pop()

    def allocate_power(self, request: AvailableFlexibilityRequest, requested_power, allocated_power):
        """Allocates power to an EV and updates its charging status."""
        charged_time_delta = timedelta(minutes=request.charged_time)
        remaining_time = (request.requested_leave_time - request.arrival_time - charged_time_delta).total_seconds() / 3600
        if remaining_time > 0:
            potential_energy_charged = allocated_power * (self.time_step / 60)
            if request.charged_energy + potential_energy_charged > request.requested_energy:
                charging_complete_time = (request.requested_energy - request.charged_energy)/allocated_power
                potential_energy_charged = allocated_power * (charging_complete_time)
                request.charged_energy += potential_energy_charged
                request.power_supplied_per_timestep.append(allocated_power)
                print(f"Allocated {allocated_power:.2f} kW to {request.session_id}")
                if request.charged_energy >= request.requested_energy:
                    time_of_completion = self.current_time + timedelta(minutes=(charging_complete_time*60))
                    print(f"{request.session_id} is fully charged with {request.charged_energy:.2f} kWh. At time {time_of_completion.strftime('%Y-%m-%d %H:%M:%S')}")
                    # remove the request from the queue
                    self.queued_requests.remove(request)
                    self.completed_requests.append(request)
                return

            request.charged_energy += potential_energy_charged
            request.power_supplied_per_timestep.append(allocated_power)

            print(f"Allocated {allocated_power:.2f} kW to {request.session_id}")
            if request.charged_energy >= request.requested_energy:
                print(f"{request.session_id} is fully charged with {request.charged_energy:.2f} kWh.")
                self.queued_requests.remove(request)
                self.completed_requests.append(request)

    def allocate_flexibility_and_load_management(self):
        """Allocates power based on demand, flexibility, and available supply."""
        active_requests = [r for r in self.queued_requests if r.arrival_time <= self.current_time <= r.requested_leave_time]
        
        # total_power_demand = sum(
        #     (request.requested_energy - request.charged_energy) / ((request.requested_leave_time - self.current_time).total_seconds() / 3600)
        #     for request in active_requests if request.requested_leave_time > self.current_time
        # )
        
        # total_power_demand = sum(
        # request.evse_id.nominal_power_cp
        # for request in active_requests if request.requested_leave_time > self.current_time
        # )
        
        total_power_demand = 0.0
        instantaneous_power_demand = 0.0
        for request in active_requests:
            remaining_energy = request.requested_energy - request.charged_energy
            remaining_time = (request.requested_leave_time - self.current_time).total_seconds() / 3600
            
            if remaining_time > 0:
                # Calculate power required to charge fully within remaining time
                required_power = remaining_energy / remaining_time
                
                # Ensure the actual power demand is capped by the nominal power of the charging point
                actual_power_demand = min(request.evse_id.nominal_power_cp, required_power)
                total_power_demand += actual_power_demand
                
                # Instantaneous demand is the nominal power (not based on energy/time)
                instantaneous_power_demand += request.evse_id.nominal_power_cp
        
        
        if instantaneous_power_demand <= self.power_supply:
            for request in active_requests:
                self.allocate_power(request, request.evse_id.nominal_power_cp, request.evse_id.nominal_power_cp)
        else:
            print("Demand exceeds supply, applying flexibility.")
            flexibility_supply = self.flexibility_supply()
            allocation_factor = (total_power_demand - self.power_supply) / flexibility_supply if flexibility_supply > 0 else 1.0

            total_allocated_power = 0.0
            for request in active_requests:
                requested_power = (request.requested_energy - request.charged_energy) / ((request.requested_leave_time - self.current_time).total_seconds() / 3600)
                power_flex = FlexibilityCalculator.calculate_power_flexibility(request, request.evse_id.nominal_power_cp)
                allocated_power = max(0, requested_power - (allocation_factor * power_flex))
                allocated_power = min(allocated_power, self.power_supply - total_allocated_power,request.evse_id.nominal_power_cp)

                flexibility_contribution = request.evse_id.nominal_power_cp - allocated_power
                if flexibility_contribution > 0:
                    request.flexibility_contribution_per_timestep.append(flexibility_contribution*0.25)
                    request.flexibility_contribution = sum(request.flexibility_contribution_per_timestep)  
                     
                total_allocated_power += allocated_power
                self.allocate_power(request, requested_power, allocated_power)

    def update_for_next_timestep(self):
        """Moves the simulation to the next time step and logs progress."""
        self.current_time += timedelta(minutes=self.time_step)
        for request in self.queued_requests:
            request.charged_time += self.time_step
        print(f"Time: {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.update_power_supply()
        print("-----")
        
    def update_power_supply(self):
        random_power_supply = math.floor(random.uniform(30, 40))
        self.power_supply = random_power_supply
        print(f"Power Supply Updated to {self.power_supply} kW")

    def handle_new_requests(self):
        """Checks and adds any pending requests that have arrived."""
        arrived_requests = [r for r in self.pending_requests if r.arrival_time <= self.current_time]
        for request in arrived_requests:
            print(f"New request added to the queue: {request.session_id} at {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.add_request(request)
            self.pending_requests.remove(request)

    def run_simulation(self, requests: List[AvailableFlexibilityRequest]):
        """Runs the full simulation and logs charging progress."""
        self.pending_requests = requests[:]  # Initially all requests are pending

        while self.queued_requests or self.pending_requests:
            self.handle_new_requests()

            active_requests = [r for r in self.queued_requests if r.arrival_time <= self.current_time <= r.requested_leave_time]
            if not active_requests and not self.pending_requests:
                print("No active charging requests. Ending simulation.")
                break

            if self.flexibility_demand() > 0 or False:  # Placeholder for external flexibility check
                flexibility_demand = self.flexibility_demand()
                flexibility_supply = self.flexibility_supply()
                print("Flexibility Demand ", flexibility_demand)
                print("Flexibility Supply ", flexibility_supply)
                if flexibility_demand > flexibility_supply:
                    self.reject_new_request()
                    continue
                self.allocate_flexibility_and_load_management()
            else:
                self.allocate_flexibility_and_load_management()

            self.update_for_next_timestep()

        self.plot_power_supplied()
        self.plot_flexibility_contribution()



    def plot_power_supplied(self):
        """Generates a bar chart of power supplied to each EV per time step, starting from their respective arrival times."""
        plt.figure(figsize=(12, 6))

        # Use the initial simulation start time for reference
        simulation_start_time = min(req.arrival_time for req in self.completed_requests)

        bar_width = 0.2  # Set a smaller width for the bars to avoid overlap
        for idx, request in enumerate(self.completed_requests):
            total_steps = len(request.power_supplied_per_timestep)
            # Calculate the step at which the car arrived relative to the simulation start time
            arrival_time_step = (request.arrival_time - simulation_start_time).total_seconds() / (self.time_step * 60)
            
            # Adjust the steps to align with the car's arrival time
            time_steps = [arrival_time_step + step for step in range(total_steps)]
            
            # Introduce a small offset for each EV to prevent overlapping
            time_steps = [step + (idx * bar_width) for step in time_steps]
            
            plt.bar(time_steps, request.power_supplied_per_timestep, width=bar_width, label=request.session_id)

        plt.xlabel('Time Step')
        plt.ylabel('Power Supplied (kW)')
        plt.title('Power Supplied to Each EV at Each Time Step')
        plt.legend(title="EV Session IDs")
        plt.grid(True)
        plt.show()

    def plot_flexibility_contribution(self):
        """Generates a bar chart of flexibility contributions per EV at each time step, starting from their respective arrival times."""
        plt.figure(figsize=(12, 6))

        # Use the initial simulation start time for reference
        simulation_start_time = min(req.arrival_time for req in self.completed_requests)

        bar_width = 0.2  # Set a smaller width for the bars to avoid overlap
        for idx, request in enumerate(self.completed_requests):
            total_steps = len(request.flexibility_contribution_per_timestep)
            # Calculate the step at which the car arrived relative to the simulation start time
            arrival_time_step = (request.arrival_time - simulation_start_time).total_seconds() / (self.time_step * 60)
            
            # Adjust the steps to align with the car's arrival time
            time_steps = [arrival_time_step + step for step in range(total_steps)]
            
            # Introduce a small offset for each EV to prevent overlapping
            time_steps = [step + (idx * bar_width) for step in time_steps]
            
            plt.bar(time_steps, request.flexibility_contribution_per_timestep, width=bar_width, label=request.session_id)

        plt.xlabel('Time Step')
        plt.ylabel('Flexibility Contribution (kW)')
        plt.title('Flexibility Contributions (Energy Reduction) by Each EV at Each Time Step')
        plt.legend(title="EV Session IDs")
        plt.grid(True)
        plt.show()



if __name__ == '__main__':
    num_connectors = 4
    connectors = [ChargingPoint(i + 1) for i in range(num_connectors)]
    connectors_in_use = []
    power_supply = 33.0
    time_step = 15

    car1 = CarSpecs(make="Tesla", model="Model S", year=2022, battery_capacity_in_kwh=100, initial_soc=50)
    request1 = AvailableFlexibilityRequest("user1", connectors[0], 20.0, datetime.now() + timedelta(hours=3), datetime.now(), car1, 0, 0)

    car2 = CarSpecs(make="Tesla", model="Model X", year=2022, battery_capacity_in_kwh=100, initial_soc=50)
    request2 = AvailableFlexibilityRequest("user2", connectors[1], 11.0, datetime.now() + timedelta(hours=1),  datetime.now(), car2, 0, 0)

    car3 = CarSpecs(make="Tesla", model="Model Z", year=2022, battery_capacity_in_kwh=100, initial_soc=50)
    request3 = AvailableFlexibilityRequest("user3", connectors[2], 24.0, datetime.now() + timedelta(hours=4.25),  datetime.now()+timedelta(hours=0.25), car3, 0, 0)

    car4 = CarSpecs(make="Tesla", model="Model A", year=2022, battery_capacity_in_kwh=100, initial_soc=50)
    request4 = AvailableFlexibilityRequest("user4", connectors[3], 30.0, datetime.now() + timedelta(hours=3.5),  datetime.now()+timedelta(hours=0.5), car4, 0, 0)

    # car1 = CarSpecs(make="Tesla", model="Model S", year=2022, battery_capacity_in_kwh=100, initial_soc=50)
    # request1 = AvailableFlexibilityRequest("user1", connectors[0], 11.0, datetime.now() + timedelta(hours=1.5), datetime.now(), car1, 0, 0)

    # car2 = CarSpecs(make="Tesla", model="Model X", year=2022, battery_capacity_in_kwh=100, initial_soc=50)
    # request2 = AvailableFlexibilityRequest("user2", connectors[1], 11.0, datetime.now() + timedelta(hours=1),  datetime.now(), car2, 0, 0)

    # car3 = CarSpecs(make="Tesla", model="Model Z", year=2022, battery_capacity_in_kwh=100, initial_soc=50)
    # request3 = AvailableFlexibilityRequest("user3", connectors[2], 11.0, datetime.now() + timedelta(hours=1),  datetime.now(), car3, 0, 0)

    # car4 = CarSpecs(make="Tesla", model="Model A", year=2022, battery_capacity_in_kwh=100, initial_soc=50)
    # request4 = AvailableFlexibilityRequest("user4", connectors[3], 11.0, datetime.now() + timedelta(hours=1),  datetime.now(), car4, 0, 0)

    simulation = FlexibilitySimulation(power_supply, time_step)
    simulation.run_simulation([request1, request2, request3, request4])
    
    
    print("Flexibility Contribution Request 1 : ",request1.flexibility_contribution)
    print("Flexibility Contribution Request 2 : ",request2.flexibility_contribution)
    print("Flexibility Contribution Request 3 : ",request3.flexibility_contribution)
    print("Flexibility Contribution Request 4 : ",request4.flexibility_contribution)

