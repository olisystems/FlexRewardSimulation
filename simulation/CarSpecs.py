class CarSpecs:
    # constructor
    def __init__(self, make: str, model: str, year: int, battery_capacity_in_kwh: float, initial_soc:float):
        self.__make = make
        self.__model = model
        self.__year = year
        self.__battery_capacity_in_kwh = battery_capacity_in_kwh
        self.__initial_soc = initial_soc
        self.__soc = initial_soc

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
    
    @property
    def initial_soc(self):
        return self.__initial_soc
    
    @property
    def soc(self):
        return self.__soc
    
    def __repr__(self):
        return (f"CarSpecs(make='{self.make}', model='{self.model}', "
                f"year={self.year}, battery_capacity_in_kwh={self.battery_capacity_in_kwh})")


