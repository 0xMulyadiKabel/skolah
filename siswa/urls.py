# Simpan sebagai: siswa/urls.py

from django.urls import path

from . import views

app_name = "siswa"

urlpatterns = [
    path("", views.beranda, name="beranda"),
    path("absen/", views.absen, name="absen"),
    path("absen/submit/", views.absen_submit, name="absen_submit"),
    path("absen/sholat/<int:sesi_id>/", views.absen_sholat, name="absen_sholat"),
    path("absen/sholat/<int:sesi_id>/submit/", views.absen_sholat_submit, name="absen_sholat_submit"),
    path("halangan/", views.halangan, name="halangan"),
    path("riwayat/", views.riwayat, name="riwayat"),
    path("izin/", views.izin, name="izin"),
    path("izin/<int:pk>/edit/", views.izin_edit, name="izin_edit"),
]