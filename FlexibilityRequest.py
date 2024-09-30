from datetime import datetime
from typing import Optional
from CarSpecs import *


class AvailableFlexibilityRequest:
    def __init__(
        self,
        session_id: str,
        evse_id: str,
        requested_energy: float,
        requested_leave_time: datetime,
        charging_start_time: datetime,
        current_soc: float,
        car_specs: CarSpecs,
    ):
        self.__session_id = session_id
        self.__evse_id = evse_id
        self.__requested_energy = requested_energy
        self.__requested_leave_time = requested_leave_time
        self.__charging_start_time = charging_start_time
        self.__current_soc = current_soc
        self.__car_specs = car_specs

        # Validation when object is created
        self.__validate_requested_energy()
        self.__validate_soc()
        self.__validate_leave_time_after_start_time()

    # Read-only properties
    @property
    def session_id(self):
        return self.__session_id

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
    def charging_start_time(self):
        return self.__charging_start_time

    @property
    def current_soc(self):
        return self.__current_soc
    
    @current_soc.setter
    def current_soc(self, value: float):
        if not (0 <= value <= 100):
            raise ValueError("State of charge (SoC) must be between 0 and 100%.")
        self.__current_soc = value

    @property
    def car_specs(self):
        return self.__car_specs

    # Validation for requested energy
    def __validate_requested_energy(self):
        if self.__requested_energy <= 0:
            raise ValueError("Requested energy must be greater than 0.")

    # Validation for state of charge (current_soc)
    def __validate_soc(self):
        if not (0 <= self.__current_soc <= 100):
            raise ValueError("State of charge (SoC) must be between 0 and 100%.")

    # Validation to ensure requested leave time is in the future and after the charging start time
    def __validate_leave_time_after_start_time(self):
        if not self.__requested_leave_time > self.__charging_start_time:
            raise ValueError("Requested leave time must be after charging start time.")
        if not self.__requested_leave_time > datetime.now():
            raise ValueError("Requested leave time must be in the future.")

    def __repr__(self) -> str:
        return f"FlexibilityRequest(session_id='{self.session_id}', evse_id='{self.evse_id}', requested_energy='{self.requested_energy}, requested_leave_time='{self.requested_leave_time}', charging_start_time='{self.charging_start_time}',current_soc='{self.current_soc}',  car_specs='{self.car_specs}')"

