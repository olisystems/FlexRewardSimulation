from datetime import datetime
from typing import Optional
from CarSpecs import *
from ChargingPoint import *

class AvailableFlexibilityRequest:
    def __init__(
        self,
        session_id: str,
        evse_id: ChargingPoint,
        requested_energy: float,
        requested_leave_time: datetime,
        arrival_time: datetime,
        car_specs: CarSpecs,
        charged_energy: float,
        charged_time:float,
        
    ):
        self.__session_id = session_id
        self.__evse_id = evse_id
        self.__car_specs = car_specs
        self.__requested_energy = requested_energy
        self.__requested_leave_time = requested_leave_time
        self.__arrival_time = arrival_time
        self.__target_soc = car_specs.initial_soc + ((requested_energy / car_specs.battery_capacity_in_kwh)*100)
        self.__charged_energy = charged_energy
        self.__charged_time = charged_time
        self.__charge_complete = False
        self.__time_flexibility = 0
        self.__power_flexibility = 0
        self.__flexibility_contribution =0

        # Validation when object is created
        self.__validate_requested_energy()
        self.__validate_soc()
        self.__validate_leave_time_after_start_time()

        # Calculate target_soc based on provided logic
        self.__calculate_target_soc()

    # Read-only properties
    @property
    def session_id(self):
        return self.__session_id
    
    @property
    def charged_energy(self):
        return self.__charged_energy
    
    @property
    def charged_time(self):
        return self.__charged_time

    @property
    def evse_id(self):
        return self.__evse_id

    @property
    def requested_energy(self):
        return self.__requested_energy

    @property
    def requested_leave_time(self):
        return self.__requested_leave_time

    @property
    def arrival_time(self):
        return self.__arrival_time

        
    @property
    def charge_complete(self):
        return self.__charge_complete
    
    @property
    def time_flexibility(self):
        return self.__time_flexibility
    
    @property
    def power_flexibility(self):
        return self.__power_flexibility
    
    @property
    def flex_contribution(self):
        return self.__flexibility_contribution
    
    # create a setter for charged_time
    @charged_time.setter
    def charged_time(self, charged_time):
        self.__charged_time = charged_time

    @property
    def target_soc(self):
        return self.__target_soc

    @property
    def car_specs(self):
        return self.__car_specs

    # setter for charged_energy
    @charged_energy.setter
    def charged_energy(self, charged_energy):
        self.__charged_energy = charged_energy
    # Validation for requested energy
    def __validate_requested_energy(self):
        if self.__requested_energy <= 0:
            raise ValueError("Requested energy must be greater than 0.")

    # Validation for state of charge (current_soc)
    def __validate_soc(self):
        if not (0 <= self.car_specs.initial_soc <= 100):
            raise ValueError("State of charge (SoC) must be between 0 and 100%.")

    # Validation to ensure requested leave time is in the future and after the charging start time
    def __validate_leave_time_after_start_time(self):
        if not self.__requested_leave_time > self.__arrival_time:
            raise ValueError("Requested leave time must be after charging start time.")
        if not self.__requested_leave_time > datetime.now():
            raise ValueError("Requested leave time must be in the future.")

    # Calculation of target_soc based on given logic
    def __calculate_target_soc(self):
        battery_capacity_in_kwh = self.__car_specs.battery_capacity_in_kwh
        self.__target_soc = min(100.0, self.car_specs.initial_soc + ((self.__requested_energy / battery_capacity_in_kwh)*100))

    def __repr__(self) -> str:
        return (f"FlexibilityRequest(session_id='{self.session_id}', "
                f"evse_id='{self.evse_id}', requested_energy='{self.requested_energy}', "
                f"requested_leave_time='{self.requested_leave_time}', "
                f"charging_start_time='{self.arrival_time}', "
                f"initial_soc='{self.car_specs.initial_soc}', target_soc='{self.target_soc}', "
                f"car_specs='{self.car_specs}')")
