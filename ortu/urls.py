# Simpan sebagai: ortu/urls.py

from django.urls import path

from . import views

app_name = "ortu"

urlpatterns = [
    path("", views.beranda, name="beranda"),
    path("riwayat/", views.riwayat, name="riwayat"),
    path("izin/", views.izin, name="izin"),
    path("izin/<int:pk>/edit/", views.izin_edit, name="izin_edit"),
    path("notifikasi/", views.notifikasi, name="notifikasi"),
]