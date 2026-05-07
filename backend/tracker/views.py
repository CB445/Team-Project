import json
from datetime import timedelta

from django.db.models import OuterRef, Subquery
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .forms import TaskForm, TaskStatusForm
from .models import LocationLog, ServiceUser, Task, WristbandDevice


ROOM_DISTANCE_THRESHOLD_METRES = 2.0
RFID_REDIRECT_WINDOW_SECONDS = 10

latest_rfid_scan = {
    "rfid_uid": None,
    "timestamp": None,
}


def home(request):
    return render(request, "tracker/home.html")


def task_dashboard(request):
    tasks = Task.objects.all()
    overdue_count = Task.objects.overdue().count()

    return render(request, "tracker/tasks.html", {
        "tasks": tasks,
        "overdue_count": overdue_count,
    })


def add_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("tracker:task_dashboard")
    else:
        form = TaskForm()

    return render(request, "tracker/task_form.html", {"form": form})


def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    return render(request, "tracker/task_detail.html", {"task": task})


def update_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == "POST":
        form = TaskStatusForm(request.POST, instance=task)

        if form.is_valid():
            updated_task = form.save(commit=False)
            updated_task.is_completed = updated_task.status == Task.Status.COMPLETED
            updated_task.save()

    return redirect("tracker:task_dashboard")


def task_alerts(request):
    overdue_tasks = Task.objects.overdue()
    overdue_count = overdue_tasks.count()

    return JsonResponse({
        "overdue_count": overdue_count,
        "message": f"You have {overdue_count} overdue tasks that require attention.",
        "task_ids": list(overdue_tasks.values_list("id", flat=True)),
    })


def _parse_service_user(full_name):
    name = full_name.strip()
    parts = name.split()

    if len(parts) < 2:
        return None

    first_name = parts[0]
    last_name = " ".join(parts[1:])

    return ServiceUser.objects.filter(
        first_name__iexact=first_name,
        last_name__iexact=last_name
    ).first()


def _movement_to_bool(movement):
    normalized = movement.strip().lower()

    if normalized in {"moving", "true", "1", "yes"}:
        return True

    if normalized in {"stable", "stationary", "false", "0", "no"}:
        return False

    return None


def _movement_filter_value(raw_value):
    if raw_value == "moving":
        return True

    if raw_value == "stable":
        return False

    return None


def _get_rssi(payload):
    rssi_value = (
        payload.get("rssi")
        or payload.get("RSSI")
        or payload.get("signal_strength")
        or payload.get("signalStrength")
    )

    try:
        return int(rssi_value)
    except (TypeError, ValueError):
        return 0


def _get_distance(payload):
    try:
        return float(payload.get("distance"))
    except (TypeError, ValueError):
        return None


def _determine_location_from_distance(base_location, distance):
    if distance is None:
        return base_location

    if distance <= ROOM_DISTANCE_THRESHOLD_METRES:
        return base_location

    return "Hallway"


def _filtered_logs_queryset(request):
    user_filter = request.GET.get("user", "").strip()
    location_filter = request.GET.get("location", "").strip()
    movement_filter_raw = request.GET.get("movement", "").strip()
    movement_filter = _movement_filter_value(movement_filter_raw)

    logs = LocationLog.objects.select_related("service_user", "wristband_device")

    if user_filter:
        logs = logs.filter(service_user_id=user_filter)

    if location_filter:
        logs = logs.filter(detector_location=location_filter)

    if movement_filter is not None:
        logs = logs.filter(movement_detected=movement_filter)

    return logs.order_by("-timestamp"), {
        "user": user_filter,
        "location": location_filter,
        "movement": movement_filter_raw,
        "movement_value": movement_filter,
    }


def _last_known_locations_queryset(filters):
    latest_logs = LocationLog.objects.all()

    if filters["location"]:
        latest_logs = latest_logs.filter(detector_location=filters["location"])

    if filters["movement_value"] is not None:
        latest_logs = latest_logs.filter(movement_detected=filters["movement_value"])

    last_location_subquery = (
        latest_logs.filter(service_user=OuterRef("pk"))
        .order_by("-timestamp")
        .values("detector_location")[:1]
    )

    last_time_subquery = (
        latest_logs.filter(service_user=OuterRef("pk"))
        .order_by("-timestamp")
        .values("timestamp")[:1]
    )

    last_signal_strength_subquery = (
        latest_logs.filter(service_user=OuterRef("pk"))
        .order_by("-timestamp")
        .values("signal_strength")[:1]
    )

    users = ServiceUser.objects.annotate(
        last_location=Subquery(last_location_subquery),
        last_seen=Subquery(last_time_subquery),
        last_signal_strength=Subquery(last_signal_strength_subquery),
    )

    if filters["user"]:
        users = users.filter(pk=filters["user"])

    return users.filter(last_seen__isnull=False).order_by("last_name", "first_name")


def _update_wristband_current_location(wristband, current_log, movement_detected):
    if hasattr(wristband, "previous_location"):
        wristband.previous_location = getattr(wristband, "current_location", "")

    if hasattr(wristband, "current_location"):
        wristband.current_location = current_log.detector_location

    if hasattr(wristband, "signal_strength"):
        wristband.signal_strength = current_log.signal_strength

    if hasattr(wristband, "detector_sensor_id"):
        wristband.detector_sensor_id = current_log.detector_location

    if hasattr(wristband, "movement_status"):
        wristband.movement_status = (
            WristbandDevice.MovementStatus.MOVING
            if movement_detected
            else WristbandDevice.MovementStatus.STATIONARY
        )

    if hasattr(wristband, "last_detected_time"):
        wristband.last_detected_time = timezone.now()

    if hasattr(wristband, "connection_status"):
        wristband.connection_status = WristbandDevice.ConnectionStatus.CONNECTED

    wristband.save()


def service_user_list(request):
    service_users = ServiceUser.objects.all()
    return render(request, "tracker/service_users.html", {"service_users": service_users})


def location_logs_dashboard(request):
    logs_queryset, filters = _filtered_logs_queryset(request)
    logs = logs_queryset[:30]
    last_known_locations = _last_known_locations_queryset(filters)

    service_users = ServiceUser.objects.order_by("last_name", "first_name")

    locations = (
        LocationLog.objects
        .order_by("detector_location")
        .values_list("detector_location", flat=True)
        .distinct()
    )

    return render(request, "tracker/location_logs.html", {
        "logs": logs,
        "last_known_locations": last_known_locations,
        "service_users": service_users,
        "locations": locations,
        "selected_user": filters["user"],
        "selected_location": filters["location"],
        "selected_movement": filters["movement"],
    })


def live_location_logs(request):
    logs_queryset, filters = _filtered_logs_queryset(request)
    logs = logs_queryset[:30]
    last_known_locations = _last_known_locations_queryset(filters)

    now = timezone.now()
    logs_payload = []

    for log in logs:
        is_recent = (now - log.timestamp).total_seconds() <= 300

        logs_payload.append({
            "id": log.id,
            "service_user": f"{log.service_user.first_name} {log.service_user.last_name}",
            "location": log.detector_location,
            "scanner": getattr(log.wristband_device, "detector_sensor_id", "unknown"),
            "signal_strength": log.signal_strength,
            "movement_detected": "Yes" if log.movement_detected else "No",
            "device_id": log.wristband_device.device_id,
            "timestamp": timezone.localtime(log.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
            "is_recent": is_recent,
        })

    last_known_payload = [
        {
            "service_user": f"{user.first_name} {user.last_name}",
            "location": user.last_location,
            "time": timezone.localtime(user.last_seen).strftime("%I:%M %p"),
            "signal_strength": user.last_signal_strength,
            "scanner": "known",
        }
        for user in last_known_locations
    ]

    return JsonResponse({
        "logs": logs_payload,
        "last_known_locations": last_known_payload,
        "active_filters": {
            "user": filters["user"],
            "location": filters["location"],
            "movement": filters["movement"],
        },
    })


def live_wristband_devices(request):
    wristbands = WristbandDevice.objects.select_related("service_user").all()
    now = timezone.now()
    payload = []

    for wristband in wristbands:
        last_detected = wristband.last_detected_time
        is_recent = False

        if last_detected:
            is_recent = (now - last_detected).total_seconds() <= 300

        service_user_name = "Unassigned"

        if wristband.service_user:
            service_user_name = (
                f"{wristband.service_user.first_name} "
                f"{wristband.service_user.last_name}"
            )

        payload.append({
            "device_id": wristband.device_id,
            "service_user": service_user_name,
            "current_location": getattr(wristband, "current_location", "Unknown"),
            "previous_location": getattr(wristband, "previous_location", ""),
            "movement_status": wristband.get_movement_status_display()
            if hasattr(wristband, "get_movement_status_display")
            else getattr(wristband, "movement_status", "Unknown"),
            "signal_strength": getattr(wristband, "signal_strength", 0),
            "last_detected_time": timezone.localtime(last_detected).strftime("%Y-%m-%d %H:%M:%S")
            if last_detected
            else "Never",
            "connection_status": wristband.get_connection_status_display()
            if hasattr(wristband, "get_connection_status_display")
            else getattr(wristband, "connection_status", "Unknown"),
            "is_recent": is_recent,
        })

    return JsonResponse({"wristbands": payload})


def latest_rfid_redirect(request):
    rfid_uid = latest_rfid_scan.get("rfid_uid")
    timestamp = latest_rfid_scan.get("timestamp")

    if not rfid_uid or not timestamp:
        return JsonResponse({"redirect": False})

    scan_age = (timezone.now() - timestamp).total_seconds()

    if scan_age > RFID_REDIRECT_WINDOW_SECONDS:
        return JsonResponse({"redirect": False})

    return JsonResponse({
        "redirect": True,
        "url": f"/rfid/{rfid_uid}/",
    })


@csrf_exempt
def receive_location_data(request):
    global latest_rfid_scan

    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Method not allowed. Use POST."},
            status=405
        )

    try:
        payload = json.loads(request.body.decode("utf-8"))
        print("📡 DATA RECEIVED:", payload)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON payload."},
            status=400
        )

    service_user_name = payload.get("service_user")
    location = payload.get("location")
    movement = payload.get("movement")
    wristband_id = payload.get("wristband")
    scanner_id = payload.get("scanner_id", "unknown")
    sensor_type = payload.get("sensor_type", "BLE")

    if not service_user_name or not location or not movement or not wristband_id:
        return JsonResponse(
            {"status": "error", "message": "Missing required fields"},
            status=400
        )

    service_user = _parse_service_user(service_user_name)

    if not service_user:
        return JsonResponse(
            {"status": "error", "message": "Service user not found"},
            status=400
        )

    wristband = WristbandDevice.objects.filter(
        device_id__iexact=wristband_id.strip()
    ).first()

    if not wristband:
        return JsonResponse(
            {"status": "error", "message": "Wristband not found"},
            status=400
        )

    movement_detected = _movement_to_bool(movement)

    if movement_detected is None:
        return JsonResponse(
            {"status": "error", "message": "Invalid movement value"},
            status=400
        )

    rssi = _get_rssi(payload)
    distance = _get_distance(payload)
    base_location = location.strip()

    final_location = _determine_location_from_distance(
        base_location=base_location,
        distance=distance,
    )

    if distance is not None:
        detector_location = (
            f"{final_location} - {distance:.2f}m from {base_location} ({scanner_id})"
        )
    else:
        detector_location = f"{final_location} ({scanner_id})"

    location_log = LocationLog.objects.create(
        service_user=service_user,
        wristband_device=wristband,
        detector_location=detector_location,
        movement_detected=movement_detected,
        signal_strength=rssi,
        timestamp=timezone.now()
    )

    if sensor_type == "RFID":
        latest_rfid_scan = {
            "rfid_uid": payload.get("rfid_uid") or wristband.rfid_uid,
            "timestamp": timezone.now(),
        }

    _update_wristband_current_location(
        wristband=wristband,
        current_log=location_log,
        movement_detected=movement_detected
    )

    print(
        f"✅ SAVED from {scanner_id}: {service_user_name} at {detector_location} | "
        f"RSSI {rssi} | Distance {distance}"
    )

    return JsonResponse(
        {
            "status": "success",
            "message": "Location data saved",
            "rssi": rssi,
            "distance": distance,
            "scanner_id": scanner_id,
            "sensor_type": sensor_type,
            "raw_location": detector_location,
            "current_location": wristband.current_location,
        },
        status=201
    )


def service_user_profile_by_rfid(request, rfid_uid):
    wristband = get_object_or_404(
        WristbandDevice.objects.select_related("service_user"),
        rfid_uid=rfid_uid
    )

    service_user = wristband.service_user

    return render(
        request,
        "tracker/service_user_profile.html",
        {
            "service_user": service_user,
            "wristband": wristband,
        }
    )