import multiprocessing as mp
import os
from dotenv import load_dotenv

load_dotenv()

def run_starter():
    import starter
    starter.run_starter()

def run_c1():
    import customer_1

def run_c2():
    import customer_2

def run_c3():
    import customer_3

def run_c4():
    import customer_4

def run_c5():
    import customer_5

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)

    procs = [
        mp.Process(target=run_starter, name="starter"),
        mp.Process(target=run_c1, name="customer_1"),
        mp.Process(target=run_c2, name="customer_2"),
        mp.Process(target=run_c3, name="customer_3"),
        mp.Process(target=run_c4, name="customer_4"),
        mp.Process(target=run_c5, name="customer_5"),
    ]

    for p in procs:
        p.start()

    for p in procs:
        p.join()
