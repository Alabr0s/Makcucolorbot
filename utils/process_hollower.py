import os
import sys
import random
import subprocess
import ctypes
from ctypes import wintypes
import psutil
import time

def get_legitimate_processes():
    """Return a list of legitimate processes that can be used"""
    return [
        "notepad.exe",
        "regedit.exe",
        "calc.exe"
    ]

def get_random_target_process():
    """Get a random legitimate process to target"""
    legitimate_processes = get_legitimate_processes()
    return random.choice(legitimate_processes)

def is_process_running(process_name):
    """Check if a process is currently running"""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'].lower() == process_name.lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def find_existing_legitimate_process():
    """Find an existing legitimate process that we can use"""
    legitimate_processes = get_legitimate_processes()
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'].lower() in [p.lower() for p in legitimate_processes]:
                return proc.info['name'], proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None, None

def start_legitimate_process(process_name):
    """Start a legitimate process normally"""
    try:
        # Get system directory
        system32 = os.path.join(os.environ['SystemRoot'], 'System32')
        process_path = os.path.join(system32, process_name)
        
        if os.path.exists(process_path):
            # Start the process normally
            process = subprocess.Popen([process_path])
            return process.pid
        else:
            # Try to find in root directory (for regedit.exe)
            root_process = os.path.join(os.environ['SystemRoot'], process_name)
            if os.path.exists(root_process):
                process = subprocess.Popen([root_process])
                return process.pid
            else:
                print(f"Process {process_name} not found")
                return None
    except PermissionError:
        print(f"Permission denied starting process {process_name}. May require elevated privileges.")
        return None
    except Exception as e:
        print(f"Error starting process {process_name}: {e}")
        return None

def disguise_current_process():
    """
    Disguise the current process to appear as a legitimate Windows process
    """
    try:
        # Change console window title if running in console
        try:
            import ctypes
            # Set console title to appear as a system process
            ctypes.windll.kernel32.SetConsoleTitleW("Windows PowerShell")
        except:
            pass
            
        # Try to change working directory to system directory
        try:
            system_dir = os.path.join(os.environ['SystemRoot'], 'System32')
            if os.path.exists(system_dir):
                os.chdir(system_dir)
        except:
            pass
            
        return True
    except Exception as e:
        print(f"Error disguising process: {e}")
        return False

def mimic_system_behavior():
    """
    Mimic system process behavior to appear more legitimate
    """
    try:
        # Add small delay to mimic system process startup
        time.sleep(0.1)
        
        # Try to set process priority (if possible)
        try:
            current_process = psutil.Process()
            # Set to normal priority
            current_process.nice(psutil.NORMAL_PRIORITY_CLASS)
        except:
            pass
            
        return True
    except Exception as e:
        return False

def run_as_stealth_process():
    """
    Function to make the application appear as a legitimate Windows process
    This version focuses on mimicking behavior rather than actual injection
    """
    try:
        print("Attempting to run as stealth process...")
        
        # First, disguise the current process
        disguise_current_process()
        
        # Mimic system behavior
        mimic_system_behavior()
        
        # Get current process name
        current_process = psutil.Process()
        current_name = current_process.name().lower()
        legitimate_processes = [p.lower() for p in get_legitimate_processes()]
        
        # If we're already running as a legitimate process name, we're already disguised
        if current_name in legitimate_processes:
            print(f"Already running as legitimate process: {current_name}")
            return True
            
        # Check if there's already a legitimate process running that we can mimic
        existing_process_name, existing_pid = find_existing_legitimate_process()
        
        if existing_process_name and existing_pid:
            print(f"Mimicking existing legitimate process: {existing_process_name}")
            # We're already running in a similar context
            return True
        else:
            print("Starting a legitimate process to blend in")
            # Select a random legitimate process
            target_process = get_random_target_process()
            print(f"Starting legitimate process: {target_process}")
            
            # Start the legitimate process normally
            pid = start_legitimate_process(target_process)
            if pid:
                print(f"Started {target_process} with PID: {pid} - Process is running normally")
                # In a real scenario, we might hide our window and show the legitimate process
                return True
            else:
                print(f"Failed to start {target_process}")
                return False
        
    except Exception as e:
        print(f"Error in stealth process execution: {e}")
        return False