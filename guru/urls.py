# Simpan sebagai: guru/urls.py

from django.urls import path

from . import views

app_name = "guru"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("koreksi/<int:siswa_id>/", views.koreksi_absensi, name="koreksi_absensi"),
    path("izin/", views.izin_list, name="izin_list"),
    path("izin/<int:pk>/setujui/", views.izin_setujui, name="izin_setujui"),
    path("izin/<int:pk>/tolak/", views.izin_tolak, name="izin_tolak"),
    path("laporan/", views.laporan, name="laporan"),
]