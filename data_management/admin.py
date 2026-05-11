from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Stop, StopTime, Agency, Route, Trip, Shape, Calendar, CalendarDate

admin.site.register(User, UserAdmin)
admin.site.register(Stop)
admin.site.register(StopTime)
admin.site.register(Agency)
admin.site.register(Route)
admin.site.register(Trip)
admin.site.register(Shape)
admin.site.register(Calendar)
admin.site.register(CalendarDate)
