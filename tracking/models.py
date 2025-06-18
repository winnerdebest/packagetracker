from django.db import models

class DeliveryStatus(models.TextChoices):
    IN_TRANSIT = 'IN_TRANSIT', 'In Transit'
    DELAYED = 'DELAYED', 'Delayed'
    DELIVERED = 'DELIVERED', 'Delivered'
    PENDING = 'PENDING', 'Pending'

class Package(models.Model):
    tracking_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING
    )

    current_city = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    # 🔽 NEW fields for destination
    destination_city = models.CharField(max_length=100, null=True)
    destination_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True )
    destination_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)

    estimated_delivery = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Package {self.tracking_number}"

class DeliveryHistory(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='history')
    city = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name_plural = "Delivery Histories"
