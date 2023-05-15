from core.target import Target
import importlib.util


class TimeSequencerFPGA(Target):
    def __init__(self, host, port, **kwargs) -> None:
        super().__init__(**kwargs)

        spec = importlib.util.find_spec(
            'fpga_communicate_jinchao', '.')
        self.backend = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.backend)
        self.backend.sequencer.connect(host, port)


if __name__ == '__main__':
    ts = TimeSequencerFPGA('192.168.107.146', 5555)
