from django.urls import path
 
from . import views
 
app_name = "dashboard"
 
urlpatterns = [
    path("", views.index, name="index"),
    path("live-checkin/", views.live_checkin_partial, name="live_checkin_partial"),
]
