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
