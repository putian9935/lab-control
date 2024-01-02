import importlib

def load_module(path, **kwds):
    """ Load module dynamically 
    
    Parameters
    ---
    - path: the path to file, e.g. "lab_control.lab.offline_lab"; 
    - kwds: parameters to be passed before the execution of module. 
    """
    
    spec = importlib.util.find_spec(path)
    module = importlib.util.module_from_spec(spec)
    module.__dict__.update(kwds)
    spec.loader.exec_module(module)
    return module 
