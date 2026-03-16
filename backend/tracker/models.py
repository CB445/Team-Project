import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class ServiceUser(models.Model):
    """Core healthcare service user record managed by care staff."""

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"
        PREFER_NOT_TO_SAY = "prefer_not_to_say", "Prefer not to say"

    class RiskLevel(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class MobilityStatus(models.TextChoices):
        INDEPENDENT = "independent", "Independent"
        ASSISTED = "assisted", "Assisted"
        WHEELCHAIR = "wheelchair", "Wheelchair"

    unique_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, default=Gender.PREFER_NOT_TO_SAY)
    room_number = models.CharField(max_length=20)
    care_plan = models.TextField(blank=True)
    medical_condition = models.TextField(help_text="Examples: dementia, learning disability, fall risk")
    risk_level = models.CharField(max_length=20, choices=RiskLevel.choices, default=RiskLevel.LOW)
    allergies = models.TextField(blank=True)
    medication_notes = models.TextField(blank=True)
    hobbies = models.TextField(blank=True)
    interests = models.TextField(blank=True)
    favourite_activities = models.TextField(blank=True)
    mobility_status = models.CharField(max_length=20, choices=MobilityStatus.choices, default=MobilityStatus.INDEPENDENT)
    emergency_contact_name = models.CharField(max_length=150)
    emergency_contact_phone = models.CharField(max_length=20)
    family_member_name = models.CharField(max_length=150, blank=True)
    family_member_contact = models.CharField(max_length=20, blank=True)
    admission_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["room_number"]),
            models.Index(fields=["risk_level"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.room_number})"


class WristbandDevice(models.Model):
    """Bluetooth wristband metadata and current detector state."""

    class MovementStatus(models.TextChoices):
        MOVING = "moving", "Moving"
        STATIONARY = "stationary", "Stationary"

    class ConnectionStatus(models.TextChoices):
        CONNECTED = "connected", "Connected"
        DISCONNECTED = "disconnected", "Disconnected"
        INTERMITTENT = "intermittent", "Intermittent"

    device_id = models.CharField(primary_key=True, max_length=64)
    service_user = models.OneToOneField(
        ServiceUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wristband_device",
    )
    bluetooth_mac_address = models.CharField(max_length=17, unique=True)
    rfid_uid = models.CharField(max_length=64, unique=True, null=True, blank=True)
    wristband_serial_number = models.CharField(max_length=100, unique=True)
    battery_level = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Battery level percentage (0-100)",
    )
    signal_strength = models.IntegerField(help_text="RSSI value in dBm")
    detector_sensor_id = models.CharField(max_length=64)
    current_location = models.CharField(max_length=150)
    previous_location = models.CharField(max_length=150, blank=True)
    movement_status = models.CharField(max_length=20, choices=MovementStatus.choices, default=MovementStatus.STATIONARY)
    last_detected_time = models.DateTimeField(default=timezone.now)
    connection_status = models.CharField(max_length=20, choices=ConnectionStatus.choices, default=ConnectionStatus.CONNECTED)
    firmware_version = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["device_id"]
        indexes = [
            models.Index(fields=["current_location"]),
            models.Index(fields=["last_detected_time"]),
            models.Index(fields=["connection_status"]),
        ]

    def __str__(self):
        return f"{self.device_id} - {self.bluetooth_mac_address}"


class LocationLog(models.Model):
    """Historical movement and detector event log for analytics and auditing."""

    service_user = models.ForeignKey(ServiceUser, on_delete=models.CASCADE, related_name="location_logs")
    wristband_device = models.ForeignKey(WristbandDevice, on_delete=models.CASCADE, related_name="location_logs")
    detector_location = models.CharField(max_length=150)
    timestamp = models.DateTimeField(default=timezone.now)
    signal_strength = models.IntegerField(help_text="RSSI value in dBm")
    movement_detected = models.BooleanField(default=False)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["timestamp"]),
            models.Index(fields=["detector_location"]),
            models.Index(fields=["service_user", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.service_user} @ {self.detector_location} ({self.timestamp:%Y-%m-%d %H:%M:%S})"