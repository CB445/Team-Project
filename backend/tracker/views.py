from django.shortcuts import render

# Create your views here.
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .models import WristbandDevice, LocationLog


@csrf_exempt
def receive_detection(request):
    if request.method == "POST":
        data = json.loads(request.body)

        mac = data.get("mac_address")
        rssi = data.get("rssi")
        location = data.get("location")
        detector_id = data.get("detector_id")

        #validate incoming data 
        if not mac or rssi is None or not location or not detector_id:
            return JsonResponse({"error": "Missing required fields"}, status=400) 
        
        # signal filtering
        if rssi is not None and rssi < -95:
            return JsonResponse({"status": "signal too weak"}, status=200)


        try:
            wristband = WristbandDevice.objects.get(bluetooth_mac_address=mac)

            previous_location = wristband.current_location
            wristband.previous_location = previous_location
            wristband.current_location = location
            wristband.signal_strength = rssi
            wristband.detector_sensor_id = detector_id
            wristband.last_detected_time = timezone.now()
            wristband.save()

            if wristband.service_user:
                LocationLog.objects.create(
                    service_user=wristband.service_user,
                    wristband_device=wristband,
                    detector_location=location,
                    signal_strength=rssi,
                    timestamp=timezone.now(),
                )

            return JsonResponse({"status": "success"})

        except WristbandDevice.DoesNotExist:
            return JsonResponse({"error": "device not registered"}, status=404)

    return JsonResponse({"error": "invalid request"}, status=400)