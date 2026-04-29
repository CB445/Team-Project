import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .models import ServiceUser, WristbandDevice, LocationLog


@csrf_exempt
def receive_location_data(request):
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Method not allowed. Use POST."},
            status=405
        )

    try:
        data = json.loads(request.body.decode("utf-8"))

        print("📡 DATA RECEIVED:", data)

        service_user_name = data.get("service_user")
        location = data.get("location")
        movement = data.get("movement")
        wristband_id = data.get("wristband")
        scanner_id = data.get("scanner_id", "unknown")  # NEW

        # Validate input
        if not service_user_name or not location or not movement or not wristband_id:
            return JsonResponse(
                {"status": "error", "message": "Missing required fields"},
                status=400
            )

        # --- Find Service User ---
        try:
            first, last = service_user_name.strip().split(" ", 1)
            service_user = ServiceUser.objects.get(
                first_name__iexact=first,
                last_name__iexact=last
            )
        except Exception:
            return JsonResponse(
                {"status": "error", "message": "Service user not found"},
                status=400
            )

        # --- Find Wristband ---
        try:
            wristband = WristbandDevice.objects.get(
                device_id__iexact=wristband_id
            )
        except WristbandDevice.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Wristband not found"},
                status=400
            )

        # --- Convert movement ---
        movement_detected = movement.lower() in ["moving", "true", "1", "yes"]

        # --- Save log ---
        log = LocationLog.objects.create(
            service_user=service_user,
            wristband_device=wristband,
            detector_location=f"{location} ({scanner_id})",  # includes Pi ID
            movement_detected=movement_detected,
            signal_strength=0,
            timestamp=timezone.now()
        )

        print(f"✅ SAVED from {scanner_id}: {service_user_name} at {location}")

        return JsonResponse(
            {"status": "success", "message": "Location data saved"},
            status=201
        )

    except Exception as e:
        print("❌ ERROR:", str(e))
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=500
        )