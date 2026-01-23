# check_files.py

import os
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


print("Current directory:", os.getcwd())
print("\nFiles in current directory:")
for file in os.listdir('.'):
    if file.endswith('.py'):
        print(f"  ✓ {file}")

print("\nLooking for specific files:")
files_to_check = [
    "final_bot1.py",
    "final_bot_2.py", 
    "final_bot_3.py",
    "final_bot_4.py",
    "final_bot_5.py",
    "final_bot1.py",
    "final_bot2.py",
    "final_bot3.py",
    "final_bot4.py",
    "final_bot5.py"
]

for file in files_to_check:
    exists = os.path.exists(file)
    symbol = "✅" if exists else "❌"
    print(f"  {symbol} {file}")