from django.contrib.auth import views as auth_views
from django.urls import path

from .views import AdminLoginView, pengaturan

app_name = "accounts"

urlpatterns = [
    path("login/", AdminLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="accounts:login"), name="logout"),
    path("pengaturan/", pengaturan, name="pengaturan"),
]