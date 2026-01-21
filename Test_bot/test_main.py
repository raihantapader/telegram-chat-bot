# test_main.py - Run 5 Customer Bots + English Evaluation

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

BOT_FILES = ["final_bot1.py", "final_bot2.py", "final_bot3.py", "final_bot4.py", "final_bot5.py"]
BOT_NAMES = ["Bot_1-Ted", "Bot_2-James", "Bot_3-Charlie", "Bot_4-Jayson", "Bot_5-Peter"]
EVALUATION_SCRIPT = "test_english_level.py"
EVALUATION_INTERVAL = 60


def start_bot(bot_file, bot_name):
    try:
        process = subprocess.Popen([sys.executable, bot_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(0.5)
        if process.poll() is None:
            print(f"  ✅ {bot_name} (PID: {process.pid})")
            return process
        print(f"  ❌ {bot_name} failed")
        return None
    except Exception as e:
        print(f"  ❌ {bot_name}: {e}")
        return None


def run_evaluation():
    try:
        result = subprocess.run([sys.executable, EVALUATION_SCRIPT], capture_output=True, text=True, timeout=120)
        if result.stdout.strip():
            print(result.stdout)
    except Exception as e:
        print(f"⚠️ Evaluation Error: {e}")


def evaluation_loop(stop_event):
    while not stop_event.is_set():
        time.sleep(EVALUATION_INTERVAL)
        if stop_event.is_set():
            break
        run_evaluation()


def main():
    print(f"\n{'='*70}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    # Check files
    missing = [f for f in BOT_FILES + [EVALUATION_SCRIPT] if not os.path.exists(f)]
    if missing:
        print(f"❌ Missing: {missing}")
        return
    
    # Start bots
    print("🤖 Starting Bots...")
    processes = []
    for bot_file, bot_name in zip(BOT_FILES, BOT_NAMES):
        proc = start_bot(bot_file, bot_name)
        if proc:
            processes.append({'file': bot_file, 'name': bot_name, 'process': proc})
        time.sleep(1)
    
    if not processes:
        print("❌ No bots started!")
        return
    
    print(f"\n✅ {len(processes)}/{len(BOT_FILES)} bots running")
    
    # Run evaluation immediately
    run_evaluation()
    
    print(f"📊 Next evaluation in {EVALUATION_INTERVAL}s")
    print(f"{'-'*70}")
    print("Press Ctrl+C to stop")
    print(f"{'-'*70}\n")
    
    # Start evaluation thread
    stop_event = threading.Event()
    threading.Thread(target=evaluation_loop, args=(stop_event,), daemon=True).start()
    
    # Monitor loop
    try:
        while True:
            for bot in processes:
                if bot['process'].poll() is not None:
                    print(f"⚠️ {bot['name']} restarting...")
                    new_proc = start_bot(bot['file'], bot['name'])
                    if new_proc:
                        bot['process'] = new_proc
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        stop_event.set()
        for bot in processes:
            try:
                bot['process'].terminate()
            except:
                pass
        print("✅ Stopped\n")


if __name__ == "__main__":
    main()