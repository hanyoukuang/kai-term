import os
import sys
import time
from par_term_emu_core_rust import PtyTerminal

def main():
    print("==================================================")
    print(" Reproducing Rust Backend Panic on Windows")
    print("==================================================\n")
    
    print("[1] Initializing PtyTerminal...")
    term = PtyTerminal(80, 24, 1000)
    term.spawn_shell()
    print("[2] Shell spawned successfully.\n")

    # Wait for the shell to fully initialize
    time.sleep(1)

    # Start a dummy foreground process that behaves like a TUI
    print("[3] Starting a dummy foreground process (simulating OpenCode)...")
    term.write(b'python -c "import time; print(\'TUI running...\'); time.sleep(10)"\n')
    time.sleep(1)

    # Send Ctrl+C (\x03) to the PTY
    # This causes the foreground process to exit, and on Windows, 
    # ConPTY will abruptly break the named pipe.
    print("[4] Sending Ctrl+C (\\x03) to terminate the foreground process...\n")
    term.write(b'\x03')
    
    print("[5] Entering poll/write loop.")
    print("    If Rust panics (e.g. unwrap() on ERROR_BROKEN_PIPE), ")
    print("    this script will instantly abort (Crash/闪退) without catching any Exception.\n")
    
    generation = 0
    for i in range(1, 11):
        time.sleep(0.5)
        print(f"--- Iteration {i} ---")
        
        # 1. Try to poll updates
        try:
            has_up = term.has_updates_since(generation)
            if has_up:
                generation = term.update_generation()
            print("    Poll OK.")
        except Exception as e:
            # If Rust gracefully returns an error, we catch it here.
            print(f"    Poll raised Python Exception (Caught safely): {e}")

        # 2. Try to write to the PTY
        try:
            term.write(b"a")
            print("    Write OK.")
        except Exception as e:
            # If Rust gracefully handles the broken pipe, we catch it here.
            print(f"    Write raised Python Exception (Caught safely): {e}")

    print("\n[6] SUCCESS: Test finished normally. If you see this, the panic did NOT occur.")

if __name__ == "__main__":
    # Isolate the Python process from the Windows CTRL_C_EVENT broadcast.
    # This ensures that if the process dies, it is strictly due to a Rust panic,
    # and NOT because the OS killed the Python interpreter.
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        global _win_ctrl_handler
        _win_ctrl_handler = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)(lambda _: True)
        ctypes.windll.kernel32.SetConsoleCtrlHandler(_win_ctrl_handler, True)
    
    main()
