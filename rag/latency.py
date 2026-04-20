import time

def timed_step(name, fn, *args, **kwargs):
    start=time.time()
    result=fn(*args, **kwargs)
    end=time.time()
    print(f"{name}: {end-start:.4f}s")
    return result