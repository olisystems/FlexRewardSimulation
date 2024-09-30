class CarSpecs:
    # constructor
    def __init__(self, make: str, model: str, year: int, battery_capacity_in_kwh: float):
        self.__make = make
        self.__model = model
        self.__year = year
        self.__battery_capacity_in_kwh = battery_capacity_in_kwh

    # Read-only properties
    @property
    def make(self):
        return self.__make

    @property
    def model(self):
        return self.__model

    @property
    def year(self):
        return self.__year

    @property
    def battery_capacity_in_kwh(self):
        return self.__battery_capacity_in_kwh
    
    def __repr__(self):
        return (f"CarSpecs(make='{self.make}', model='{self.model}', "
                f"year={self.year}, battery_capacity_in_kwh={self.battery_capacity_in_kwh})")


