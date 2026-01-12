import os
from dotenv import load_dotenv
#from New_way_try.customer_bot import run_customer_bot
from customer_bot import run_customer_bot


load_dotenv()

if __name__ == "__main__":
    run_customer_bot(os.environ["TELEGRAM_BOT_3_TOKEN"], "customer_3")
