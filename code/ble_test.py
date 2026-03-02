import asyncio
from bleak import BleakScanner

async def main():
    print("Scanning for BLE devices (10 seconds)...\n")

    def callback(device, adv_data):
        name = adv_data.local_name or device.name or "Unknown"
        print(f"{device.address} | {adv_data.rssi} dBm | {name}")

    scanner = BleakScanner(detection_callback=callback)

    await scanner.start()
    await asyncio.sleep(10)
    await scanner.stop()

asyncio.run(main())
