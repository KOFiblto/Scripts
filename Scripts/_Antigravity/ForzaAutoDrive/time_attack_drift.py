import time
import vgamepad as vg

# Configuration
DRIFT_INTERVAL = 0.7  # Time between e-brake taps (seconds)
DRIFT_DURATION = 0.1  # E-brake tap duration (seconds)
EBRAKE_BUTTON = vg.XUSB_BUTTON.XUSB_GAMEPAD_A

print("Starting in 5 seconds... Switch to the Forza Horizon window.")
time.sleep(5)

# Initialize gamepad
gamepad = vg.VX360Gamepad()
gamepad.reset()
gamepad.update()

# Engage right trigger (accelerator) fully
gamepad.right_trigger_float(1.0)
gamepad.update()
print("Gas pedal (Right Trigger) engaged. Drifting running... Press Ctrl+C to stop.")

try:
    last_tap = time.time()
    ebrake_state = False
    
    while True:
        now = time.time()
        since_last = now - last_tap
        if not ebrake_state:
            # Wait to press e-brake
            if since_last >= DRIFT_INTERVAL:
                gamepad.press_button(button=EBRAKE_BUTTON)
                gamepad.update()
                ebrake_state = True
                last_tap = now
        else:
            # Wait to release e-brake
            if since_last >= DRIFT_DURATION:
                gamepad.release_button(button=EBRAKE_BUTTON)
                gamepad.update()
                ebrake_state = False
                last_tap = now
                
        # Small sleep for precision loop timings
        time.sleep(0.01)
except KeyboardInterrupt:
    print("\nStopping...")
finally:
    gamepad.reset()
    gamepad.update()
    del gamepad
    print("Controller reset and disconnected.")