from ...core.target import Target 
from .filename_gui import main, exported_funcs, action_changeFilenameAndStartCamAcq, action_StopCamAcq
from ...core.config import config 

class FileNameGenerator(Target):
    def __init__(self) -> None:
        super().__init__()
        type(self).backgrounds.append(main()) 

    def test_precondition(self):
        input(f'[INFO] name okay?')
        print('setting up cam')
        exported_funcs['set_cam']()
        return True
    
class FileNameGeneratorNoGui(Target):
    ''' No GUI file name generator '''
    def __init__(self, update_func=None, stop_func=None) -> None:
        super().__init__()
        if update_func is None:
            update_func = action_changeFilenameAndStartCamAcq
        self.update_func = update_func
        if stop_func is None:
            stop_func = action_StopCamAcq
        self.stop_func = stop_func

    def test_precondition(self):
        self.update_func(config.fname[:80])
        return True
    
    def test_postcondition(self) -> bool:
        self.stop_func()
        return True
