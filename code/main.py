import asyncio
import requests
from datetime import datetime
from bleak import BleakScanner
from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()

API_URL = "http://172.20.10.13:8000/api/location/"

SCANNER_ID = "pi-01"
SCANNER_NAME = "Scanner 01"

SHOW_UNKNOWN_BLE = False

KNOWN_DEVICES = {
    "D5:A8:CE:D3:FA:9A": {
        "service_user": "John Smith",
        "wristband": "WB001",
        "type": "BLE"
    },

    "CE:69:71:EO:25:C5": {
        "service_user": "Jane Smith",
        "wristband": "WB002",
        "type": "BLE"
    },

    "1044952846010": {
        "service_user": "John Smith",
        "wristband": "WB001",
        "type": "RFID"
    },

    "975777736343": {
        "service_user": "Jane Smith",
        "wristband": "WB002",
        "type": "RFID"
    }
}


def calculate_distance(rssi):
    if rssi is None:
        return 0.0

    measured_power = -59
    environmental_factor = 3.0
    distance = 10 ** ((measured_power - rssi) / (10 * environmental_factor))
    return round(distance, 2)


def determine_location(distance):
    if distance < 2:
        return f"{SCANNER_NAME} - Very Close"
    elif distance < 5:
        return f"{SCANNER_NAME} - Near"
    return f"{SCANNER_NAME} - Far"


def determine_movement(rssi):
    if rssi is None:
        return "unknown"
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

        response = requests.post(API_URL, json=payload, timeout=5)

        if response.status_code in (200, 201):
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"✅ SUCCESS: {sensor_type} sent | ID: {identifier} | Payload: {payload}"
            )
        else:
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"❌ API ERROR {response.status_code}: {response.text}"
            )

    except requests.exceptions.ConnectionError:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"❌ REQUEST ERROR: Could not connect to Django server at {API_URL}"
        )

    except requests.exceptions.Timeout:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            "❌ REQUEST ERROR: Request to Django server timed out"
        )

    except Exception as e:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"❌ GENERAL ERROR: {e}"
        )


def ble_callback(device, adv_data):
    if adv_data.rssi is None:
        return

    post_detection(device.address, adv_data.rssi, is_rfid=False)


async def ble_scanner():
    print("--- BLE Scanner Started ---")
    scanner = BleakScanner(detection_callback=ble_callback)
    await scanner.start()

    try:
        while True:
            await asyncio.sleep(1)

    finally:
        await scanner.stop()
        print("--- BLE Scanner Stopped ---")


async def rfid_listener():
    print("--- RFID Listener Ready ---")

    last_id = None
    loop = asyncio.get_event_loop()

    while True:
        try:
            tag_id, text = await loop.run_in_executor(None, reader.read)

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


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n--- Scanner Stopped Safely ---")