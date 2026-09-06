from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import SchoolSettingsForm
from .models import School


def admin_required(view_func):
    """
    Decorator: cuma izinkan user dengan role='admin' yang bisa akses view ini.
    Dipakai di SEMUA view halaman Admin -- ini pertahanan di level backend,
    bukan cuma sembunyikan menu di UI (yang bisa diakali kalau cuma
    sembunyi-sembunyian di frontend).
    """
    decorated = login_required(
        user_passes_test(lambda u: u.role == "admin", login_url=reverse_lazy("accounts:login"))(view_func)
    )
    return decorated


class AdminLoginView(auth_views.LoginView):
    template_name = "registration/login.html"

    def get_success_url(self):
        return reverse_lazy("dashboard:index")


def _get_school(request):
    return request.user.school or School.objects.first()


def siswa_required(view_func):
    """Sama seperti admin_required, tapi khusus role='siswa'. Redirect ke
    halaman login siswa (bukan login admin) kalau belum login/role salah."""
    decorated = login_required(
        user_passes_test(lambda u: u.role == "siswa", login_url=reverse_lazy("accounts:siswa_login"))(view_func)
    )
    return decorated


class SiswaLoginView(auth_views.LoginView):
    template_name = "registration/login_siswa.html"

    def get_success_url(self):
        return reverse_lazy("siswa:beranda")


def guru_required(view_func):
    """Sama seperti admin_required/siswa_required, khusus role='guru'."""
    decorated = login_required(
        user_passes_test(lambda u: u.role == "guru", login_url=reverse_lazy("accounts:guru_login"))(view_func)
    )
    return decorated


class GuruLoginView(auth_views.LoginView):
    template_name = "registration/login_guru.html"

    def get_success_url(self):
        return reverse_lazy("guru:dashboard")


def ortu_required(view_func):
    """Sama seperti decorator lain, khusus role='orang_tua'."""
    decorated = login_required(
        user_passes_test(lambda u: u.role == "orang_tua", login_url=reverse_lazy("accounts:ortu_login"))(view_func)
    )
    return decorated


class OrtuLoginView(auth_views.LoginView):
    template_name = "registration/login_ortu.html"

    def get_success_url(self):
        return reverse_lazy("ortu:beranda")


@admin_required
def pengaturan(request):
    # Import di sini (bukan di atas) buat hindari circular import,
    # karena absensi/models.py juga meng-import dari accounts/models.py.
    from absensi.models import SesiSholat

    school = _get_school(request)
    sesi_list = list(SesiSholat.objects.filter(school=school).order_by("id"))

    if request.method == "POST":
        form = SchoolSettingsForm(request.POST, instance=school)
        if form.is_valid():
            form.save()
            for sesi in sesi_list:
                sesi.aktif = request.POST.get(f"sesi_{sesi.id}_aktif") == "on"
                mulai = request.POST.get(f"sesi_{sesi.id}_mulai") or None
                selesai = request.POST.get(f"sesi_{sesi.id}_selesai") or None
                sesi.jendela_mulai = mulai
                sesi.jendela_selesai = selesai
                sesi.save()
            messages.success(request, "Pengaturan berhasil disimpan.")
            return redirect("accounts:pengaturan")
    else:
        form = SchoolSettingsForm(instance=school)

    context = {"page_title": "Pengaturan", "form": form, "sesi_list": sesi_list}
    return render(request, "accounts/pengaturan.html", context)