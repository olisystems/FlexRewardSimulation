class ChargingPoint:
  def __init__(self, id):
    self.id = id
    self.available = True
    self.current_request = None

  def assign_request(self, request):
    self.current_request = request
    self.available = False

  def finish_charging(self):
    self.current_request = None
    self.available = True
    
  def isAvailable(self):
    print(self.id, " is Available")
    return self.available