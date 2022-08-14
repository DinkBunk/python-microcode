import string
from relay_state import RelayState

class RGSettings:
    relayState: string
    analog59: float
    analog60: float
    analog61: float
    analog62: float
    analog63: float
    analog64: float

    def __init__(self, relayState, analog59, analog60, analog61, analog62, analog63, analog64):
        self.relayState, self.analog59, self.analog60, self.analog61, self.analog62, self.analog63, self.analog64 = relayState, analog59, analog60, analog61, analog62, analog63, analog64
        
    

    
    
