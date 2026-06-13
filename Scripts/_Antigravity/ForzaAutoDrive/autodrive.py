import time
import threading
import vgamepad as vg
import win32gui
import win32con
import win32com.client
import win32ui
import win32process
import psutil
import ctypes
import cv2
import numpy as np
import os

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

class GameStreamer:
    def __init__(self, tracker):
        # Set process DPI awareness to prevent scaling/cut-off issues
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2) # PROCESS_PER_MONITOR_DPI_AWARE
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

        self.tracker = tracker
        self.latest_frame = None
        self.lock = threading.Lock()
        self.is_running = False
        self.thread = None
        
        # Video recording state
        self.recording = False
        self.video_writer = None
        self.run_start_time = None
        self.part_index = 1
        self.current_run_dir = None
        self.frame_size = (1280, 720)
        self.fps = 10
        self.part_start_time = 0
        
    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        
    def start_recording(self, runs_to_keep=2):
        self.cleanup_old_runs(runs_to_keep)
        
        os.makedirs("videos", exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.current_run_dir = os.path.join("videos", f"run_{timestamp}")
        os.makedirs(self.current_run_dir, exist_ok=True)
        
        self.part_index = 1
        self.run_start_time = time.time()
        self.recording = True
        self._start_new_video_part()
        
    def stop_recording(self):
        self.recording = False
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            
    def _start_new_video_part(self):
        if self.video_writer:
            self.video_writer.release()
            
        filename = os.path.join(self.current_run_dir, f"part_{self.part_index:03d}.mp4")
        self.part_index += 1
        self.part_start_time = time.time()
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(filename, fourcc, self.fps, self.frame_size)
        
    def cleanup_old_runs(self, keep_count):
        if not os.path.exists("videos"):
            return
        run_dirs = []
        for name in os.listdir("videos"):
            p = os.path.join("videos", name)
            if os.path.isdir(p) and name.startswith("run_"):
                run_dirs.append((p, os.path.getmtime(p)))
                
        run_dirs.sort(key=lambda x: x[1])
        
        target_count = max(0, keep_count - 1)
        if len(run_dirs) > target_count:
            to_delete = run_dirs[:len(run_dirs) - target_count]
            for p, _ in to_delete:
                try:
                    import shutil
                    shutil.rmtree(p)
                    print(f"Deleted old video run: {p}")
                except Exception as e:
                    print(f"Error deleting run folder {p}: {e}")

    def _capture_loop(self):
        while self.is_running:
            frame = self._capture_window()
            if frame is not None:
                frame_with_overlay = self._add_overlay(frame)
                with self.lock:
                    self.latest_frame = frame_with_overlay
                if self.recording and self.video_writer:
                    elapsed = time.time() - self.part_start_time
                    if elapsed >= 3600:
                        self._start_new_video_part()
                    self.video_writer.write(frame_with_overlay)
            else:
                standby = self._create_standby_frame()
                with self.lock:
                    self.latest_frame = standby
            time.sleep(1.0 / self.fps)
            
    def _capture_window(self):
        hwnd = self._get_game_hwnd("forzahorizon6.exe")
        if not hwnd:
            return None
        try:
            left, top, right, bottom = win32gui.GetClientRect(hwnd)
            w = right - left
            h = bottom - top
            if w <= 0 or h <= 0:
                return None
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
            saveDC.SelectObject(saveBitMap)
            result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            img = np.frombuffer(bmpstr, dtype='uint8')
            img.shape = (bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            img = cv2.resize(img, self.frame_size)
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)
            return img
        except Exception:
            return None
            
    def _get_game_hwnd(self, process_name="forzahorizon6.exe"):
        hwnd_found = []
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    proc = psutil.Process(pid)
                    if proc.name().lower() == process_name.lower():
                        hwnd_found.append(hwnd)
                except Exception:
                    pass
            return True
        win32gui.EnumWindows(callback, None)
        return hwnd_found[0] if hwnd_found else None
        
    def _add_overlay(self, frame):
        snap = self.tracker.get_snapshot()
        phase = snap.get("phase", "Idle")
        desc = snap.get("description", "")
        text = f"{phase}"
        if desc and desc != "Idle" and desc != "Starting up...":
            text += f" - {desc}"
        img = frame.copy()
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.65
        thickness = 2
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        text_w, text_h = text_size
        margin = 15
        box_left = self.frame_size[0] - text_w - 2 * margin
        box_top = margin
        box_right = self.frame_size[0] - margin
        box_bottom = margin + text_h + 2 * margin
        overlay = img.copy()
        cv2.rectangle(overlay, (box_left, box_top), (box_right, box_bottom), (16, 11, 10), -1)
        cv2.rectangle(overlay, (box_left, box_top), (box_right, box_bottom), (212, 182, 6), 1)
        alpha = 0.8
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
        cv2.putText(img, text, (box_left + margin, box_bottom - margin), font, font_scale, (246, 244, 243), thickness, cv2.LINE_AA)
        return img
        
    def _create_standby_frame(self):
        img = np.zeros((self.frame_size[1], self.frame_size[0], 3), dtype=np.uint8)
        for y in range(self.frame_size[1]):
            factor = y / self.frame_size[1]
            img[y, :] = [
                int(16 * (1 - factor) + 33 * factor),
                int(11 * (1 - factor) + 20 * factor),
                int(10 * (1 - factor) + 18 * factor)
            ]
        text = "GAME STREAM STANDBY"
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, text, (400, 360), font, 1.0, (212, 182, 6), 2, cv2.LINE_AA)
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(img, ts, (520, 400), font, 0.5, (150, 150, 150), 1, cv2.LINE_AA)
        return img


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
    def __init__(self, tracker, streamer=None):
        self.tracker = tracker
        self.streamer = streamer
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
        if self.streamer:
            try:
                keep_runs = int(settings.get("video_runs_to_keep", "2"))
            except ValueError:
                keep_runs = 2
            self.streamer.start_recording(runs_to_keep=keep_runs)
            
        self.thread = threading.Thread(
            target=self._run,
            args=(track, car, start_seq, post_seq, settings),
            daemon=True
        )
        self.thread.start()
        
    def stop(self):
        self.tracker.update(is_running=False, phase="Stopping", description="Stopping virtual controller...")
        if self.streamer:
            self.streamer.stop_recording()
        
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
                is_first_loop = True
                while self.tracker.is_running:
                    # Phase 0: AutoDrive Activation (Only on first run)
                    if autodrive_activation_enabled and is_first_loop:
                        if not self.tracker.is_running:
                            return
                        self.tracker.update(phase="AutoDrive Activation", description="Pressing ANNA (D-Pad Down)", progress=0.0)
                        press_btn(gamepad, "ROLE_ANNA", settings)
                        time.sleep(0.5)
                        
                        if not self.tracker.is_running:
                            return
                        self.tracker.update(phase="AutoDrive Activation", description="Pressing AutoDrive (D-Pad Left)", progress=0.33)
                        press_btn(gamepad, "ROLE_AUTODRIVE", settings)
                        time.sleep(0.5)
                        
                        if not self.tracker.is_running:
                            return
                        self.tracker.update(phase="AutoDrive Activation", description="Waiting 1s before default sequence...", progress=0.66)
                        time.sleep(1.0)
                        is_first_loop = False

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
                    try:
                        import db
                        db.add_history_record(track["id"], car["id"], car["cr"], car["xp"], car["skillpoints"])
                    except Exception as e:
                        print(f"Error logging run to history: {e}")
                    for step in post_seq:
                        if not self.tracker.is_running:
                            return
                        self.tracker.update(description=f"Post-Race: {step['label']}", progress=0.0)
                        execute_step(gamepad, step, settings)
                        
                        delay = step["delay"]
                        if delay > 0:
                            wait_first = min(delay, 1.0)
                            steps_first = int(wait_first * 10)
                            for i in range(steps_first):
                                if not self.tracker.is_running:
                                    return
                                time.sleep(0.1)
                                self.tracker.update(time_left=max(0.0, delay - (i / 10.0)), progress=(i / (delay * 10.0)))
                            
                            remaining_delay = delay - wait_first
                            if remaining_delay > 0:
                                ebrake_control = settings.get("control_EBRAKE", "A_BTN")
                                ebrake_btn = BUTTON_MAP.get(ebrake_control, vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
                                
                                gamepad.press_button(button=ebrake_btn)
                                gamepad.left_trigger_float(1.0)
                                gamepad.update()
                                
                                steps_hold = int(remaining_delay * 10)
                                try:
                                    for i in range(steps_hold):
                                        if not self.tracker.is_running:
                                            break
                                        time.sleep(0.1)
                                        current_elapsed = wait_first + (i / 10.0)
                                        self.tracker.update(
                                            time_left=max(0.0, delay - current_elapsed),
                                            progress=(current_elapsed / delay)
                                        )
                                finally:
                                    gamepad.release_button(button=ebrake_btn)
                                    gamepad.left_trigger_float(0.0)
                                    gamepad.update()
                                
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
                        try:
                            import db
                            db.add_history_record(track["id"], car["id"], car["cr"], car["xp"], car["skillpoints"])
                        except Exception as e:
                            print(f"Error logging run to history: {e}")
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
                            try:
                                import db
                                db.add_history_record(track["id"], car["id"], car["cr"], car["xp"], car["skillpoints"])
                            except Exception as e:
                                print(f"Error logging run to history: {e}")
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
            if self.streamer:
                self.streamer.stop_recording()
            if gamepad is not None:
                try:
                    gamepad.reset()
                    gamepad.update()
                    del gamepad
                except Exception:
                    pass
