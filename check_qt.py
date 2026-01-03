
try:
    import qtawesome
    print("qtawesome found")
except ImportError:
    print("qtawesome NOT found")

try:
    from PyQt5.QtWidgets import QWidget
    print("PyQt5 found")
except ImportError:
    print("PyQt5 NOT found")
