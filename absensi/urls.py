from django.urls import path

from . import views

app_name = "absensi"

urlpatterns = [
    path("laporan/", views.laporan_sekolah, name="laporan_sekolah"),
    path("laporan/export/", views.laporan_export_csv, name="laporan_export_csv"),
    path("gerbang/", views.gerbang_qr, name="gerbang_qr"),
    path("gerbang/qr.png", views.gerbang_qr_image, name="gerbang_qr_image"),
]