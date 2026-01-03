# Defending Store - Multi-Computer Aim Assistant

A sophisticated multi-computer aim assistance system designed for low-spec secondary computers. This project enables color-based target detection on a powerful primary computer while sending precise mouse commands to a secondary computer with limited resources.

### Showcase Video
Thanks for the video, KainX

[Watch Showcase](https://streamable.com/ltv74c)


# Update Notes:

**Version 2.3**
User Interface Overhaul We have introduced a completely new, professional-grade Graphical User Interface (GUI). The design is now softer, more modern, and streamlined to improve user experience and visual comfort.

Performance Optimization The screen capture mechanism has been heavily optimized. You will notice significantly improved performance with lower latency and reduced CPU/GPU usage.

Bug Fixes & Improvements

Aim Stability: Fixed the issue causing the aim to shake or jitter. Targeting is now much smoother and more precise.

Spike Timer Accuracy: The issue regarding the Spike Timer has been resolved. The countdown is now perfectly synced and accurate.

New Features

Configuration System: Added a brand new Config System. You can now save your custom settings, create different profiles, and load them instantly whenever needed.

*Version 1.3*
- Added 'tcp_nodelay' to the TCP connection protocol
- Added 3 preset weapon configs to the Triggerbot page (Sheriff, Vandal, Ghost)
- Added a spectrum to the Color page for adjustments
Note: This is a minor update intended to fix aim speed jitter issues and improve ease of use.

*Version 1.2*
- Freezing issue on the Aimbot page resolved
- Queue added to the TCP client (for optimization)
- Lag issue while aiming fixed


## Features

### Aimbot System
- Advanced target detection with customizable sensitivity
- Head and body targeting options
- Adjustable aim speed and smoothness
- Configurable FPS scanning rates (up to 200 FPS)
- Adaptive prediction algorithms for improved accuracy
- Visual indicator overlay for target tracking

### HSV Color Settings
- Precise color detection using HSV (Hue, Saturation, Value) color space
- Customizable color range parameters
- Preset color templates (Purple, Red, Yellow)
- Real-time color calibration for optimal target recognition

### Triggerbot
- Automatic firing when targets are detected
- Configurable fire delay settings (min/max values)
- Adjustable scan area size and FPS
- Hold key and toggle key support
- Integration with color settings for accurate detection

### Recoil Control System (RCS)
- Automatic downward recoil compensation
- Configurable pull speed settings
- Activation delay and rapid click threshold controls
- Integration with aimbot for combined movement control
- Designed specifically for Valorant spray patterns

### Spike Timer
- Automatic spike detection in Valorant
- Configurable time tolerance settings
- Visual countdown timer display
- Automatic activation when spike is detected

## Why This Project?

I created this project because my secondary computer has very limited resources (Raspberry Pi level specifications). Most color bot applications were unable to run effectively on such low-spec hardware. 

This solution allows my powerful primary computer to handle all the intensive color detection and processing tasks, while sending only lightweight mouse movement commands to the secondary computer. This approach makes it possible for users with low-spec secondary systems to benefit from accurate color-based target detection without overloading their hardware.

## Installation Instructions

1. Install the required dependencies using pip:
   ```
   pip install -r req.txt
   ```

2. Run the `2pc.py` file on your secondary computer.

3. Note the local IP address of your secondary computer.

4. Run the `main.py` file from the defendingstore project on your primary computer.

5. In the server connection screen, enter the local IP address you noted earlier. (This step is only necessary if the automatic detection fails to find your secondary computer.)

## Requirements

- Python 3.7+
- PyQt5
- NumPy
- QtAwesome
- Pynput
- MSS
- OpenCV-Python
- Keyboard

## How It Works

The system consists of two components:
1. **Primary Computer**: Runs the full application with GUI, performs color detection and processing
2. **Secondary Computer**: Receives lightweight mouse commands via TCP connection

Communication between the computers is handled through a custom TCP protocol on port 1515, ensuring minimal latency and maximum responsiveness.




This is a defendingstore.com project.


