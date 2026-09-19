# Simpan sebagai: guru/urls.py

from django.urls import path

from . import views

app_name = "guru"

urlpatterns = [
    path("", views.beranda_pribadi, name="beranda_pribadi"),
    path("riwayat/", views.riwayat_pribadi, name="riwayat_pribadi"),
    path("izin-saya/", views.izin_pribadi, name="izin_pribadi"),
    path("izin-saya/<int:pk>/edit/", views.izin_pribadi_edit, name="izin_pribadi_edit"),

    path("kelas/", views.dashboard, name="dashboard"),
    path("koreksi/<int:siswa_id>/", views.koreksi_absensi, name="koreksi_absensi"),
    path("izin/", views.izin_list, name="izin_list"),
    path("izin/<int:pk>/setujui/", views.izin_setujui, name="izin_setujui"),
    path("izin/<int:pk>/tolak/", views.izin_tolak, name="izin_tolak"),
    path("laporan/", views.laporan, name="laporan"),
]