from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class User(AbstractUser):
    def __str__(self):
        return self.username

class Agency(models.Model):
    id = models.AutoField(primary_key=True)
    agency_id = models.CharField(unique=True, null=False, max_length=200)
    agency_name = models.CharField(null=False, max_length=200)
    agency_timezone = models.CharField(null=False, max_length=200)

    def __str__(self):
        return self.agency_name
    
    def clean(self):
        agencies = Agency.objects.filter(
            agency_name = self.agency_name
        )

        if self.pk:
            agencies = agencies.exclude(pk=self.pk)
        if agencies.exists():
            raise ValidationError("Agency already exists.")

    class Meta:
        ordering = ["agency_name"]

class Route(models.Model):
    id = models.AutoField(primary_key=True)
    route_id = models.CharField(max_length=200, null=False)
    route_type = models.IntegerField(null=False)
    agency = models.ForeignKey(Agency, null=True, on_delete=models.CASCADE)
    route_short_name = models.CharField(null=True, max_length=200)
    route_long_name = models.CharField(null=True, max_length=500)
    route_color = models.CharField(null=True, max_length=6)
    route_text_color = models.CharField(null=True, max_length=6)

    def __str__(self):
        return self.route_short_name or self.route_long_name
    
    class Meta:
        ordering = ["agency", "route_short_name", "route_long_name"]

class Shape(models.Model):
    id = models.AutoField(primary_key=True)
    shape_id = models.CharField(max_length=200, null=False)
    shape_pt_lat = models.FloatField(null=False)
    shape_pt_lon = models.FloatField(null=False)
    shape_pt_sequence = models.PositiveIntegerField(null=False)
    shape_dist_traveled = models.FloatField(null=True)

    def __str__(self):
        return f"{self.shape_id} {self.shape_pt_sequence}"

    class Meta:
        ordering = ["shape_id"]

class Calendar(models.Model):
    id = models.AutoField(primary_key=True)
    service_id = models.CharField(max_length=200, null=False)
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=False)
    monday = models.CharField(max_length=1, null=False)
    tuesday = models.CharField(max_length=1, null=False)
    wednesday = models.CharField(max_length=1, null=False)
    thursday = models.CharField(max_length=1, null=False)
    friday = models.CharField(max_length=1, null=False)
    saturday = models.CharField(max_length=1, null=False)
    sunday = models.CharField(max_length=1, null=False)

    def __str__(self):
        return self.service_id
    
    class Meta:
        ordering = ["service_id"]

class CalendarDate(models.Model):
    id = models.AutoField(primary_key=True)
    service_id = models.CharField(max_length=200, null=False)
    date = models.DateField(null=False)
    exception_type = models.CharField(max_length=1, null=False)
    
    def __str__(self):
        return self.service_id
    
    class Meta:
        ordering = ["service_id"]

class Stop(models.Model):
    id = models.AutoField(primary_key=True)
    stop_id = models.CharField(max_length=200, null=False)
    stop_name = models.CharField(max_length=500, null=True)
    stop_lat = models.FloatField(null=True)
    stop_lon = models.FloatField(null=True)
    location_type = models.CharField(max_length=1, null=True)
    parent_station = models.ForeignKey('self', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.stop_id

    class Meta:
        ordering = ["stop_name"]

class Trip(models.Model):
    id = models.AutoField(primary_key=True)
    trip_id = models.CharField(max_length=200, null=False)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, null=False)
    service_id = models.CharField(null=False, max_length=200)
    direction_id = models.CharField(max_length=1, null=True)
    shape = models.CharField(max_length=200, null=True)

    def __str__(self):
        return self.trip_id

    class Meta:
        ordering = ["trip_id"]

class StopTime(models.Model):
    id = models.AutoField(primary_key=True)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, null=False)
    stop = models.ForeignKey(Stop, on_delete=models.CASCADE, null=True)
    stop_sequence = models.PositiveIntegerField(null=False)
    arrival_time = models.CharField(max_length=8, null=True)
    departure_time = models.CharField(max_length=8, null=True)

    def __str__(self):
        return f"{self.stop} {self.trip}"

    class Meta:
        ordering = ["trip", "stop_sequence"]