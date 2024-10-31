from datetime import timedelta, datetime
from typing import List
from CarSpecs import CarSpecs
from FlexibilityRequest import AvailableFlexibilityRequest
from FlexibilityCalculator import FlexibilityCalculator
from ChargingPoint import ChargingPoint
import random
import math
import pandas as pd
from FlexUtils import generate_random_car, generate_random_request, generate_random_requests
from PlottingUtils import PlottingUtils 
import copy

class FlexibilitySimulation:
    def __init__(self, power_supply: float, time_step: int):
        """Initialize the FlexibilitySimulation instance.

        Args:
            power_supply (float): The total available power supply for the simulation.
            time_step (int): The time interval (in minutes) for the simulation steps.
        """
        self.power_supply = power_supply  # Total power supply available for allocation.
        self.time_step = time_step  # Duration of each simulation step in minutes.
        self.queued_requests: List[AvailableFlexibilityRequest] = []  # List of requests that are queued for charging.
        self.pending_requests: List[AvailableFlexibilityRequest] = []  # Requests that have not yet arrived.
        self.completed_requests: List[AvailableFlexibilityRequest] = []  # Requests that have been fully charged.
        self.current_time = datetime.now()  # Set the simulation's current time to now.
        self.start_time = datetime.now()  # Record the start time of the simulation.
        self.rejected_requests = []  # List to track rejected requests.
        



    def flexibility_demand(self):       
        """Calculates total flexibility demand based on queued requests.

        Returns:
            float: The total flexibility demand, which is the amount of power required beyond the available supply.
        """
        total_power_demand = 0.0  # Initialize total power demand to zero.
        for request in self.queued_requests:  # Loop through all queued requests.
            charged_time_in_minutes = request.charged_time  # Get the time already charged.
            charged_time_delta = timedelta(minutes=charged_time_in_minutes) # Convert to timedelta.
            # Check if the request is fully charged or if the requested leave time is exceeded.
            if charged_time_delta >= (request.requested_leave_time - request.arrival_time) or request.requested_energy <= request.charged_energy: 
                continue # Skip this request if it's fully charged or the leave time is exceeded.
            # Calculate the remaining time for charging.
            remaining_time = (request.requested_leave_time - request.arrival_time - charged_time_delta).total_seconds() / 60
            if remaining_time <= 15: # If less than or equal to 15 minutes left,
                # Calculate required power to meet the requested energy within the remaining time.
                required_power = min(request.evse_id.nominal_power_cp, (request.requested_energy - request.charged_energy) / ((request.requested_leave_time - request.arrival_time - charged_time_delta).total_seconds() / 3600))
            else:
                required_power = request.evse_id.nominal_power_cp # Use nominal power if enough time is available.
            total_power_demand += required_power # Accumulate total power demand.
        # Return the flexibility demand as the difference between total demand and available power supply.
        flexibility_demand = total_power_demand - self.power_supply
        return max(0.0, flexibility_demand) # Ensure non-negative demand.
    
    
    
    

    def flexibility_supply(self):
        """Calculates total flexibility supply available from queued requests.

        Returns:
            float: Total available flexibility supply.
        """      
        # Calculate the total flexibility supply from all queued requests using the FlexibilityCalculator.
        return sum(
            FlexibilityCalculator.calculate_power_flexibility(request, request.evse_id.nominal_power_cp)
            for request in self.queued_requests
        )
        
        
        
        
    
    def add_request(self, request: AvailableFlexibilityRequest):
        """Adds a new charging request to the queue.

        Args:
            request (AvailableFlexibilityRequest): The charging request to be added.
        """
        request.power_supplied_per_timestep = [] # Initialize the list to track power supplied over time.
        self.queued_requests.append(request)  # Add the request to the queue.
        print(f"Request {request.session_id} has been accepted.")
        
        
        
        
        

    def reject_new_request(self):
        """Rejects the latest charging request in the queue due to insufficient flexibility."""
        if self.queued_requests:  # Check if there are any queued requests.
            # Log the rejection and details of the request.
            print(f"Rejecting request due to insufficient flexibility: {self.queued_requests[-1].session_id}")
            print(f"It has been charged with: {self.queued_requests[-1].charged_energy} kW energy. However the requested energy was: {self.queued_requests[-1].requested_energy} kW")
            req = self.queued_requests.pop()  # Remove the last request from the queue.
            self.rejected_requests.append(req)  # Add it to the list of rejected requests.
            
            
            
            
            

    def allocate_power(self, request: AvailableFlexibilityRequest, requested_power, allocated_power):
        """Allocates power to an EV and updates its charging status.

        Args:
            request (AvailableFlexibilityRequest): The charging request to allocate power to.
            requested_power (float): The power requested by the EV.
            allocated_power (float): The power allocated to the EV.
        """
        charged_time_delta = timedelta(minutes=request.charged_time)  # Get the charged time as timedelta.
        remaining_time = (request.requested_leave_time - request.arrival_time - charged_time_delta).total_seconds() / 3600  # Calculate remaining time until leave.
        if remaining_time > 0:  # If there is still time left for charging,
            potential_energy_charged = allocated_power * (self.time_step / 60)  # Calculate potential energy charged in the current time step.
            # Check if charging will exceed requested energy.
            if request.charged_energy + potential_energy_charged > request.requested_energy:
                charging_complete_time = (request.requested_energy - request.charged_energy) / allocated_power  # Calculate time to fully charge.
                potential_energy_charged = allocated_power * (charging_complete_time)  # Adjust to the energy needed to fully charge.
                request.charged_energy += potential_energy_charged  # Update charged energy.
                request.power_supplied_per_timestep.append(allocated_power)  # Record the power supplied in this timestep.
                print(f"Allocated {allocated_power:.2f} kW to {request.session_id}")  # Log the allocation.
                # Check if the request is fully charged.
                if request.charged_energy >= request.requested_energy:
                    time_of_completion = self.current_time + timedelta(minutes=(charging_complete_time * 60))  # Calculate completion time.
                    print(f"{request.session_id} is fully charged with {request.charged_energy:.2f} kWh. At time {time_of_completion.strftime('%Y-%m-%d %H:%M:%S')}")  # Log completion.
                    # Mark the request as complete and remove it from the queue.
                    request.charge_complete = True
                    self.queued_requests.remove(request)
                    self.completed_requests.append(request)  # Add to completed requests.
                return  # Exit function since power allocation is complete.

            request.charged_energy += potential_energy_charged  # Update charged energy with potential energy.
            request.power_supplied_per_timestep.append(allocated_power)  # Record the power supplied.

            print(f"Allocated {allocated_power:.2f} kW to {request.session_id}")  # Log the allocation.
            # Check if the request is fully charged after this allocation.
            if request.charged_energy >= request.requested_energy:
                print(f"{request.session_id} is fully charged with {request.charged_energy:.2f} kWh.")  # Log completion.
                self.queued_requests.remove(request)  # Remove from the queue.
                request.charge_complete = True  # Mark as complete.
                self.completed_requests.append(request)  # Add to completed requests.






    def allocate_flexibility_and_load_management(self):
        """Allocates power based on demand, flexibility, and available supply."""
        active_requests = [r for r in self.queued_requests if r.arrival_time <= self.current_time <= r.requested_leave_time]  # Filter active requests based on current time.
        
        total_power_demand = 0.0  # Initialize total power demand.
        instantaneous_power_demand = 0.0  # Initialize instantaneous power demand.
        for request in active_requests:  # Loop through active requests.
            remaining_energy = request.requested_energy - request.charged_energy  # Calculate remaining energy needed.
            remaining_time = (request.requested_leave_time - self.current_time).total_seconds() / 3600  # Calculate remaining time until leave.
            
            if remaining_time > 0:  # If there is still time left for charging,
                # Calculate required power to charge fully within remaining time.
                required_power = remaining_energy / remaining_time
                
                # Ensure the actual power demand is capped by the nominal power of the charging point.
                actual_power_demand = min(request.evse_id.nominal_power_cp, required_power)
                total_power_demand += actual_power_demand  # Accumulate total power demand.
                
                # Instantaneous demand is the nominal power (not based on energy/time).
                instantaneous_power_demand += request.evse_id.nominal_power_cp
        
        # Check if the total instantaneous power demand is within the available power supply.
        if instantaneous_power_demand <= self.power_supply:
            # If so, allocate the nominal power to all requests.
            for request in active_requests:
                self.allocate_power(request, request.evse_id.nominal_power_cp, request.evse_id.nominal_power_cp)
        else:
            print("Demand exceeds supply, applying flexibility.")  # Log that demand exceeds supply.
            flexibility_supply = self.flexibility_supply()  # Get total flexibility supply.
            # Calculate allocation factor to adjust power allocation based on flexibility.
            allocation_factor = (total_power_demand - self.power_supply) / flexibility_supply if flexibility_supply > 0 else 1.0

            total_allocated_power = 0.0  # Initialize total allocated power.
            for request in active_requests:  # Loop through active requests.
                # Calculate requested power based on remaining energy and time.
                requested_power = (request.requested_energy - request.charged_energy) / ((request.requested_leave_time - self.current_time).total_seconds() / 3600)
                power_flex = FlexibilityCalculator.calculate_power_flexibility(request, request.evse_id.nominal_power_cp)  # Calculate flexibility contribution.
                # Determine the allocated power, ensuring it's non-negative and does not exceed supply.
                allocated_power = max(0, requested_power - (allocation_factor * power_flex))
                allocated_power = min(allocated_power, self.power_supply - total_allocated_power, request.evse_id.nominal_power_cp)

                # Calculate the flexibility contribution based on the allocated power.
                flexibility_contribution = request.evse_id.nominal_power_cp - allocated_power
                if flexibility_contribution > 0:  # If there is a contribution,
                    request.flexibility_contribution_per_timestep.append(flexibility_contribution * 0.25)  # Log the contribution for the timestep.
                    request.flexibility_contribution = sum(request.flexibility_contribution_per_timestep)  # Update total flexibility contribution.

                total_allocated_power += allocated_power  # Update total allocated power.
                self.allocate_power(request, requested_power, allocated_power)  # Allocate power to the request.




    def update_for_next_timestep(self):
        """Moves the simulation to the next time step and logs progress."""
        self.current_time += timedelta(minutes=self.time_step)  # Advance the current time by the timestep.
        for request in self.queued_requests:  # Update the charged time for all queued requests.
            request.charged_time += self.time_step
        print(f"Time: {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}")  # Log the current time.
        # Print current time step.
        current_time_step = (self.current_time - self.start_time) / timedelta(minutes=15)
        print(f"Current Time Step: {current_time_step}")  # Log the current timestep.
        print("-----")  # Separator for clarity.
        self.update_power_supply()  # Update the power supply for the next timestep. Uncomment this line to enable random power supply updates.




    def update_power_supply(self):
        """Updates the power supply to a random value within a specified range."""
        random_power_supply = math.floor(random.uniform(30, 40))  # Generate a random power supply value.
        self.power_supply = random_power_supply  # Update the power supply.
        print(f"Power Supply Updated to {self.power_supply} kW")  # Log the updated supply.





    def handle_new_requests(self):
        """Checks and adds any pending requests that have arrived."""
        arrived_requests = [r for r in self.pending_requests if r.arrival_time <= self.current_time]  # Filter requests that have arrived.
        for request in arrived_requests:  # Loop through all arrived requests.
            print(f"New request added to the queue: {request.session_id} at {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}")  # Log the addition.
            self.add_request(request)  # Add the request to the queue.
            self.pending_requests.remove(request)  # Remove it from the pending list.
            
            
            
            
    def flex_contributions(self):
        """Logs the flexibility contributions of all completed requests."""
        for request in self.completed_requests:  # Loop through completed requests.
            print(f"Flexibility contribution of {request.session_id}: {request.flexibility_contribution:.2f} kW")  # Log flexibility contributions.




    def run_simulation(self, requests: List[AvailableFlexibilityRequest]):
        """Runs the full simulation and logs charging progress.

        Args:
            requests (List[AvailableFlexibilityRequest]): List of charging requests to simulate.
        """
        self.pending_requests = requests[:]  # Initially, all requests are pending.

        while self.queued_requests or self.pending_requests:  # Continue until all requests are processed.
            self.handle_new_requests()  # Check and add new requests.

            active_requests = [r for r in self.queued_requests if r.arrival_time <= self.current_time <= r.requested_leave_time]  # Filter active requests based on current time.
            if not active_requests and not self.pending_requests:  # If no active requests are present,
                print("No active charging requests. Ending simulation.")  # Log end of simulation.
                break  # Exit the loop.

            if self.flexibility_demand() > 0 or False:  # Placeholder for external flexibility check.
                flexibility_demand = self.flexibility_demand()  # Get the current flexibility demand.
                flexibility_supply = self.flexibility_supply()  # Get the current flexibility supply.
                print("Flexibility Demand ", flexibility_demand)  # Log the flexibility demand.
                print("Flexibility Supply ", flexibility_supply)  # Log the flexibility supply.
                if flexibility_demand > flexibility_supply:  # If demand exceeds supply,
                    self.reject_new_request()  # Reject the latest request.
                    continue  # Skip to the next iteration.
                self.allocate_flexibility_and_load_management()  # Allocate power based on flexibility.
            else:
                self.allocate_flexibility_and_load_management()  # Allocate power based on current state.

            self.update_for_next_timestep()  # Move to the next timestep.
        self.flex_contributions()  # Log flexibility contributions of completed requests.





if __name__ == '__main__':
    num_connectors = 5
    connectors = [ChargingPoint(i + 1) for i in range(num_connectors)]
    connectors_in_use = []
    power_supply = 40.0
    time_step = 15

    car1 = CarSpecs(make="Tesla", model="Model S", year=2022, battery_capacity_in_kwh=100, initial_soc=50)
    request1 = AvailableFlexibilityRequest("user1", connectors[0], 11.0,90, datetime.now(), car1, 0, 0)

    car2 = CarSpecs(make="Tesla", model="Model X", year=2022, battery_capacity_in_kwh=100, initial_soc=50)
    request2 = AvailableFlexibilityRequest("user2", connectors[1], 11.0, 60,  datetime.now(), car2, 0, 0)

    car3 = CarSpecs(make="Tesla", model="Model Z", year=2022, battery_capacity_in_kwh=100, initial_soc=50)
    request3 = AvailableFlexibilityRequest("user3", connectors[2], 11.0, 60,  datetime.now(), car3, 0, 0)

    car4 = CarSpecs(make="Tesla", model="Model A", year=2022, battery_capacity_in_kwh=100, initial_soc=50)
    request4 = AvailableFlexibilityRequest("user4", connectors[3], 11.0, 60,  datetime.now(), car4, 0, 0)
    
    simulation = FlexibilitySimulation(power_supply, time_step)
    requests = [request1, request2, request3, request4]
    # create a copy of the requests
    copy_requests = copy.deepcopy(requests)

    simulation.run_simulation(copy_requests)
        

    PlottingUtils.plot_power_supplied(simulation.completed_requests)
    PlottingUtils.plot_flexibility_contribution(simulation.completed_requests)
    


# Uncomment the following code to run the simulation with random requests generated by the FlexUtils module dynamically.
# if __name__ == '__main__':
#     num_connectors = 4
#     connectors = [ChargingPoint(i + 1) for i in range(num_connectors)]
#     power_supply = 40.0
#     time_step = 15
#     num_requests = 5  # Specify the number of random requests to generate

#     # Generate random charging requests
#     requests = generate_random_requests(num_requests, connectors)

#     # Run the simulation
#     simulation = FlexibilitySimulation(power_supply, time_step)
#     simulation.run_simulation(requests)



