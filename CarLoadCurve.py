
class CarLoadCurve:
    def __init__(self, car_specs, supported_power_for_every_ten_percent=None):
        # Initialize the fields
        self.car_specs = car_specs  # CarSpecs object (can be a dictionary or class in Python)
        self.supported_power_for_every_ten_percent = supported_power_for_every_ten_percent if supported_power_for_every_ten_percent else [0] * 10  # Array of float (10 values)

    def to_dict(self):
        # Convert the object to a dictionary (useful for inserting into MongoDB)
        return {
            "_id": self.car_specs,  # Treating car_specs as ID like in Java
            "supported_power_for_every_ten_percent": self.supported_power_for_every_ten_percent
        }

    @classmethod
    def from_dict(cls, data):
        # Create a CarLoadCurve object from a dictionary (useful for fetching from MongoDB)
        return cls(
            car_specs=data["_id"], 
            supported_power_for_every_ten_percent=data.get("supported_power_for_every_ten_percent", [0] * 10)
        )
