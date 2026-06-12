import time
import sys
import vgamepad as vg

# Initialize the virtual Xbox 360 controller channel
gamepad = vg.VX360Gamepad()

def visual_sleep(seconds, label="Waiting"):
    bar_length = 30
    total_steps = int(seconds * 10)
    
    for i in range(total_steps + 1):
        progress = i / total_steps if total_steps > 0 else 1.0
        block = int(progress * bar_length)
        remaining_seconds = max(0, seconds - (i / 10))
        
        text = f"\r{label}: [{'█' * block}{'.' * (bar_length - block)}] {int(progress * 100)}% ({remaining_seconds:.1f}s)"
        sys.stdout.write(text)
        sys.stdout.flush()
        
        if i < total_steps:
            time.sleep(0.1)
            
    sys.stdout.write("\r" + " " * (len(text) + 10) + "\r")
    sys.stdout.flush()

def press_btn(button, duration=0.15):
    gamepad.press_button(button=button)
    gamepad.update()
    time.sleep(duration)
    gamepad.release_button(button=button)
    gamepad.update()
    time.sleep(0.25)

def flick_stick(direction, duration=0.15):
    if direction == "UP":
        gamepad.left_joystick_float(0.0, 1.0)
    elif direction == "DOWN":
        gamepad.left_joystick_float(0.0, -1.0)
    elif direction == "LEFT":
        gamepad.left_joystick_float(-1.0, 0.0)
    elif direction == "RIGHT":
        gamepad.left_joystick_float(1.0, 0.0)
        
    gamepad.update()
    time.sleep(duration)
    
    gamepad.left_joystick_float(0.0, 0.0)
    gamepad.update()
    time.sleep(0.25)

def run_macro():
    global gamepad
    gamepad.reset()
    gamepad.update()
    
    print("Virtual Controller initialized and driver states flushed.")
    print("You can now safely move the game to the background display screen.")
    counter = 0
    
    A_BTN = vg.XUSB_BUTTON.XUSB_GAMEPAD_A
    B_BTN = vg.XUSB_BUTTON.XUSB_GAMEPAD_B
    X_BTN = vg.XUSB_BUTTON.XUSB_GAMEPAD_X

    try:
        while True:
            print(f"Startet Run {counter}")
            
            print(" - Start Event (X)")
            press_btn(X_BTN)
            visual_sleep(3)

            print(" - Go to Custom (Joystick Down -> A)")
            flick_stick("DOWN")  
            press_btn(A_BTN)
            visual_sleep(3)

            print(" - Change Cars (Joystick Up -> A)")
            flick_stick("UP")
            press_btn(A_BTN)
            visual_sleep(3)

            print(" - Select All Cars (Joystick Left 20x -> Joystick Up -> A)")
            for _ in range(20):
                flick_stick("LEFT")
            flick_stick("UP")
            press_btn(A_BTN)
            visual_sleep(4)

            print(" - Select X-Class (Joystick Right 5x -> A)")
            #for _ in range(5):
            #    flick_stick("RIGHT")
            press_btn(A_BTN)
            visual_sleep(2)

            print(" - Confirm Event (Joystick Down -> A)")
            flick_stick("DOWN")
            press_btn(A_BTN)
            visual_sleep(2)

            print(" - Start with Solo (A)")
            press_btn(A_BTN)
            visual_sleep(2)

            print(" - Keep current Car (A)")
            press_btn(A_BTN)
            visual_sleep(30, "Loading Menu")
            
            print(" - Dismissing potential difficulty prompts (B)")
            press_btn(B_BTN)
            visual_sleep(1)

            print(" - Start race (A)")
            press_btn(A_BTN)

            print(" - Wait before D-pad inputs")
            visual_sleep(5, "Pre-race buffer")

            print(" - D-pad down")
            flick_stick("DOWN")
            visual_sleep(1, "Post D-pad down wait")

            print(" - D-pad left")
            flick_stick("LEFT")
            
            print(" - Wait for race to finish")
            visual_sleep(7 * 60, "Race Active")
            
            print(" - Out of Leaderboard (A)")
            press_btn(A_BTN)
            visual_sleep(30, "Leaving Race")
            
            print(" - Cooldown complete. Restarting loop sequence.")
            counter += 1

    except KeyboardInterrupt:
        print("\nAutomation loop gracefully terminated.")
    finally:
        print("Disconnecting virtual controller and clearing hardware states...")
        gamepad.reset()
        gamepad.update()
        del gamepad 

if __name__ == "__main__":
    run_macro()