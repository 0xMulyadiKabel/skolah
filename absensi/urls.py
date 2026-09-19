# Simpan sebagai: absensi/urls.py

from django.urls import path

from . import views

app_name = "absensi"

urlpatterns = [
    path("laporan/", views.laporan_sekolah, name="laporan_sekolah"),
    path("laporan/export/", views.laporan_export_csv, name="laporan_export_csv"),
    path("hari-libur/", views.hari_libur_list, name="hari_libur_list"),
    path("hari-libur/tambah/", views.hari_libur_create, name="hari_libur_create"),
    path("hari-libur/<int:pk>/hapus/", views.hari_libur_delete, name="hari_libur_delete"),
    path("kiosk/gerbang/", views.kiosk_gerbang, name="kiosk_gerbang"),
    path("kiosk/gerbang/submit/", views.kiosk_gerbang_submit, name="kiosk_gerbang_submit"),
    path("kiosk/sholat/", views.kiosk_sholat, name="kiosk_sholat"),
    path("kiosk/sholat/submit/", views.kiosk_sholat_submit, name="kiosk_sholat_submit"),
]