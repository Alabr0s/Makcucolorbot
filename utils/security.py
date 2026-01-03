import ctypes
from ctypes import wintypes
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SecurityUtils")

# Constants for SetWindowDisplayAffinity
WDA_NONE = 0x00
WDA_MONITOR = 0x01
WDA_EXCLUDEFROMCAPTURE = 0x11  # Available in Windows 10 Version 2004 and later

def set_window_affinity(hwnd, affinity=WDA_EXCLUDEFROMCAPTURE):
    """
    Sets the display affinity for the specified window to prevent screen capture.
    
    Args:
        hwnd (int): The handle to the window (HWND).
        affinity (int): The affinity value. Default is WDA_EXCLUDEFROMCAPTURE.
                        Use WDA_NONE to remove protection.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Use WinDLL with use_last_error=True to capture error codes reliably
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        
        # Define function prototype
        SetWindowDisplayAffinity = user32.SetWindowDisplayAffinity
        SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
        SetWindowDisplayAffinity.restype = wintypes.BOOL
        
        # Helper to try setting affinity
        def try_set_affinity(aff_value):
            # First reset to WDA_NONE to ensure clean state (fixes glitches on toggle)
            SetWindowDisplayAffinity(hwnd, WDA_NONE)
            
            success_status = SetWindowDisplayAffinity(hwnd, aff_value)
            # Check for error if success status is 0 (FALSE)
            if not success_status:
                err = ctypes.get_last_error()
                return False, err
            return True, 0

        # Attempt 1: Requested affinity (default WDA_EXCLUDEFROMCAPTURE)
        success, error_code = try_set_affinity(affinity)
        
        if success:
            logger.info(f"Successfully set window affinity {hex(affinity)} for HWND {hwnd}")
            return True
        else:
            logger.warning(f"Failed to set affinity {hex(affinity)} for HWND {hwnd}. Error: {error_code}")
            
            # Attempt 2: Fallback to WDA_MONITOR if original failed and was EXCLUDEFROMCAPTURE
            # WDA_MONITOR is supported on older Windows versions (Win 7+)
            if affinity == WDA_EXCLUDEFROMCAPTURE:
                logger.info(f"Retrying with WDA_MONITOR ({hex(WDA_MONITOR)}) for HWND {hwnd}...")
                success_fb, error_code_fb = try_set_affinity(WDA_MONITOR)
                if success_fb:
                    logger.info(f"Fallback success: set WDA_MONITOR for HWND {hwnd}")
                    return True
                else:
                    logger.error(f"Fallback failed. Error: {error_code_fb}")
            
            return False
            
    except Exception as e:
        logger.error(f"Exception in set_window_affinity: {e}")
        return False
