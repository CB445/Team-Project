import asyncio
import socket
import requests
from datetime import datetime
from bleak import BleakScanner

# RFID hardware check
try:
    from mfrc522 import SimpleMFRC522
    HAS_RFID = True
except ImportError:
    HAS_RFID = False


# Change this to the laptop IP running Django
API_URL = "http://192.168.1.104:8000/api/location/"

# Automatically detect which Pi is running the script
NODE_NAME = socket.gethostname()
SCANNER_ID = NODE_NAME

# Memory for filtering weak repeated detections
STABLE_DETECTIONS = {}

# Registered BLE/RFID devices
KNOWN_DEVICES = {
    "4A:B3:0F:8F:76:86": {
        "service_user": "John Smith",
        "wristband": "WB001",
        "type": "BLE"
    },

    "6C:7E:F7:E8:13:38": {
        "service_user": "Jane Smith",
        "wristband": "WB002",
        "type": "BLE"
    },

    # Replace these with real RFID tag IDs when known
    "CARD_UID_HERE": {
        "service_user": "John Smith",
        "wristband": "WB001",
        "type": "RFID"
    },

    "SECOND_UID_HERE": {
        "service_user": "Jane Smith",
        "wristband": "WB002",
        "type": "RFID"
    }
}


def calculate_meters(rssi):
    if rssi is None:
        return 0.0

    if rssi >= 0:
        return 0.1

    measured_power = -59
    environmental_factor = 3.0

    distance = 10 ** ((measured_power - rssi) / (10 * environmental_factor))
    return round(distance, 2)


def determine_location(distance):
    if distance < 2:
        return f"Node: {NODE_NAME} - Very Close"
    elif distance < 5:
        return f"Node: {NODE_NAME} - Near"
    else:
        return f"Node: {NODE_NAME} - Away"


def determine_movement(rssi):
    if rssi is None:
        return "unknown"

    return "moving" if rssi > -75 else "stationary"


def send_to_django(identifier, rssi=None, is_rfid=False):
    identifier = str(identifier).upper()
    sensor_type = "RFID" if is_rfid else "BLE"

    if identifier not in KNOWN_DEVICES:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"UNKNOWN {sensor_type} | ID: {identifier} | RSSI: {rssi}"
        )
        return

    device_info = KNOWN_DEVICES[identifier]

    if is_rfid:
        distance = 0.0
        location = f"RFID Scanner: {NODE_NAME}"
        movement = "stationary"
        rssi_value = 100
    else:
        distance = calculate_meters(rssi)

        STABLE_DETECTIONS[identifier] = STABLE_DETECTIONS.get(identifier, 0) + 1

        if distance > 30.0 and STABLE_DETECTIONS[identifier] < 2:
            print(f"--- IGNORED weak single BLE ping at {distance}m ---")
            return

        location = f"{determine_location(distance)} ({distance}m)"
        movement = determine_movement(rssi)
        rssi_value = rssi if rssi is not None else 0

    payload = {
        "service_user": device_info["service_user"],
        "location": location,
        "movement": movement,
        "wristband": device_info["wristband"],
        "rssi": rssi_value,
        "scanner_id": SCANNER_ID
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=5)

        if response.status_code in (200, 201):
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"SUCCESS: Sent {sensor_type} data | {payload}"
            )
        else:
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"API ERROR {response.status_code}: {response.text}"
            )

    except requests.exceptions.ConnectionError:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"REQUEST ERROR: Could not connect to Django at {API_URL}"
        )

    except requests.exceptions.Timeout:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            "REQUEST ERROR: Django request timed out"
        )

    except Exception as e:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"GENERAL ERROR: {e}"
        )


def ble_callback(device, adv_data):
    if adv_data.rssi is None:
        return

    send_to_django(device.address, adv_data.rssi, is_rfid=False)


async def ble_scanner():
    scanner = BleakScanner(detection_callback=ble_callback)

    try:
        await scanner.start()
        print("--- BLE Scanner Started ---")

        while True:
            await asyncio.sleep(1)

    finally:
        await scanner.stop()
        print("--- BLE Scanner Stopped ---")


async def rfid_listener():
    if not HAS_RFID:
        print("--- RFID module not installed. RFID disabled. ---")
        return

    print("--- RFID Listener Started ---")

    reader = SimpleMFRC522()
    loop = asyncio.get_event_loop()

    while True:
        try:
            tag_id, text = await loop.run_in_executor(None, reader.read)
            print(f"RFID detected: {tag_id}")
            send_to_django(str(tag_id), rssi=100, is_rfid=True)
            await asyncio.sleep(2)

        except Exception as e:
            print(f"RFID ERROR: {e}")
            await asyncio.sleep(2)


async def hardware_heartbeat():
    while True:
        await asyncio.sleep(60)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Scanner Status: ONLINE")


async def main():
    print("--- Smart Wristband Monitoring System: Gateway Node Active ---")
    print(f"--- Node Name: {NODE_NAME} ---")
    print(f"--- Sending data to Django: {API_URL} ---")

    tasks = [
        ble_scanner(),
        hardware_heartbeat()
    ]

    if HAS_RFID:
        tasks.append(rfid_listener())
    else:
        print("--- RFID not available. Running BLE only. ---")

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n--- Scanner Stopped Safely ---")