# main.py

import subprocess
import sys
import os
import time
from datetime import datetime


if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# CORRECT: Without underscores (matching your actual files)
BOT_FILES = [
    "final_bot1.py",
    "final_bot2.py",
    "final_bot3.py",
    "final_bot4.py",
    "final_bot5.py"
]

BOT_NAMES = [
    "🤖 Bot_1 - Ted (@Cust0m3rBot)",
    "🤖 Bot_2 - James (@Cust0m4rBot)",
    "🤖 Bot_3 - Charlie (@Cust0m5rBot)",
    "🤖 Bot_4 - Jayson (@Cust0m6rBot)",
    "🤖 Bot_5 - Peter (@Cust0m7rBot)"
]

def print_header():
    """Print a nice header"""
    print("\n" + "="*70)
    print("CUSTOMER BOTS MANAGER".center(70))
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

def check_bot_files():
    """Check if all bot files exist"""
    missing_files = []
    
    print("Checking bot files...")
    for bot_file in BOT_FILES:
        if os.path.exists(bot_file):
            print(f"  ✅ {bot_file}")
        else:
            print(f"  ❌ {bot_file}")
            missing_files.append(bot_file)
    
    print()
    
    if missing_files:
        print("❌ ERROR: Missing files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print(f"✅ All {len(BOT_FILES)} bot files found!\n")
    return True

def start_bot(bot_file, bot_name):
    """Start a single bot as a subprocess"""
    try:
        print(f"🚀 Starting {bot_name}...")
        
        process = subprocess.Popen(
            [sys.executable, bot_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        time.sleep(0.5)
        
        if process.poll() is None:
            print(f"   ✅ Started (PID: {process.pid})")
            return process
        else:
            print(f"   ❌ Failed to start")
            return None
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def main():
    """Main function to run all bots concurrently"""
    
    print_header()
    
    if not check_bot_files():
        print("\n⚠️  Fix missing files first!")
        return
    
    print("-"*70)
    print("Starting all customer bots...".center(70))
    print("-"*70 + "\n")
    
    processes = []
    
    for bot_file, bot_name in zip(BOT_FILES, BOT_NAMES):
        process = start_bot(bot_file, bot_name)
        if process:
            processes.append({
                'file': bot_file,
                'name': bot_name,
                'process': process
            })
        time.sleep(1)
    
    if not processes:
        print("\n❌ No bots started!")
        return
    
    print("\n" + "="*70)
    print(f"✅ {len(processes)}/{len(BOT_FILES)} BOTS RUNNING".center(70))
    print("="*70)
    print("\nActive Bots:")
    for i, bot in enumerate(processes, 1):
        print(f"   {i}. {bot['name']} (PID: {bot['process'].pid})")
    
    print("\n" + "-"*70)
    print("Press Ctrl+C to stop all bots".center(70))
    print("-"*70 + "\n")
    
    try:
        while True:
            for bot in processes:
                poll = bot['process'].poll()
                if poll is not None:
                    print(f"\n⚠️  {bot['name']} stopped (code: {poll})")
                    print(f"🔄 Restarting...")
                    new_process = start_bot(bot['file'], bot['name'])
                    if new_process:
                        bot['process'] = new_process
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("STOPPING ALL BOTS...".center(70))
        print("="*70 + "\n")
        
        for i, bot in enumerate(processes, 1):
            try:
                print(f"   {i}. Stopping {bot['name']}...", end=" ")
                bot['process'].terminate()
                bot['process'].wait(timeout=5)
                print("✅")
            except Exception as e:
                print(f"❌")
                try:
                    bot['process'].kill()
                except:
                    pass
        
        print("\n" + "="*70)
        print("ALL BOTS STOPPED".center(70))
        print("="*70 + "\n")

if __name__ == "__main__":
    main()