import socket
import json
import time
from picarx import Picarx

HOST = "192.168.0.138"
PORT = 65432

SPEED = 80
TURN_ANGLE = 28

METRES_PER_SEC = 0.15

px = Picarx()

car_state = {
    "direction": "stopped",
    "speed": 0,
    "distance": 0.0,
    "temperature": 0.0,
    "obstacle_dist": 0.0,
}

# Timestamp of the last call – used to measure elapsed time between messages
_last_tick = time.time()

def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return round(int(f.read().strip()) / 1000.0, 1)
    except Exception:
        return 0.0

def apply_command(cmd):
    global _last_tick

    now = time.time()
    dt = now - _last_tick
    _last_tick = now

    # Accumulate distance for however long the previous direction was held
    if car_state["direction"] != "stopped":
        car_state["distance"] = round(car_state["distance"] + METRES_PER_SEC * dt, 2)

    if cmd == "forward":
        car_state["direction"] = "forward"
        car_state["speed"] = SPEED
        px.set_dir_servo_angle(0)
        px.forward(SPEED)

    elif cmd == "backward":
        car_state["direction"] = "backward"
        car_state["speed"] = SPEED
        px.set_dir_servo_angle(0)
        px.backward(SPEED)

    elif cmd == "left":
        car_state["direction"] = "turning left"
        car_state["speed"] = SPEED
        px.set_dir_servo_angle(-TURN_ANGLE)
        px.forward(SPEED)

    elif cmd == "right":
        car_state["direction"] = "turning right"
        car_state["speed"] = SPEED
        px.set_dir_servo_angle(TURN_ANGLE)
        px.forward(SPEED)

    elif cmd == "stop":
        car_state["direction"] = "stopped"
        car_state["speed"] = 0
        px.stop()
        px.set_dir_servo_angle(0)

    # ping / unknown: just return current state, no motor change

    # Refresh sensors on every message
    car_state["temperature"] = get_cpu_temp()
    try:
        car_state["obstacle_dist"] = round(px.get_distance(), 1)
    except Exception:
        car_state["obstacle_dist"] = 0.0

    return json.dumps(car_state) + "\n"


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    print(f"Server listening on {HOST}:{PORT}")
    s.listen()

    try:
        while True:
            print("Waiting for connection...")
            conn, addr = s.accept()
            print(f"Connected: {addr}")
            buf = ""

            with conn:
                while True:
                    try:
                        chunk = conn.recv(1024).decode("utf-8", errors="ignore")
                        if not chunk:
                            print("Client disconnected")
                            break
                        buf += chunk
                        while "\n" in buf:
                            line, buf = buf.split("\n", 1)
                            line = line.strip()
                            if line:
                                print(f"Command: {line!r}")
                                conn.sendall(apply_command(line).encode("utf-8"))
                    except Exception as e:
                        print(f"Error: {e}")
                        break

            print("Stopping car after disconnect")
            px.stop()
            px.set_dir_servo_angle(0)
            car_state["direction"] = "stopped"
            car_state["speed"] = 0

    except KeyboardInterrupt:
        print("Shutting down")
        px.stop()