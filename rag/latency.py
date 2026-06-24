import time

def timed_step(name, fn, *args, **kwargs):
    start=time.time()
    result=fn(*args, **kwargs)
    elapsed_ms=(time.time()-start)*1000
    print(f"{name}: {elapsed_ms:.2f}ms")
    return result, elapsed_ms