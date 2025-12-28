import asyncio
import os
import subprocess

# Main function to run all bots
async def run_all_bots():
    # Start the starter bot
    starter_bot_process = subprocess.Popen(["python", "start.py"])

    # Start the customer bots
    customer_bot_process = subprocess.Popen(["python", "customer.py"])

    # Start the sales bot
    sales_bot_process = subprocess.Popen(["python", "sales.py"])

    # Wait for all bots to finish (in case of any issues)
    await asyncio.gather(
        starter_bot_process.wait(),
        customer_bot_process.wait(),
        sales_bot_process.wait()
    )

# Entry point to run the bots concurrently
if __name__ == "__main__":
    asyncio.run(run_all_bots())
