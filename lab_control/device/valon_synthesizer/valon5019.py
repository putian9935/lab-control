import pyvisa

class Synth:
    def __init__(self):
        # to be determined 
        self.device_name = 'ASRL3::INSTR'
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
        # this doesn't work and I don't know why
        self.synth = self.rm.open_resource(self.device_name)
        reply = self.synth.query('Frequency?')
        print(reply)
        self.synth.close()
        
if __name__ == '__main__':
    s = Synth()

    while(True):
        freq = input()
        s.set_freq(freq)