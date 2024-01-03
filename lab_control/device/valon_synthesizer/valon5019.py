import pyvisa
from functools import lru_cache 

class Synth:
    def __init__(self, device_name):
        self.device_name = device_name
        self.rm = pyvisa.ResourceManager()
        rmlist = self.rm.list_resources()
        if self.device_name not in rmlist:
            raise ValueError(
                f'Could not find valon synthesizer {device_name};\nAvailable devices are {rmlist}.'
            )
        # stops uploading if the frequency does not change 
        self.set_freq = lru_cache(maxsize=1)(self.set_freq)
        self.set_power = lru_cache(maxsize=1)(self.set_power)
        
    def set_freq(self, freq):
        self.synth = self.rm.open_resource(self.device_name)
        # set frequency in MHz
        self.synth.write('cw ' + str(freq) + ' mhz')
        self.synth.close()
    
    def get_freq(self):
        self.synth = self.rm.open_resource(self.device_name)
        # for some reason, we can read one line at a time
        self.synth.query('FREQ')
        print(self.synth.read())
        self.synth.close()

    def set_power(self, new_power):
        """ Set power level; currently the level is +1dBm """ 
        if new_power > 8 or new_power < -30:
            raise ValueError("New power must be within +1dBm and -30dBm")
        self.synth = self.rm.open_resource(self.device_name)
        # set power in dBm 
        self.synth.write(f'PWR {new_power}')
        self.synth.close()

    def get_power(self):
        self.synth = self.rm.open_resource(self.device_name)
        # for some reason, we can read one line at a time
        self.synth.query('PWR')
        print(self.synth.read())
        self.synth.close()
        
if __name__ == '__main__':
    s = Synth('ASRL9::INSTR')
    while True:
        freq = input('Input frequency in MHz:\n')
        s.set_freq(freq)
        s.get_freq()
        power = float(input('Input power in dBm:\n'))
        s.set_power(power)
        s.get_power()
    