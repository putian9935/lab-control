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
        self.set_mode = lru_cache(maxsize=1)(self.set_mode)
        
    def set_mode(self, mod_str):
        """ 
        - mod_str: "cw" | "list" 
        """
        self.synth = self.rm.open_resource(self.device_name)
        self.synth.write(f'MOD {mod_str}')
        self.synth.close()
    
    def set_freq(self, freq):
        self.set_mode('cw')
        self.synth = self.rm.open_resource(self.device_name)
        # set frequency in MHz
        print('???', freq)
        self.synth.write('cw ' + str(freq) + ' mhz')
        self.synth.close()
        self.get_freq()
    
        self.synth = self.rm.open_resource(self.device_name)
        self.synth.query('mod?')
        print(self.synth.read())
        self.synth.close()

    def set_freq2(self, freq1, freq2):
        """ Set two frequencies, controlled by TTL 
        
        Freq 1: when TTL is low 
        Freq 2: when TTL is high  
        """
        self.set_mode('list')
        self.synth = self.rm.open_resource(self.device_name)
        print(freq1, freq2)
        self.synth.write(f'list 31 {freq1} mhz')
        # print(self.synth.read())
        self.synth.write(f'list 32 {freq2} mhz')
        # print(self.synth.read())
        # self.synth.query('List?')
        # for i in range(32):
        #     print(self.synth.read())
        # self.synth.close()
        # self.synth = self.rm.open_resource(self.device_name)
            
        # self.synth.query('mod?')
        # print(self.synth.read())
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
    
    def set_list(self, index, freq):
        self.synth = self.rm.open_resource(self.device_name)
        self.synth.query('')
        self.synth.close()
        
if __name__ == '__main__':
    s = Synth('ASRL16::INSTR')
    # s.set_freq2(1000, 2000)
    # while True:
    #     freq = input('Input frequency in MHz:\n')
    #     s.set_freq(freq)
    #     s.get_freq()
    #     power = float(input('Input power in dBm:\n'))
    #     s.set_power(power)
    #     s.get_power()

    synth = s.rm.open_resource(s.device_name)
    # # for i in range(30, 33):
    # #     f = 1000 + i*10
    # #     synth.write('List '+str(i)+' '+str(f))
    # #     print('List '+str(i)+' '+str(f))
    # synth.write('MOD cw')
    synth.query('mod?')
    print(synth.read())
    synth.close()
    # s.set_freq(500)
    s.get_freq()
    s.get_power()
    # synth = s.rm.open_resource(s.device_name)
    # synth.query('List?')
    # for i in range(32):
    #     print(synth.read())
    # synth.close()

