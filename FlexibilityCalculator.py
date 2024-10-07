# import random
# from datetime import datetime
# from FlexUtils import FlexibilityUtils
# from datetime import datetime, timedelta

# class FlexibilityCalculator:
    
#     def calculate_flexible_shifted_kwh(self,
#             available_flexibility_request,
#             car_load_curve,
#             latest_start_time: datetime
#         ) -> float:

#         flexible_shifted_kwh = 0.0
#         current_time = available_flexibility_request['charging_start_time']
#         current_soc_percentage = available_flexibility_request['current_soc']
#         remaining_energy = available_flexibility_request['requested_energy']

#         while current_time < latest_start_time:
#             # Determine the start and end of the current interval (15 minutes in this case)
#             interval_start = current_time
#             next_quarter_hour = (interval_start + timedelta(minutes=15)).replace(second=0, microsecond=0)
#             interval_end = min(next_quarter_hour, latest_start_time)

#             # Calculate the duration of the charging interval in hours
#             interval_duration = (interval_end - interval_start).total_seconds() / 3600.0

#             # Calculate the maximum available charging power based on current SOC and car load curve
#             max_power = self.get_max_power_for_soc(car_load_curve, current_soc_percentage)

#             # Assuming a static power limit for each interval (can be replaced with a more dynamic calculation if needed)
#             available_power = min(max_power, 50.0)  # Example static power limit of 50 kW

#             # Calculate the energy that can be charged in this interval
#             interval_energy = available_power * interval_duration

#             # Ensure energy does not exceed the remaining energy needed
#             if interval_energy > remaining_energy:
#                 interval_energy = remaining_energy

#             flexible_shifted_kwh += interval_energy
#             remaining_energy -= interval_energy

#             if remaining_energy <= 0:
#                 break

#             # Update SOC based on the interval energy
#             current_soc_percentage = self.update_soc(current_soc_percentage, interval_energy, car_load_curve['battery_capacity_kwh'])

#             # Move to the end of the current interval
#             current_time = interval_end

#         return flexible_shifted_kwh


#     def get_max_power_for_soc(car_load_curve, soc_percentage):
#         """
#         Returns the maximum available power based on the state of charge (SOC)
#         and the car's load curve. The car_load_curve is an array of 10 floats
#         representing the power limits for each SOC range (0%-10%, 10%-20%, etc.).
        
#         :param car_load_curve: List[float] - array of power limits for different SOC ranges
#         :param soc_percentage: float - current state of charge (0% - 100%)
#         :return: float - the max power available for the given SOC
#         """
        
#         if soc_percentage < 0 or soc_percentage > 100:
#             raise ValueError("SOC percentage must be between 0 and 100")
        
#         # Determine the index for the car_load_curve based on SOC percentage
#         index = int(soc_percentage // 10)  # Integer division to map SOC to the curve (0-9)

#         # Handle edge case for 100% SOC, which should correspond to the last index (9)
#         if index == 10:
#             index = 9

#         # Return the max power from the car load curve for the given SOC range
#         return car_load_curve[index]



#     def update_soc(self,current_soc, interval_energy, battery_capacity_kwh):
#         # Logic to update the state of charge (SOC)
#         return current_soc + (interval_energy / battery_capacity_kwh) * 100

from FlexibilityRequest import AvailableFlexibilityRequest

class FlexibilityCalculator:
    @staticmethod
    def calculate_time_flexibility(charging_request:AvailableFlexibilityRequest, nominal_power_cp):
        """
        Calculate time flexibility for a given charging request.
        
        :param charging_request: AvailableFlexibilityRequest
        :return: float - time flexibility in minutes
        """
        # Calculate the time flexibility as the difference between anticipated charging time
        # and the minimum required charging time
        charging_duration = (charging_request.requested_leave_time - charging_request.charging_start_time).total_seconds() / 60  # in minutes
        required_charging_time = (charging_request.requested_energy /nominal_power_cp) * 60  # in minutes

        flexibility = charging_duration - required_charging_time
        return flexibility

    @staticmethod
    def calculate_power_flexibility(charging_request,nominal_power_cp):
        """
        Calculate power flexibility for a given charging request.
        
        :param charging_request: AvailableFlexibilityRequest
        :return: float - power flexibility in kW
        """
        time_flexibility = FlexibilityCalculator.calculate_time_flexibility(charging_request,nominal_power_cp)
        
        if time_flexibility >= 15:  # If there's enough time flexibility
            return nominal_power_cp  # Full power flexibility
        else:
            # Scale the power flexibility based on available time flexibility
            power_flexibility = (time_flexibility / 15) * nominal_power_cp
            return power_flexibility
