# Simpan sebagai: accounts/urls.py

from django.contrib.auth import views as auth_views
from django.urls import path

from .views import AdminLoginView, GuruLoginView, KioskLoginView, OrtuLoginView, SiswaLoginView, kiosk_akun_create, kiosk_akun_delete, kiosk_akun_list, kiosk_akun_reset, kiosk_pilih, pengaturan

app_name = "accounts"

urlpatterns = [
    path("login/", AdminLoginView.as_view(), name="login"),
    path("siswa/login/", SiswaLoginView.as_view(), name="siswa_login"),
    path("guru/login/", GuruLoginView.as_view(), name="guru_login"),
    path("ortu/login/", OrtuLoginView.as_view(), name="ortu_login"),
    path("kiosk/login/", KioskLoginView.as_view(), name="kiosk_login"),
    path("kiosk/pilih/", kiosk_pilih, name="kiosk_pilih"),
    path("logout/", auth_views.LogoutView.as_view(next_page="accounts:login"), name="logout"),
    path("siswa/logout/", auth_views.LogoutView.as_view(next_page="accounts:siswa_login"), name="siswa_logout"),
    path("guru/logout/", auth_views.LogoutView.as_view(next_page="accounts:guru_login"), name="guru_logout"),
    path("ortu/logout/", auth_views.LogoutView.as_view(next_page="accounts:ortu_login"), name="ortu_logout"),
    path("kiosk/logout/", auth_views.LogoutView.as_view(next_page="accounts:kiosk_login"), name="kiosk_logout"),
    path("pengaturan/", pengaturan, name="pengaturan"),
    path("kiosk-akun/", kiosk_akun_list, name="kiosk_akun_list"),
    path("kiosk-akun/tambah/", kiosk_akun_create, name="kiosk_akun_create"),
    path("kiosk-akun/<int:pk>/reset/", kiosk_akun_reset, name="kiosk_akun_reset"),
    path("kiosk-akun/<int:pk>/hapus/", kiosk_akun_delete, name="kiosk_akun_delete"),
]