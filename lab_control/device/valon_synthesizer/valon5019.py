import pyvisa

class Synth:
    def __init__(self):
        # device name on indium desktop 1
        self.device_name = 'ASRL16::INSTR'
        # device name on strontium laptop
        # self.device_name = 'ASRL3::INSTR'
        self.rm = pyvisa.ResourceManager()
        self.rmlist = self.rm.list_resources()
        print(self.rmlist)
        if self.device_name not in self.rmlist:
            raise Exception('Could not find valon synthesizer ' + self.device_name)

        # self.synth = self.rm.open_resource(self.device_name)
        # print('Connected to valon synthesizer!')

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
        
if __name__ == '__main__':
    s = Synth()

    while(True):
        freq = input('Input frequency in MHz:\n')
        s.set_freq(freq)
        s.get_freq()