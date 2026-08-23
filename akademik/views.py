from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.utils import get_school
from accounts.views import admin_required

from .forms import GuruAccountForm, GuruEditForm, KelasForm, OrangTuaAccountForm, OrangTuaEditForm, SiswaForm
from .models import Guru, Kelas, OrangTua, Siswa

User = get_user_model()


def _school_or_guard(request):
    """Kembalikan (school, None) kalau ada, atau (None, response_guard) kalau
    School belum ada sama sekali -- panggil di awal tiap view, langsung
    `return guard` kalau guard bukan None."""
    school = get_school(request)
    if school is None:
        return None, render(request, "accounts/school_missing.html", {"page_title": "Data Siswa"})
    return school, None


# ================= SISWA =================

@admin_required
def siswa_list(request):
    school, guard = _school_or_guard(request)
    if guard:
        return guard

    q = request.GET.get("q", "").strip()
    kelas_id = request.GET.get("kelas", "")

    siswa_qs = Siswa.objects.filter(school=school).select_related("kelas").order_by("nama")
    if q:
        siswa_qs = siswa_qs.filter(Q(nama__icontains=q) | Q(nis__icontains=q))
    if kelas_id:
        siswa_qs = siswa_qs.filter(kelas_id=kelas_id)

    paginator = Paginator(siswa_qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_title": "Data Siswa",
        "page_obj": page_obj,
        "kelas_list": Kelas.objects.filter(school=school).order_by("nama_kelas"),
        "q": q,
        "kelas_id_selected": str(kelas_id),
    }
    return render(request, "akademik/siswa_list.html", context)


@admin_required
def siswa_create(request):
    school, guard = _school_or_guard(request)
    if guard:
        return guard

    if request.method == "POST":
        form = SiswaForm(request.POST, school=school)
        if form.is_valid():
            siswa = form.save(commit=False)
            siswa.school = school
            siswa.save()
            messages.success(request, f"Siswa {siswa.nama} berhasil ditambahkan.")
            return redirect("akademik:siswa_list")
    else:
        form = SiswaForm(school=school)
    return render(request, "akademik/siswa_form.html", {"page_title": "Tambah Siswa", "form": form})


@admin_required
def siswa_update(request, pk):
    school, guard = _school_or_guard(request)
    if guard:
        return guard

    siswa = get_object_or_404(Siswa, pk=pk, school=school)
    if request.method == "POST":
        form = SiswaForm(request.POST, instance=siswa, school=school)
        if form.is_valid():
            form.save()
            messages.success(request, f"Data {siswa.nama} berhasil diperbarui.")
            return redirect("akademik:siswa_list")
    else:
        form = SiswaForm(instance=siswa, school=school)
    return render(request, "akademik/siswa_form.html", {"page_title": f"Edit Siswa — {siswa.nama}", "form": form, "siswa": siswa})


@admin_required
def siswa_bulk_nonaktifkan(request):
    school, guard = _school_or_guard(request)
    if guard:
        return guard

    if request.method == "POST":
        ids = request.POST.getlist("siswa_ids")
        updated = Siswa.objects.filter(school=school, pk__in=ids).update(aktif=False)
        messages.success(request, f"{updated} siswa berhasil dinonaktifkan.")
    return redirect("akademik:siswa_list")


# ================= KELAS =================

@admin_required
def kelas_list(request):
    school, guard = _school_or_guard(request)
    if guard:
        return guard
    q = request.GET.get("q", "").strip()
    kelas_qs = Kelas.objects.filter(school=school).select_related("wali_kelas").order_by("nama_kelas")
    if q:
        kelas_qs = kelas_qs.filter(Q(nama_kelas__icontains=q) | Q(wali_kelas__nama__icontains=q))
    return render(request, "akademik/kelas_list.html", {"page_title": "Kelas", "kelas_list": kelas_qs, "q": q})


@admin_required
def kelas_create(request):
    school, guard = _school_or_guard(request)
    if guard:
        return guard

    if request.method == "POST":
        form = KelasForm(request.POST, school=school)
        if form.is_valid():
            kelas = form.save(commit=False)
            kelas.school = school
            kelas.save()
            messages.success(request, f"Kelas {kelas.nama_kelas} berhasil ditambahkan.")
            return redirect("akademik:kelas_list")
    else:
        form = KelasForm(school=school)
    return render(request, "akademik/kelas_form.html", {"page_title": "Tambah Kelas", "form": form})


@admin_required
def kelas_update(request, pk):
    school, guard = _school_or_guard(request)
    if guard:
        return guard

    kelas = get_object_or_404(Kelas, pk=pk, school=school)
    if request.method == "POST":
        form = KelasForm(request.POST, instance=kelas, school=school)
        if form.is_valid():
            form.save()
            messages.success(request, f"Kelas {kelas.nama_kelas} berhasil diperbarui.")
            return redirect("akademik:kelas_list")
    else:
        form = KelasForm(instance=kelas, school=school)
    return render(request, "akademik/kelas_form.html", {"page_title": f"Edit Kelas — {kelas.nama_kelas}", "form": form})


# ================= AKUN GURU =================

@admin_required
def akun_guru_list(request):
    school, guard = _school_or_guard(request)
    if guard:
        return guard
    guru_list = Guru.objects.filter(school=school).select_related("user").prefetch_related("kelas_diampu")
    return render(request, "akademik/akun_guru_list.html", {"page_title": "Akun Guru", "guru_list": guru_list})


@admin_required
def akun_guru_create(request):
    school, guard = _school_or_guard(request)
    if guard:
        return guard

    if request.method == "POST":
        form = GuruAccountForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
                role=User.Role.GURU,
                school=school,
            )
            Guru.objects.create(school=school, user=user, nama=form.cleaned_data["nama"], email=form.cleaned_data["email"])
            messages.success(request, f"Akun guru {form.cleaned_data['nama']} berhasil dibuat.")
            return redirect("akademik:akun_guru_list")
    else:
        form = GuruAccountForm()
    return render(request, "akademik/akun_form.html", {"page_title": "Tambah Akun Guru", "form": form})


@admin_required
def akun_guru_edit(request, pk):
    guru = get_object_or_404(Guru, pk=pk, school=get_school(request))
    if request.method == "POST":
        form = GuruEditForm(request.POST, instance=guru)
        if form.is_valid():
            form.save()
            messages.success(request, f"Data {guru.nama} berhasil diperbarui.")
            return redirect("akademik:akun_guru_list")
    else:
        form = GuruEditForm(instance=guru)
    return render(request, "akademik/akun_form.html", {"page_title": f"Edit Akun Guru — {guru.nama}", "form": form})


@admin_required
def akun_guru_reset(request, pk):
    from django.utils.crypto import get_random_string
    guru = get_object_or_404(Guru, pk=pk, school=get_school(request))
    if request.method == "POST":
        temp_password = get_random_string(8)
        guru.user.set_password(temp_password)
        guru.user.save()
        messages.success(request, f"Kata sandi {guru.nama} direset jadi: {temp_password} — sampaikan ke yang bersangkutan.")
    return redirect("akademik:akun_guru_list")


@admin_required
def akun_guru_toggle_active(request, pk):
    guru = get_object_or_404(Guru, pk=pk, school=get_school(request))
    if request.method == "POST":
        guru.user.is_active = not guru.user.is_active
        guru.user.save()
        status = "diaktifkan" if guru.user.is_active else "dinonaktifkan"
        messages.success(request, f"Akun {guru.nama} berhasil {status}.")
    return redirect("akademik:akun_guru_list")


# ================= AKUN ORANG TUA =================

@admin_required
def akun_ortu_list(request):
    school, guard = _school_or_guard(request)
    if guard:
        return guard
    ortu_list = OrangTua.objects.filter(school=school).select_related("user").prefetch_related("anak")
    return render(request, "akademik/akun_ortu_list.html", {"page_title": "Akun Orang Tua", "ortu_list": ortu_list})


@admin_required
def akun_ortu_create(request):
    school, guard = _school_or_guard(request)
    if guard:
        return guard

    if request.method == "POST":
        form = OrangTuaAccountForm(request.POST, school=school)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
                role=User.Role.ORANG_TUA,
                school=school,
            )
            ortu = OrangTua.objects.create(school=school, user=user, nama=form.cleaned_data["nama"], no_hp=form.cleaned_data["no_hp"])
            ortu.anak.set(form.cleaned_data["anak"])
            messages.success(request, f"Akun orang tua {form.cleaned_data['nama']} berhasil dibuat.")
            return redirect("akademik:akun_ortu_list")
    else:
        form = OrangTuaAccountForm(school=school)
    return render(request, "akademik/akun_form.html", {"page_title": "Tambah Akun Orang Tua", "form": form})


@admin_required
def akun_ortu_edit(request, pk):
    school = get_school(request)
    ortu = get_object_or_404(OrangTua, pk=pk, school=school)
    if request.method == "POST":
        form = OrangTuaEditForm(request.POST, instance=ortu, school=school)
        if form.is_valid():
            form.save()
            messages.success(request, f"Data {ortu.nama} berhasil diperbarui.")
            return redirect("akademik:akun_ortu_list")
    else:
        form = OrangTuaEditForm(instance=ortu, school=school)
    return render(request, "akademik/akun_form.html", {"page_title": f"Edit Akun Orang Tua — {ortu.nama}", "form": form})


@admin_required
def akun_ortu_reset(request, pk):
    from django.utils.crypto import get_random_string
    ortu = get_object_or_404(OrangTua, pk=pk, school=get_school(request))
    if request.method == "POST":
        temp_password = get_random_string(8)
        ortu.user.set_password(temp_password)
        ortu.user.save()
        messages.success(request, f"Kata sandi {ortu.nama} direset jadi: {temp_password} — sampaikan ke yang bersangkutan.")
    return redirect("akademik:akun_ortu_list")


@admin_required
def akun_ortu_toggle_active(request, pk):
    ortu = get_object_or_404(OrangTua, pk=pk, school=get_school(request))
    if request.method == "POST":
        ortu.user.is_active = not ortu.user.is_active
        ortu.user.save()
        status = "diaktifkan" if ortu.user.is_active else "dinonaktifkan"
        messages.success(request, f"Akun {ortu.nama} berhasil {status}.")
    return redirect("akademik:akun_ortu_list")