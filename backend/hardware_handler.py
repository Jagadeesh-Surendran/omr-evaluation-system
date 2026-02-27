import serial
import threading
import time
import json
import traceback

class OMRHardwareHandler:
    def __init__(self, callback=None):
        self.port = None
        self.baudrate = 9600
        self.serial_conn = None
        self.running = False
        self.thread = None
        self.callback = callback  # Function to call when data is received
        self.simulating = False

    def connect(self, port, baudrate=9600):
        """Connect to the physical OMR machine."""
        try:
            self.port = port
            self.baudrate = baudrate
            self.serial_conn = serial.Serial(port, baudrate, timeout=1)
            self.running = True
            self.thread = threading.Thread(target=self._listen, daemon=True)
            self.thread.start()
            print(f"[Hardware] Connected to OMR Machine on {port}")
            return True, "Connected"
        except Exception as e:
            print(f"[Hardware] Connection failed: {e}")
            return False, str(e)

    def disconnect(self):
        """Stop listening and close the port."""
        self.running = False
        if self.serial_conn:
            self.serial_conn.close()
        self.simulating = False
        print("[Hardware] Disconnected")

    def _listen(self):
        """Background thread to listen for serial data."""
        while self.running:
            try:
                if self.serial_conn and self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode('utf-8').strip()
                    if line:
                        print(f"[Hardware] Raw Data Received: {line}")
                        parsed_data = self._parse_line(line)
                        if parsed_data and self.callback:
                            self.callback(parsed_data)
                time.sleep(0.1)
            except Exception as e:
                print(f"[Hardware] Read error: {e}")
                time.sleep(1)

    def _parse_line(self, line):
        """
        Generic parser for OMR data strings. 
        Expects something like: ROLL_NUMBER,A,B,C,D...
        Or a custom format based on common OMR protocols.
        """
        try:
            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 2:
                return None
            
            student_id = parts[0]
            answers = parts[1:] # Remaining parts are answers
            
            # Map to standard result format
            question_details = []
            for i, ans in enumerate(answers):
                question_details.append({
                    "question_number": i + 1,
                    "marked_answer": ans.upper(),
                    "correct_answer": "?", # To be filled by backend logic
                    "is_correct": False
                })
                
            return {
                "student_id": student_id,
                "question_details": question_details,
                "source": "HARDWARE"
            }
        except Exception as e:
            print(f"[Hardware] Parse error: {e}")
            return None

    def start_simulation(self):
        """Simulation mode if no hardware is connected."""
        self.simulating = True
        self.running = True
        self.thread = threading.Thread(target=self._simulate_behavior, daemon=True)
        self.thread.start()
        print("[Hardware] Simulation Started")

    def _simulate_behavior(self):
        """Mocks a sheet being fed every 15 seconds."""
        mock_sets = [
            "1001,A,B,C,D,E,A,B,C,D,E",
            "1002,B,C,D,E,A,B,C,D,E,A",
            "1003,C,D,E,A,B,C,D,E,A,B"
        ]
        import random
        while self.simulating:
            time.sleep(10) # Wait 10 seconds between mock sheets
            if not self.simulating: break
            
            line = random.choice(mock_sets)
            print(f"[Hardware] [Sim] Feeding Mock Sheet: {line}")
            parsed = self._parse_line(line)
            if parsed and self.callback:
                self.callback(parsed)
