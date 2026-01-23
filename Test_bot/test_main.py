# test_main.py - Run Starter Bot + 5 Customer Bots + English Evaluation + Telegram Monitor

import subprocess
import sys
import os
import time
import threading
from datetime import datetime

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# FILE CONFIGURATIONS
STARTER_BOT_SCRIPT = "starter_bot2.py"
BOT_FILES = ["final_bot1.py", "final_bot2.py", "final_bot3.py", "final_bot4.py", "final_bot5.py"]
BOT_NAMES = ["Bot_1-Ted", "Bot_2-James", "Bot_3-Charlie", "Bot_4-Jayson", "Bot_5-Peter"]
EVALUATION_SCRIPT = "test_english_level.py"
TELEGRAM_MONITOR_SCRIPT = "telegram_chat.py"
EVALUATION_INTERVAL = 60


def start_process(script_file, script_name):
    """Generic function to start any script"""
    try:
        process = subprocess.Popen(
            [sys.executable, script_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(0.5)
        if process.poll() is None:
            print(f"  ✅ {script_name} (PID: {process.pid})")
            return process
        print(f"  ❌ {script_name} failed to start")
        return None
    except Exception as e:
        print(f"  ❌ {script_name}: {e}")
        return None


def run_evaluation():
    """Run the evaluation script"""
    try:
        result = subprocess.run(
            [sys.executable, EVALUATION_SCRIPT],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.stdout.strip():
            print(result.stdout)
    except Exception as e:
        print(f"⚠️ Evaluation Error: {e}")


def evaluation_loop(stop_event):
    """Periodically run evaluation"""
    while not stop_event.is_set():
        time.sleep(EVALUATION_INTERVAL)
        if stop_event.is_set():
            break
        run_evaluation()


def main():
    print(f"\n{'='*70}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    # CHECK ALL REQUIRED FILES
    required_files = [STARTER_BOT_SCRIPT] + BOT_FILES + [EVALUATION_SCRIPT, TELEGRAM_MONITOR_SCRIPT]
    missing = [f for f in required_files if not os.path.exists(f)]
    if missing:
        print(f"❌ Missing files: {missing}")
        return
    
    print("✅ All required files found\n")
    
    # Store all processes for cleanup
    all_processes = []
    
    # STEP 1: Start Starter Bot (First)
    print("🚀 Step 1: Starting Starter Bot...")
    starter_process = start_process(STARTER_BOT_SCRIPT, "Starter Bot")
    if starter_process:
        all_processes.append({'name': 'Starter Bot', 'file': STARTER_BOT_SCRIPT, 'process': starter_process})
    time.sleep(1)

    # STEP 2: Start Customer Bots (1-5)
    print("\n🤖 Step 2: Starting Customer Bots...")
    bot_processes = []
    for bot_file, bot_name in zip(BOT_FILES, BOT_NAMES):
        proc = start_process(bot_file, bot_name)
        if proc:
            bot_processes.append({'name': bot_name, 'file': bot_file, 'process': proc})
            all_processes.append({'name': bot_name, 'file': bot_file, 'process': proc})
        time.sleep(1)

    # STEP 3: Start Telegram Monitor
    print("\n📡 Step 3: Starting Telegram Monitor...")
    telegram_process = start_process(TELEGRAM_MONITOR_SCRIPT, "Telegram Monitor")
    if telegram_process:
        all_processes.append({'name': 'Telegram Monitor', 'file': TELEGRAM_MONITOR_SCRIPT, 'process': telegram_process})
    time.sleep(1)

    # STEP 4: Run Initial Evaluation
    print("\n📊 Step 4: Running Initial Evaluation...")
    run_evaluation()

    # SUMMARY
    print(f"\n{'='*70}")
    print("SYSTEM STATUS".center(70))
    print(f"{'='*70}")
    print(f"  • Starter Bot:      {'✅ Running' if starter_process else '❌ Failed'}")
    print(f"  • Customer Bots:    ✅ {len(bot_processes)}/{len(BOT_FILES)} running")
    print(f"  • Telegram Monitor: {'✅ Running' if telegram_process else '❌ Failed'}")
    print(f"  • Evaluation:       ✅ Running every {EVALUATION_INTERVAL}s")
    print(f"{'='*70}")
    print(f"\n📊 Next evaluation in {EVALUATION_INTERVAL}s")
    print(f"{'-'*70}")
    print("Press Ctrl+C to stop all processes")
    print(f"{'-'*70}\n")
    
    # START EVALUATION LOOP
    stop_event = threading.Event()
    eval_thread = threading.Thread(target=evaluation_loop, args=(stop_event,), daemon=True)
    eval_thread.start()
    
    # MONITOR AND AUTO-RESTART LOOP

    try:
        while True:
            # Check and restart Starter Bot if needed
            if starter_process and starter_process.poll() is not None:
                print("⚠️ Starter Bot restarting...")
                starter_process = start_process(STARTER_BOT_SCRIPT, "Starter Bot")
                # Update in all_processes
                for p in all_processes:
                    if p['name'] == 'Starter Bot':
                        p['process'] = starter_process
            
            # Check and restart Customer Bots if needed
            for bot in bot_processes:
                if bot['process'].poll() is not None:
                    print(f"⚠️ {bot['name']} restarting...")
                    new_proc = start_process(bot['file'], bot['name'])
                    if new_proc:
                        bot['process'] = new_proc
                        # Update in all_processes
                        for p in all_processes:
                            if p['name'] == bot['name']:
                                p['process'] = new_proc
            
            # Check and restart Telegram Monitor if needed
            if telegram_process and telegram_process.poll() is not None:
                print("⚠️ Telegram Monitor restarting...")
                telegram_process = start_process(TELEGRAM_MONITOR_SCRIPT, "Telegram Monitor")
                # Update in all_processes
                for p in all_processes:
                    if p['name'] == 'Telegram Monitor':
                        p['process'] = telegram_process
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print(f"\n{'='*70}")
        print("🛑 STOPPING ALL PROCESSES...".center(70))
        print(f"{'='*70}\n")
        
        stop_event.set()
        
        # Stop all processes
        for proc_info in all_processes:
            try:
                if proc_info['process'] and proc_info['process'].poll() is None:
                    proc_info['process'].terminate()
                    print(f"  ⏹️ Stopped {proc_info['name']}")
            except Exception as e:
                print(f"  ⚠️ Error stopping {proc_info['name']}: {e}")
        
        print(f"\n{'='*70}")
        print("✅ ALL PROCESSES STOPPED".center(70))
        print(f"{'='*70}\n")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 STARTING COMPLETE SYSTEM...".center(70))
    print("=" * 70)
    print("\nExecution Order:")
    print("  1️⃣  Starter Bot (starter_bot2.py)")
    print("  2️⃣  Customer Bots (final_bot1-5.py)")
    print("  3️⃣  Telegram Monitor (telegram_chat.py)")
    print("  4️⃣  English Evaluation (test_english_level.py)")
    print("=" * 70)
    main()