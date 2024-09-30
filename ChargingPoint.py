class ChargingPoint:
  def __init__(self, id):
    self.id = id
    self.available = True
    self.current_request = None

  def assign_request(self, request):
    self.current_request = request

  def finish_charging(self):
    self.current_request = None
  
  def setAvailable(self,val):
    self.available = val

  def isAvailable(self):
    return self.available