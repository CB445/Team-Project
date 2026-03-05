from __future__ import annotations

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from tracker.models import LocationLog, ServiceUser, WristbandDevice

SEED_PREFIX = "[SEED_DATA]"
SEED_COUNT = 25
LOGS_PER_DEVICE = 18

FIRST_NAMES = [
    "Margaret",
    "John",
    "Dorothy",
    "Peter",
    "Sheila",
    "Brian",
    "Eileen",
    "David",
    "Patricia",
    "Alan",
    "June",
    "Michael",
    "Brenda",
    "Terence",
    "Irene",
    "Anthony",
    "Jean",
    "Paul",
    "Maureen",
    "Graham",
    "Barbara",
    "Kenneth",
    "Susan",
    "Robert",
    "Carol",
    "Angela",
    "Colin",
    "Linda",
    "Frances",
    "Trevor",
]

LAST_NAMES = [
    "Thompson",
    "Walker",
    "Hughes",
    "Bennett",
    "Khan",
    "Fletcher",
    "Morris",
    "Roberts",
    "Shaw",
    "Ali",
    "Price",
    "Bell",
    "Wright",
    "Murphy",
    "Wood",
    "Baker",
    "Ward",
    "Cooper",
    "Carter",
    "Turner",
    "Cook",
    "Hill",
    "Bailey",
    "Brooks",
    "Powell",
    "Russell",
]

CARE_PLANS = [
    "Daily blood pressure monitoring and supervised evening medication.",
    "Falls prevention plan with hourly mobility checks.",
    "Memory support routine with orientation prompts at mealtimes.",
    "Diabetes care plan with glucose checks before meals.",
    "Post-stroke rehabilitation support and assisted transfers.",
    "Hydration and nutrition support with fortified meal reminders.",
    "Night-time reassurance rounds every 2 hours.",
    "Respiratory care observations and inhaler support.",
]

MEDICAL_CONDITIONS = [
    "Mild dementia",
    "Type 2 diabetes",
    "Arthritis",
    "Hypertension",
    "COPD",
    "Parkinson's disease",
    "Post-stroke weakness",
    "Fall risk",
    "Visual impairment",
    "Anxiety",
]

HOBBIES = [
    "Knitting",
    "Gardening",
    "Listening to jazz",
    "Puzzle books",
    "Bingo",
    "Painting",
    "Reading history",
    "Walking club",
    "Choir sessions",
    "Board games",
]

LOCATIONS = [
    "Dining Hall",
    "Bedroom",
    "Garden",
    "Nurse Station",
    "Activity Room",
    "Bathroom",
]


class Command(BaseCommand):
    help = "Seed realistic care-home service users, wristbands, and movement logs."

    def handle(self, *args, **options):
        random_gen = random.Random(20260305)
        created_users = 0
        created_devices = 0
        created_logs = 0

        with transaction.atomic():
            service_users = []
            for index in range(1, SEED_COUNT + 1):
                service_user, was_created = self._upsert_service_user(index=index, random_gen=random_gen)
                service_users.append(service_user)
                if was_created:
                    created_users += 1

            for index, service_user in enumerate(service_users, start=1):
                _, was_created = self._upsert_wristband(index=index, service_user=service_user, random_gen=random_gen)
                if was_created:
                    created_devices += 1

            for service_user in service_users:
                created_logs += self._regenerate_logs(service_user=service_user, random_gen=random_gen)

        self.stdout.write(self.style.SUCCESS("Seeding complete."))
        self.stdout.write(
            self.style.SUCCESS(
                f"Service users total={SEED_COUNT}, created={created_users}; "
                f"wristbands linked/created={SEED_COUNT}/{created_devices}; "
                f"location logs generated={created_logs}."
            )
        )

    def _upsert_service_user(self, index: int, random_gen: random.Random):
        marker = f"{SEED_PREFIX} SU{index:03d}"
        matches = list(ServiceUser.objects.filter(notes__startswith=marker).order_by("created_at", "unique_id"))
        existing = matches[0] if matches else None

        for duplicate in matches[1:]:
            # Keep the earliest seeded resident for this key and remove accidental duplicates.
            duplicate.delete()

        age = random_gen.randint(67, 96)
        days_offset = random_gen.randint(0, 364)
        today = timezone.localdate()
        date_of_birth = today - timedelta(days=(age * 365) + days_offset)
        admission_date = today - timedelta(days=random_gen.randint(10, 1200))

        first_name = FIRST_NAMES[(index * 3) % len(FIRST_NAMES)]
        last_name = LAST_NAMES[(index * 5) % len(LAST_NAMES)]
        gender = random_gen.choice([choice[0] for choice in ServiceUser.Gender.choices])
        risk_level = random_gen.choices(
            population=[
                ServiceUser.RiskLevel.LOW,
                ServiceUser.RiskLevel.MEDIUM,
                ServiceUser.RiskLevel.HIGH,
                ServiceUser.RiskLevel.CRITICAL,
            ],
            weights=[35, 35, 20, 10],
            k=1,
        )[0]
        mobility_status = random_gen.choice(
            [
                ServiceUser.MobilityStatus.INDEPENDENT,
                ServiceUser.MobilityStatus.ASSISTED,
                ServiceUser.MobilityStatus.WHEELCHAIR,
            ]
        )

        data = {
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": date_of_birth,
            "age": age,
            "gender": gender,
            "room_number": f"A{100 + index}",
            "care_plan": random_gen.choice(CARE_PLANS),
            "medical_condition": ", ".join(random_gen.sample(MEDICAL_CONDITIONS, k=2)),
            "risk_level": risk_level,
            "allergies": random_gen.choice(["None", "Penicillin", "Latex", "Nuts"]),
            "medication_notes": random_gen.choice(
                [
                    "Morning and evening medication administered by nursing staff.",
                    "Medication chart reviewed weekly by GP.",
                    "Requires prompting for lunchtime medication.",
                ]
            ),
            "hobbies": ", ".join(random_gen.sample(HOBBIES, k=2)),
            "interests": random_gen.choice(["Music therapy", "Group discussions", "News hour", "Art sessions"]),
            "favourite_activities": random_gen.choice(["Gardening", "Bingo", "Reminiscence class", "Light exercise"]),
            "mobility_status": mobility_status,
            "emergency_contact_name": f"{random_gen.choice(FIRST_NAMES)} {random_gen.choice(LAST_NAMES)}",
            "emergency_contact_phone": f"07{random_gen.randint(100000000, 999999999)}",
            "family_member_name": f"{random_gen.choice(FIRST_NAMES)} {last_name}",
            "family_member_contact": f"07{random_gen.randint(100000000, 999999999)}",
            "admission_date": admission_date,
            "notes": f"{marker} - Synthetic resident profile for development/testing.",
        }

        if existing:
            for field_name, value in data.items():
                setattr(existing, field_name, value)
            existing.save()
            return existing, False

        return ServiceUser.objects.create(**data), True

    def _upsert_wristband(self, index: int, service_user: ServiceUser, random_gen: random.Random):
        mac_address = self._mac_for_index(index)
        last_seen = timezone.now() - timedelta(minutes=random_gen.randint(1, 60))

        defaults = {
            "service_user": service_user,
            "bluetooth_mac_address": mac_address,
            "wristband_serial_number": f"WB-SN-{index:05d}",
            "battery_level": random_gen.randint(45, 100),
            "signal_strength": random_gen.randint(-88, -52),
            "detector_sensor_id": f"SENSOR-{(index % 6) + 1:02d}",
            "current_location": random_gen.choice(LOCATIONS),
            "previous_location": random_gen.choice(LOCATIONS),
            "movement_status": random_gen.choice([choice[0] for choice in WristbandDevice.MovementStatus.choices]),
            "last_detected_time": last_seen,
            "connection_status": WristbandDevice.ConnectionStatus.CONNECTED,
            "firmware_version": random_gen.choice(["v1.2.0", "v1.2.1", "v1.3.0"]),
        }

        wristband, created = WristbandDevice.objects.update_or_create(
            device_id=f"WB-{index:04d}",
            defaults=defaults,
        )
        return wristband, created

    def _regenerate_logs(self, service_user: ServiceUser, random_gen: random.Random) -> int:
        wristband = service_user.wristband_device
        LocationLog.objects.filter(service_user=service_user, wristband_device=wristband).delete()

        now = timezone.now()
        logs = []
        previous_location = None

        for _ in range(LOGS_PER_DEVICE):
            minutes_ago = random_gen.randint(2, 60 * 72)
            location = random_gen.choice(LOCATIONS)
            signal_strength = random_gen.randint(-92, -46)
            timestamp = now - timedelta(minutes=minutes_ago)
            movement_detected = previous_location is not None and previous_location != location

            logs.append(
                LocationLog(
                    service_user=service_user,
                    wristband_device=wristband,
                    detector_location=location,
                    timestamp=timestamp,
                    signal_strength=signal_strength,
                    movement_detected=movement_detected,
                )
            )
            previous_location = location

        logs.sort(key=lambda item: item.timestamp)
        LocationLog.objects.bulk_create(logs)

        last_log = logs[-1]
        wristband.previous_location = logs[-2].detector_location if len(logs) > 1 else ""
        wristband.current_location = last_log.detector_location
        wristband.signal_strength = last_log.signal_strength
        wristband.last_detected_time = last_log.timestamp
        wristband.movement_status = (
            WristbandDevice.MovementStatus.MOVING
            if last_log.movement_detected
            else WristbandDevice.MovementStatus.STATIONARY
        )
        wristband.connection_status = WristbandDevice.ConnectionStatus.CONNECTED
        wristband.save(
            update_fields=[
                "previous_location",
                "current_location",
                "signal_strength",
                "last_detected_time",
                "movement_status",
                "connection_status",
                "updated_at",
            ]
        )

        return len(logs)

    @staticmethod
    def _mac_for_index(index: int) -> str:
        # 02 sets the local-administered/unicast bits for synthetic MAC addresses.
        b1 = (index * 29) % 256
        b2 = (index * 53) % 256
        b3 = (index * 71) % 256
        b4 = (index * 97) % 256
        b5 = (index * 113) % 256
        return f"02:{b1:02X}:{b2:02X}:{b3:02X}:{b4:02X}:{b5:02X}"
