import asyncio
<<<<<<< Updated upstream
import socket
=======
>>>>>>> Stashed changes
import requests
from datetime import datetime
from bleak import BleakScanner
from mfrc522 import SimpleMFRC522

<<<<<<< Updated upstream
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
=======
reader = SimpleMFRC522()

API_URL = "http://172.20.10.13:8000/api/location/"

SCANNER_ID = "pi-01"
SCANNER_NAME = "Scanner 01"

SHOW_UNKNOWN_BLE = False

KNOWN_DEVICES = {
    "D5:A8:CE:D3:FA:9A": {
>>>>>>> Stashed changes
        "service_user": "John Smith",
        "wristband": "WB001",
        "type": "BLE"
    },

<<<<<<< Updated upstream
    "6C:7E:F7:E8:13:38": {
=======
    "CE:69:71:EO:25:C5": {
>>>>>>> Stashed changes
        "service_user": "Jane Smith",
        "wristband": "WB002",
        "type": "BLE"
    },

<<<<<<< Updated upstream
    # Replace these with real RFID tag IDs when known
    "CARD_UID_HERE": {
=======
    "1044952846010": {
>>>>>>> Stashed changes
        "service_user": "John Smith",
        "wristband": "WB001",
        "type": "RFID"
    },

<<<<<<< Updated upstream
    "SECOND_UID_HERE": {
=======
    "975777736343": {
>>>>>>> Stashed changes
        "service_user": "Jane Smith",
        "wristband": "WB002",
        "type": "RFID"
    }
}


<<<<<<< Updated upstream
def calculate_meters(rssi):
    if rssi is None:
        return 0.0

    if rssi >= 0:
        return 0.1

    measured_power = -59
    environmental_factor = 3.0

=======
def calculate_distance(rssi):
    if rssi is None:
        return 0.0

    measured_power = -59
    environmental_factor = 3.0
>>>>>>> Stashed changes
    distance = 10 ** ((measured_power - rssi) / (10 * environmental_factor))
    return round(distance, 2)


def determine_location(distance):
    if distance < 2:
<<<<<<< Updated upstream
        return f"Node: {NODE_NAME} - Very Close"
    elif distance < 5:
        return f"Node: {NODE_NAME} - Near"
    else:
        return f"Node: {NODE_NAME} - Away"
=======
        return f"{SCANNER_NAME} - Very Close"
    elif distance < 5:
        return f"{SCANNER_NAME} - Near"
    return f"{SCANNER_NAME} - Far"
>>>>>>> Stashed changes


def determine_movement(rssi):
    if rssi is None:
        return "unknown"
<<<<<<< Updated upstream

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
=======
    return "moving" if rssi > -75 else "stationary"


def post_detection(identifier, rssi=None, is_rfid=False):
    try:
        identifier = str(identifier).upper().strip()
        sensor_type = "RFID" if is_rfid else "BLE"

        known_devices_clean = {
            key.strip().upper(): value
            for key, value in KNOWN_DEVICES.items()
        }

        print(f"DEBUG detected ID: [{identifier}]")
        print(f"DEBUG known IDs: {list(known_devices_clean.keys())}")

        if identifier not in known_devices_clean:
            if SHOW_UNKNOWN_BLE or is_rfid:
                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] "
                    f"ALERT: Unregistered {sensor_type} device | ID: {identifier} | RSSI: {rssi}"
                )
            return

        device_info = known_devices_clean[identifier]

        if is_rfid:
            print(f"✅ Registered RFID detected: {identifier}")
            location = "RFID Scanner 01"
            movement = "stationary"
            rssi_value = 100
        else:
            print(f"✅ Registered BLE detected: {identifier} | RSSI: {rssi}")
            distance = calculate_distance(rssi)
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

>>>>>>> Stashed changes
        response = requests.post(API_URL, json=payload, timeout=5)

        if response.status_code in (200, 201):
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
<<<<<<< Updated upstream
                f"SUCCESS: Sent {sensor_type} data | {payload}"
=======
                f"✅ SUCCESS: {sensor_type} sent | ID: {identifier} | Payload: {payload}"
>>>>>>> Stashed changes
            )
        else:
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
<<<<<<< Updated upstream
                f"API ERROR {response.status_code}: {response.text}"
=======
                f"❌ API ERROR {response.status_code}: {response.text}"
>>>>>>> Stashed changes
            )

    except requests.exceptions.ConnectionError:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
<<<<<<< Updated upstream
            f"REQUEST ERROR: Could not connect to Django at {API_URL}"
=======
            f"❌ REQUEST ERROR: Could not connect to Django server at {API_URL}"
>>>>>>> Stashed changes
        )

    except requests.exceptions.Timeout:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
<<<<<<< Updated upstream
            "REQUEST ERROR: Django request timed out"
=======
            "❌ REQUEST ERROR: Request to Django server timed out"
>>>>>>> Stashed changes
        )

    except Exception as e:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
<<<<<<< Updated upstream
            f"GENERAL ERROR: {e}"
=======
            f"❌ GENERAL ERROR: {e}"
>>>>>>> Stashed changes
        )


def ble_callback(device, adv_data):
    if adv_data.rssi is None:
        return

<<<<<<< Updated upstream
    send_to_django(device.address, adv_data.rssi, is_rfid=False)


async def ble_scanner():
    scanner = BleakScanner(detection_callback=ble_callback)

    try:
        await scanner.start()
        print("--- BLE Scanner Started ---")

=======
    post_detection(device.address, adv_data.rssi, is_rfid=False)


async def ble_scanner():
    print("--- BLE Scanner Started ---")
    scanner = BleakScanner(detection_callback=ble_callback)
    await scanner.start()

    try:
>>>>>>> Stashed changes
        while True:
            await asyncio.sleep(1)

    finally:
        await scanner.stop()
        print("--- BLE Scanner Stopped ---")


async def rfid_listener():
<<<<<<< Updated upstream
    if not HAS_RFID:
        print("--- RFID module not installed. RFID disabled. ---")
        return

    print("--- RFID Listener Started ---")

    reader = SimpleMFRC522()
=======
    print("--- RFID Listener Ready ---")

    last_id = None
>>>>>>> Stashed changes
    loop = asyncio.get_event_loop()

    while True:
        try:
            tag_id, text = await loop.run_in_executor(None, reader.read)
<<<<<<< Updated upstream
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
=======

            if tag_id and tag_id != last_id:
                print(f"RFID detected: {tag_id}")
                post_detection(str(tag_id), rssi=100, is_rfid=True)
                last_id = tag_id

            await asyncio.sleep(1)

        except Exception as e:
            print(f"RFID Error: {e}")
            await asyncio.sleep(1)


async def main():
    print("--- BLE + RFID Detection System ---")
    print(f"Sending data to: {API_URL}")
    print(f"Known devices loaded: {list(KNOWN_DEVICES.keys())}")

    await asyncio.gather(
        ble_scanner(),
        rfid_listener()
    )
>>>>>>> Stashed changes


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n--- Scanner Stopped Safely ---")