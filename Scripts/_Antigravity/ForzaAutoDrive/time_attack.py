import time
import vgamepad as vg

print("Starting in 5 seconds... Switch to the Forza Horizon window.")
time.sleep(5)

# Initialize gamepad
gamepad = vg.VX360Gamepad()
gamepad.reset()
gamepad.update()

try:
    # Engage right trigger (accelerator) fully
    gamepad.right_trigger_float(1.0)
    gamepad.update()
    print("Gas pedal (Right Trigger) engaged. Running... Press Ctrl+C to stop.")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping...")
finally:
    gamepad.reset()
    gamepad.update()
    del gamepad
    print("Controller reset and disconnected.")