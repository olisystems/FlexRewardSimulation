import matplotlib.pyplot as plt

class PlottingUtils:
    

    @staticmethod
    def plot_power_supplied( completed_requests):
        """Generates a bar chart of power supplied to each EV per time step, starting from their respective arrival times."""
        plt.figure(figsize=(12, 6))

        # Use the initial simulation start time for reference
        simulation_start_time = min(req.arrival_time for req in completed_requests)

        bar_width = 0.2  # Set a smaller width for the bars to avoid overlap
        for idx, request in enumerate(completed_requests):
            total_steps = len(request.power_supplied_per_timestep)
            # Calculate the step at which the car arrived relative to the simulation start time
            arrival_time_step = (request.arrival_time - simulation_start_time).total_seconds() / (15 * 60)
            
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

    @staticmethod
    def plot_flexibility_contribution( completed_requests):
        """Generates a bar chart of flexibility contributions per EV at each time step, starting from their respective arrival times."""
        plt.figure(figsize=(12, 6))

        # Use the initial simulation start time for reference
        simulation_start_time = min(req.arrival_time for req in completed_requests)

        bar_width = 0.2  # Set a smaller width for the bars to avoid overlap
        for idx, request in enumerate(completed_requests):
            total_steps = len(request.flexibility_contribution_per_timestep)
            # Calculate the step at which the car arrived relative to the simulation start time
            arrival_time_step = (request.arrival_time - simulation_start_time).total_seconds() / (15 * 60)
            
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