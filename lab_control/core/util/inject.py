from functools import wraps 


def inject_dict_into_function(f, attrs):
    @wraps(f)
    def ret(*args, **kwds):
        for k, v in attrs.items():
            f.__globals__[k] = v
        return f(*args, **kwds)
    return ret 
