from django.urls import path

from . import views

app_name = "ortu"

urlpatterns = [
    path("", views.beranda, name="beranda"),
    path("riwayat/", views.riwayat, name="riwayat"),
    path("izin/", views.izin, name="izin"),
    path("notifikasi/", views.notifikasi, name="notifikasi"),
]