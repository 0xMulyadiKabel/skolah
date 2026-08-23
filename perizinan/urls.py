from django.urls import path

from . import views

app_name = "perizinan"

urlpatterns = [
    path("", views.izin_list, name="izin_list"),
    path("<int:pk>/", views.izin_detail, name="izin_detail"),
    path("<int:pk>/setujui/", views.izin_setujui, name="izin_setujui"),
    path("<int:pk>/tolak/", views.izin_tolak, name="izin_tolak"),
]