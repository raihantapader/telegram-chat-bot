import multiprocessing as mp
import os
from dotenv import load_dotenv

load_dotenv()

def run_starter():
    import starter
    starter.run_starter()

def run_customer_1():
    import customer_1
    customer_1.run_customer_bot(os.environ["TELEGRAM_BOT_1_TOKEN"], "customer_1")

def run_customer_2():
    import customer_2
    customer_2.run_customer_bot(os.environ["TELEGRAM_BOT_2_TOKEN"], "customer_2")

def run_customer_3():
    import customer_3
    customer_3.run_customer_bot(os.environ["TELEGRAM_BOT_3_TOKEN"], "customer_3")

def run_customer_4():
    import customer_4
    customer_4.run_customer_bot(os.environ["TELEGRAM_BOT_4_TOKEN"], "customer_4")

def run_customer_5():
    import customer_5
    customer_5.run_customer_bot(os.environ["TELEGRAM_BOT_5_TOKEN"], "customer_5")

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)

    procs = [
        mp.Process(target=run_starter, name="starter"),
        mp.Process(target=run_customer_1, name="customer_1"),
        mp.Process(target=run_customer_2, name="customer_2"),
        mp.Process(target=run_customer_3, name="customer_3"),
        mp.Process(target=run_customer_4, name="customer_4"),
        mp.Process(target=run_customer_5, name="customer_5"),
    ]

    for p in procs:
        p.start()

    for p in procs:
        p.join()
