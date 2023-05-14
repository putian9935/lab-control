from target import Target 
from fname_gen_backend.filename_gui import main

class FileNameGenerator(Target):
    def __init__(self) -> None:
        super().__init__()
        Target.backgrounds.append(main()) 
    