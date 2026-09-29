# Simpan sebagai: accounts/views.py

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
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
        return reverse_lazy("guru:beranda_pribadi")


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


def kiosk_required(view_func):
    """
    Akun Kiosk SENGAJA dibuat terpisah dari akun Admin -- device fisik di
    gerbang/musholla itu rentan diakses siapa saja, jadi kredensialnya
    tidak boleh sama dengan kredensial Admin penuh (yang bisa buka
    Pengaturan, Data Siswa, dll). Decorator ini yang jadi pagar backend-nya
    -- BUKAN sekadar nyembunyiin menu Kiosk di sisi Admin.
    """
    decorated = login_required(
        user_passes_test(lambda u: u.role == "kiosk", login_url=reverse_lazy("accounts:kiosk_login"))(view_func)
    )
    return decorated


class KioskLoginView(auth_views.LoginView):
    template_name = "registration/login_kiosk.html"

    def get_success_url(self):
        return reverse_lazy("accounts:kiosk_pilih")


@admin_required
def pengaturan(request):
    # Import di sini (bukan di atas) buat hindari circular import,
    # karena absensi/models.py juga meng-import dari accounts/models.py.
    from absensi.models import SesiSholat

    school = _get_school(request)
    sesi_list = list(SesiSholat.objects.filter(school=school).order_by("id"))

    # Buat dropdown "+ Tambah Sesi" -- cuma tampilkan jenis sholat yang
    # BELUM ada baris-nya buat sekolah ini, biar nggak bisa nambah dobel.
    sudah_ada = {s.nama_sholat for s in sesi_list}
    sesi_belum_ada = [(nilai, label) for nilai, label in SesiSholat.NamaSholat.choices if nilai not in sudah_ada]

    HARI_FIELDS = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu"]

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
                for hari in HARI_FIELDS:
                    setattr(sesi, f"aktif_{hari}", request.POST.get(f"sesi_{sesi.id}_hari_{hari}") == "on")
                sesi.save()
            messages.success(request, "Pengaturan berhasil disimpan.")
            return redirect("accounts:pengaturan")
    else:
        form = SchoolSettingsForm(instance=school)

    context = {"page_title": "Pengaturan", "form": form, "sesi_list": sesi_list, "sesi_belum_ada": sesi_belum_ada}
    return render(request, "accounts/pengaturan.html", context)


@admin_required
def sesi_sholat_tambah(request):
    from absensi.models import SesiSholat

    school = _get_school(request)
    if request.method == "POST":
        nama = request.POST.get("nama_sholat", "")
        label_map = dict(SesiSholat.NamaSholat.choices)
        if nama not in label_map:
            messages.error(request, "Jenis sholat tidak dikenali.")
        else:
            _, created = SesiSholat.objects.get_or_create(school=school, nama_sholat=nama)
            if created:
                messages.success(request, f"Sesi {label_map[nama]} ditambahkan ke daftar. Atur jam & hari aktifnya, lalu Simpan.")
            else:
                messages.info(request, f"Sesi {label_map[nama]} sudah ada di daftar.")
    return redirect("accounts:pengaturan")


@admin_required
def sesi_sholat_hapus(request, pk):
    from absensi.models import SesiSholat

    school = _get_school(request)
    sesi = get_object_or_404(SesiSholat, pk=pk, school=school)
    if request.method == "POST":
        nama = sesi.get_nama_sholat_display()
        sesi.delete()
        messages.success(request, f"Sesi {nama} dihapus dari daftar yang dipantau.")
    return redirect("accounts:pengaturan")


@kiosk_required
def kiosk_pilih(request):
    return render(request, "registration/kiosk_pilih.html", {"page_title": "Pilih Mode Kiosk"})


# ================= KELOLA AKUN KIOSK (ADMIN) =================
# Sengaja dipisah dari halaman Pengaturan biasa -- device Kiosk itu benda
# fisik yang bisa dipegang siapa saja, jadi manajemen kredensialnya jangan
# nyampur visual sama pengaturan sensitif lain (jam sekolah, radius, dst).

@admin_required
def kiosk_akun_list(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    school = _get_school(request)
    kiosk_list = User.objects.filter(school=school, role=User.Role.KIOSK).order_by("username")
    return render(request, "accounts/kiosk_akun_list.html", {"page_title": "Akun Kiosk", "kiosk_list": kiosk_list})


@admin_required
def kiosk_akun_create(request):
    from django.contrib.auth import get_user_model
    from django.utils.crypto import get_random_string
    User = get_user_model()
    school = _get_school(request)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        if not username:
            messages.error(request, "Username wajib diisi.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' sudah dipakai.")
        else:
            temp_password = get_random_string(8)
            User.objects.create_user(username=username, password=temp_password, role=User.Role.KIOSK, school=school)
            messages.success(request, f"Akun kiosk '{username}' dibuat. Password: {temp_password} (login sekali di device, biarkan tetap masuk).")
    return redirect("accounts:kiosk_akun_list")


@admin_required
def kiosk_akun_reset(request, pk):
    from django.contrib.auth import get_user_model
    from django.utils.crypto import get_random_string
    User = get_user_model()
    school = _get_school(request)
    akun = get_object_or_404(User, pk=pk, school=school, role=User.Role.KIOSK)

    if request.method == "POST":
        temp_password = get_random_string(8)
        akun.set_password(temp_password)
        akun.save()
        messages.success(request, f"Kata sandi kiosk '{akun.username}' direset jadi: {temp_password}")
    return redirect("accounts:kiosk_akun_list")


@admin_required
def kiosk_akun_delete(request, pk):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    school = _get_school(request)
    akun = get_object_or_404(User, pk=pk, school=school, role=User.Role.KIOSK)

    if request.method == "POST":
        username = akun.username
        akun.delete()
        messages.success(request, f"Akun kiosk '{username}' dihapus.")
    return redirect("accounts:kiosk_akun_list")