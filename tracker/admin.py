from django.contrib import admin

from .models import LocationLog, ServiceUser, Task, WristbandDevice


@admin.register(ServiceUser)
class ServiceUserAdmin(admin.ModelAdmin):
	list_display = (
		"unique_id",
		"first_name",
		"last_name",
		"room_number",
		"risk_level",
		"mobility_status",
		"admission_date",
		"updated_at",
	)
	search_fields = (
		"first_name",
		"last_name",
		"room_number",
		"medical_condition",
		"emergency_contact_name",
		"family_member_name",
	)
	list_filter = ("risk_level", "mobility_status", "gender", "admission_date")
	readonly_fields = ("unique_id", "created_at", "updated_at")
	date_hierarchy = "admission_date"


@admin.register(WristbandDevice)
class WristbandDeviceAdmin(admin.ModelAdmin):
	list_display = (
		"device_id",
		"service_user",
		"bluetooth_mac_address",
		"wristband_serial_number",
		"current_location",
		"movement_status",
		"connection_status",
		"battery_level",
		"last_detected_time",
	)
	search_fields = (
		"device_id",
		"bluetooth_mac_address",
		"wristband_serial_number",
		"detector_sensor_id",
		"current_location",
		"service_user__first_name",
		"service_user__last_name",
	)
	list_filter = ("movement_status", "connection_status", "current_location")
	readonly_fields = ("created_at", "updated_at")


@admin.register(LocationLog)
class LocationLogAdmin(admin.ModelAdmin):
	list_display = (
		"service_user",
		"wristband_device",
		"detector_location",
		"signal_strength",
		"movement_detected",
		"timestamp",
	)
	search_fields = (
		"detector_location",
		"service_user__first_name",
		"service_user__last_name",
		"wristband_device__device_id",
	)
	list_filter = ("movement_detected", "detector_location", "timestamp")
	date_hierarchy = "timestamp"
	autocomplete_fields = ("service_user", "wristband_device")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
	list_display = ("id", "title", "status", "is_completed", "due_date", "assigned_to", "created_at")
	search_fields = ("title", "description", "assigned_to")
	list_filter = ("status", "is_completed", "due_date", "created_at")