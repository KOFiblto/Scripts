import time
import threading
import vgamepad as vg
import win32gui
import win32con
import win32com.client

BUTTON_MAP = {
    "A_BTN": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    "B_BTN": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    "X_BTN": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    "Y_BTN": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    "START": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    "BACK": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    "LB": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    "RB": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    "L_THUMB": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    "R_THUMB": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    "DPAD_UP": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    "DPAD_DOWN": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    "DPAD_LEFT": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    "DPAD_RIGHT": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
}

class StatusTracker:
    def __init__(self):
        self.lock = threading.Lock()
        self.is_running = False
        self.phase = "Stopped"
        self.description = "Idle"
        self.progress = 0.0
        self.run_count = 0
        self.accumulated_cr = 0
        self.accumulated_xp = 0
        self.accumulated_skillpoints = 0
        self.time_left = 0.0
        self.error_msg = None
        
    def update(self, **kwargs):
        with self.lock:
            for k, v in kwargs.items():
                if hasattr(self, k):
                    setattr(self, k, v)
                    
    def get_snapshot(self):
        with self.lock:
            return {
                "is_running": self.is_running,
                "phase": self.phase,
                "description": self.description,
                "progress": self.progress,
                "run_count": self.run_count,
                "accumulated_cr": self.accumulated_cr,
                "accumulated_xp": self.accumulated_xp,
                "accumulated_skillpoints": self.accumulated_skillpoints,
                "time_left": self.time_left,
                "error_msg": self.error_msg
            }

def focus_window_by_title(title_substring):
    hwnd_found = []
    def enum_windows_callback(hwnd, extra):
        title = win32gui.GetWindowText(hwnd)
        if title_substring.lower() in title.lower() and win32gui.IsWindowVisible(hwnd):
            hwnd_found.append(hwnd)
        return True
    
    win32gui.EnumWindows(enum_windows_callback, None)
    if hwnd_found:
        hwnd = hwnd_found[0]
        try:
            # Send an ALT key to release foreground lock
            shell = win32com.client.Dispatch("WScript.Shell")
            shell.SendKeys('%')
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception as e:
            print(f"Error focusing window: {e}")
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetForegroundWindow(hwnd)
                return True
            except Exception:
                pass
    return False

def resolve_control(val, settings):
    if val.startswith("ROLE_"):
        role = val.replace("ROLE_", "")
        return settings.get(f"control_{role}", "A_BTN")
    return val

def apply_accelerate(gamepad, control, value):
    if control == "RT":
        gamepad.right_trigger_float(value)
    elif control == "LT":
        gamepad.left_trigger_float(value)
    else:
        btn = BUTTON_MAP.get(control)
        if btn is not None:
            if value > 0.5:
                gamepad.press_button(button=btn)
            else:
                gamepad.release_button(button=btn)
    gamepad.update()

def press_btn(gamepad, btn_str, settings, duration=0.15):
    btn_str = resolve_control(btn_str, settings)
    btn = BUTTON_MAP.get(btn_str)
    if btn is not None:
        gamepad.press_button(button=btn)
        gamepad.update()
        time.sleep(duration)
        gamepad.release_button(button=btn)
        gamepad.update()
        time.sleep(0.25)

def flick_stick(gamepad, direction_str, settings, duration=0.15):
    direction_str = resolve_control(direction_str, settings)
    if direction_str == "STICK_UP" or direction_str == "UP":
        gamepad.left_joystick_float(0.0, 1.0)
    elif direction_str == "STICK_DOWN" or direction_str == "DOWN":
        gamepad.left_joystick_float(0.0, -1.0)
    elif direction_str == "STICK_LEFT" or direction_str == "LEFT":
        gamepad.left_joystick_float(-1.0, 0.0)
    elif direction_str == "STICK_RIGHT" or direction_str == "RIGHT":
        gamepad.left_joystick_float(1.0, 0.0)
        
    gamepad.update()
    time.sleep(duration)
    gamepad.left_joystick_float(0.0, 0.0)
    gamepad.update()
    time.sleep(0.25)

def execute_step(gamepad, step, settings):
    rep = step.get("repetitions", 1)
    for _ in range(rep):
        if step["action_type"] == "button":
            press_btn(gamepad, step["action_value"], settings)
        elif step["action_type"] == "stick":
            flick_stick(gamepad, step["action_value"], settings)
        elif step["action_type"] == "wait":
            time.sleep(0.4)

class AutodriveRunner:
    def __init__(self, tracker):
        self.tracker = tracker
        self.thread = None
        
    def start(self, track, car, start_seq, post_seq, settings):
        self.tracker.update(
            is_running=True,
            phase="Startup Delay",
            description="Starting up...",
            progress=0.0,
            run_count=0,
            accumulated_cr=0,
            accumulated_xp=0,
            accumulated_skillpoints=0,
            time_left=0.0,
            error_msg=None
        )
        self.thread = threading.Thread(
            target=self._run,
            args=(track, car, start_seq, post_seq, settings),
            daemon=True
        )
        self.thread.start()
        
    def stop(self):
        self.tracker.update(is_running=False, phase="Stopping", description="Stopping virtual controller...")
        
    def _run(self, track, car, start_seq, post_seq, settings):
        gamepad = None
        try:
            gamepad = vg.VX360Gamepad()
            gamepad.reset()
            gamepad.update()
            
            # Read dynamic execution overrides
            focus_mode = settings.get("execution_focus_mode", "Foreground")
            if focus_mode == "Background":
                startup_delay = 0.0
                focus_enabled = False
            else:
                startup_delay = float(settings.get("startup_delay", 5.0))
                focus_enabled = True
                
            autodrive_activation_enabled = settings.get("execution_auto_enable", "True") == "True"
            autodrive_activation_delay = float(settings.get("autodrive_activation_delay", 5.0))
            race_time_buffer = float(settings.get("race_time_buffer", 15.0))
            
            # 1. Countdown delay
            if startup_delay > 0:
                self.tracker.update(phase="Startup Delay", description=f"Waiting for countdown...", progress=0.0)
                steps = int(startup_delay * 10)
                for i in range(steps + 1):
                    if not self.tracker.is_running:
                        return
                    progress = i / steps if steps > 0 else 1.0
                    self.tracker.update(time_left=max(0.0, startup_delay - (i / 10.0)), progress=progress)
                    if i < steps:
                        time.sleep(0.1)
            
            # 2. Focus Window
            if focus_enabled:
                if not self.tracker.is_running:
                    return
                self.tracker.update(phase="Focus Window", description="Focusing Forza Horizon window...", progress=0.5)
                focused = focus_window_by_title("Forza")
                if not focused:
                    print("Could not find or focus Forza Horizon window.")
                time.sleep(1.0)
                
            # 3. Main execution loop
            track_type = track["type"]
            
            if track_type == "Race":
                while self.tracker.is_running:
                    # Phase 1: Universal Start Sequence
                    self.tracker.update(phase="Universal Start", progress=0.0)
                    for step in start_seq:
                        if not self.tracker.is_running:
                            return
                        self.tracker.update(description=f"Start: {step['label']}", progress=0.0)
                        execute_step(gamepad, step, settings)
                        
                        # Post-step delay
                        delay = step["delay"]
                        if delay > 0:
                            steps = int(delay * 10)
                            for i in range(steps):
                                if not self.tracker.is_running:
                                    return
                                time.sleep(0.1)
                                self.tracker.update(time_left=max(0.0, delay - (i / 10.0)), progress=(i / steps))
                                
                    # Phase 2: AutoDrive Activation
                    if autodrive_activation_enabled:
                        if not self.tracker.is_running:
                            return
                        self.tracker.update(phase="AutoDrive Activation", description="Waiting to activate AutoDrive...", progress=0.0)
                        steps = int(autodrive_activation_delay * 10)
                        for i in range(steps):
                            if not self.tracker.is_running:
                                return
                            time.sleep(0.1)
                            self.tracker.update(time_left=max(0.0, autodrive_activation_delay - (i / 10.0)), progress=(i / steps))
                        
                        if not self.tracker.is_running:
                            return
                        self.tracker.update(description="Pressing ANNA (D-Pad Down)")
                        press_btn(gamepad, "ROLE_ANNA", settings)
                        time.sleep(0.5)
                        
                        if not self.tracker.is_running:
                            return
                        self.tracker.update(description="Pressing AutoDrive (D-Pad Left)")
                        press_btn(gamepad, "ROLE_AUTODRIVE", settings)
                        time.sleep(0.5)
                        
                    # Phase 3: Driving / Wait for race to finish
                    self.tracker.update(phase="Race Active", description=f"Driving: Wait for race to finish...", progress=0.0)
                    race_time = car["time_seconds"] + race_time_buffer
                    steps = int(race_time * 10)
                    for i in range(steps + 1):
                        if not self.tracker.is_running:
                            return
                        progress = i / steps if steps > 0 else 1.0
                        self.tracker.update(time_left=max(0.0, race_time - (i / 10.0)), progress=progress)
                        if i < steps:
                            time.sleep(0.1)
                            
                    # Phase 4: Post-Race Sequence
                    self.tracker.update(phase="Post-Race Sequence", progress=0.0)
                    for step in post_seq:
                        if not self.tracker.is_running:
                            return
                        self.tracker.update(description=f"Post-Race: {step['label']}", progress=0.0)
                        execute_step(gamepad, step, settings)
                        
                        delay = step["delay"]
                        if delay > 0:
                            steps = int(delay * 10)
                            for i in range(steps):
                                if not self.tracker.is_running:
                                    return
                                time.sleep(0.1)
                                self.tracker.update(time_left=max(0.0, delay - (i / 10.0)), progress=(i / steps))
                                
                    # End of Run
                    with self.tracker.lock:
                        self.tracker.run_count += 1
                        self.tracker.accumulated_cr += car["cr"]
                        self.tracker.accumulated_xp += car["xp"]
                        self.tracker.accumulated_skillpoints += car["skillpoints"]
                        
            elif track_type == "Time Attack":
                accelerate_control = settings.get("control_ACCELERATE", "RT")
                apply_accelerate(gamepad, accelerate_control, 1.0)
                
                try:
                    while self.tracker.is_running:
                        self.tracker.update(phase="Time Attack Active", description=f"Driving {car['name']} - Gas Held", progress=0.0)
                        race_time = car["time_seconds"] + race_time_buffer
                        steps = int(race_time * 10)
                        for i in range(steps + 1):
                            if not self.tracker.is_running:
                                return
                            progress = i / steps if steps > 0 else 1.0
                            self.tracker.update(time_left=max(0.0, race_time - (i / 10.0)), progress=progress)
                            if i < steps:
                                time.sleep(0.1)
                                
                        with self.tracker.lock:
                            self.tracker.run_count += 1
                            self.tracker.accumulated_cr += car["cr"]
                            self.tracker.accumulated_xp += car["xp"]
                            self.tracker.accumulated_skillpoints += car["skillpoints"]
                finally:
                    apply_accelerate(gamepad, accelerate_control, 0.0)
                    
            elif track_type == "Drift":
                accelerate_control = settings.get("control_ACCELERATE", "RT")
                apply_accelerate(gamepad, accelerate_control, 1.0)
                
                ebrake_control = car["drift_button"] or settings.get("control_EBRAKE", "A_BTN")
                ebrake_button = BUTTON_MAP.get(ebrake_control, vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
                
                drift_interval = float(car["drift_interval"] or 0.7)
                drift_duration = float(car["drift_duration"] or 0.1)
                race_time = car["time_seconds"] + race_time_buffer
                
                try:
                    run_start = time.time()
                    last_tap = time.time()
                    ebrake_state = False
                    
                    while self.tracker.is_running:
                        now = time.time()
                        elapsed = now - run_start
                        if elapsed >= race_time:
                            with self.tracker.lock:
                                self.tracker.run_count += 1
                                self.tracker.accumulated_cr += car["cr"]
                                self.tracker.accumulated_xp += car["xp"]
                                self.tracker.accumulated_skillpoints += car["skillpoints"]
                            run_start = now
                            elapsed = 0.0
                            
                        self.tracker.update(
                            phase="Drift Active",
                            description=f"Drifting {car['name']} (E-Brake: {'ON' if ebrake_state else 'OFF'})",
                            time_left=max(0.0, race_time - elapsed),
                            progress=min(1.0, elapsed / race_time)
                        )
                        
                        since_last_tap = now - last_tap
                        if not ebrake_state:
                            if since_last_tap >= drift_interval:
                                gamepad.press_button(button=ebrake_button)
                                gamepad.update()
                                ebrake_state = True
                                last_tap = now
                        else:
                            if since_last_tap >= drift_duration:
                                gamepad.release_button(button=ebrake_button)
                                gamepad.update()
                                ebrake_state = False
                                last_tap = now
                                
                        time.sleep(0.02)
                finally:
                    apply_accelerate(gamepad, accelerate_control, 0.0)
                    gamepad.release_button(button=ebrake_button)
                    gamepad.update()
                    
            self.tracker.update(is_running=False, phase="Finished", description="AutoDrive loop completed.")
        except Exception as e:
            self.tracker.update(is_running=False, phase="Error", error_msg=str(e), description=f"Error: {e}")
        finally:
            if gamepad is not None:
                try:
                    gamepad.reset()
                    gamepad.update()
                    del gamepad
                except Exception:
                    pass
