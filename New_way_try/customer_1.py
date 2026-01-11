import os
from dotenv import load_dotenv
from customer_bots import run_customer_bot

load_dotenv()

if __name__ == "__main__":
    run_customer_bot(os.environ["CUST1_TOKEN"], "customer_1")
