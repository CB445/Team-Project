from django.db import models

# Create your models here.
from django.db import models

class Resident(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Wristband(models.Model):
    mac_address = models.CharField(max_length=17, unique=True)
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.mac_address} -> {self.resident.name}"

class DetectionEvent(models.Model):
    wristband = models.ForeignKey(Wristband, on_delete=models.CASCADE)
    location = models.CharField(max_length=100)
    rssi = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.wristband.mac_address} @ {self.location} ({self.rssi})"