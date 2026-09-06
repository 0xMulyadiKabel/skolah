from django.contrib.auth import views as auth_views
from django.urls import path

from .views import AdminLoginView, GuruLoginView, OrtuLoginView, SiswaLoginView, pengaturan

app_name = "accounts"

urlpatterns = [
    path("login/", AdminLoginView.as_view(), name="login"),
    path("siswa/login/", SiswaLoginView.as_view(), name="siswa_login"),
    path("guru/login/", GuruLoginView.as_view(), name="guru_login"),
    path("ortu/login/", OrtuLoginView.as_view(), name="ortu_login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="accounts:login"), name="logout"),
    path("siswa/logout/", auth_views.LogoutView.as_view(next_page="accounts:siswa_login"), name="siswa_logout"),
    path("guru/logout/", auth_views.LogoutView.as_view(next_page="accounts:guru_login"), name="guru_logout"),
    path("ortu/logout/", auth_views.LogoutView.as_view(next_page="accounts:ortu_login"), name="ortu_logout"),
    path("pengaturan/", pengaturan, name="pengaturan"),
]