# Simpan sebagai: dashboard/views.py (timpa yang lama)

from django.shortcuts import render
from django.utils import timezone

from absensi.models import AbsensiGuru, AbsensiHarian
from absensi.utils import is_hari_sekolah
from accounts.utils import get_school
from accounts.views import admin_required
from akademik.models import Guru, Siswa


def _build_context_siswa(school):
    today = timezone.localdate()

    total_siswa = Siswa.objects.filter(school=school, aktif=True).count()
    absensi_hari_ini = AbsensiHarian.objects.filter(siswa__school=school, tanggal=today)

    hadir = absensi_hari_ini.filter(
        status__in=[AbsensiHarian.Status.HADIR, AbsensiHarian.Status.TERLAMBAT]
    ).count()
    izin = absensi_hari_ini.filter(status=AbsensiHarian.Status.IZIN).count()
    belum_absen = total_siswa - absensi_hari_ini.count()

    live_checkin = (
        absensi_hari_ini
        .select_related("siswa", "siswa__kelas")
        .exclude(jam_masuk__isnull=True)
        .order_by("-jam_masuk")[:10]
    )

    return {
        "total_siswa": total_siswa,
        "hadir_siswa": hadir,
        "izin_siswa": izin,
        "belum_absen_siswa": belum_absen,
        "live_checkin": live_checkin,
    }


def _build_context_guru(school):
    today = timezone.localdate()

    guru_list = Guru.objects.filter(school=school).order_by("nama")
    absensi_map = {a.guru_id: a for a in AbsensiGuru.objects.filter(guru__school=school, tanggal=today)}

    baris_guru = []
    hadir = izin = belum_absen = 0
    for guru in guru_list:
        a = absensi_map.get(guru.id)
        if a and a.status in [AbsensiGuru.Status.HADIR, AbsensiGuru.Status.TERLAMBAT]:
            hadir += 1
        elif a and a.status == AbsensiGuru.Status.IZIN:
            izin += 1
        elif not a:
            belum_absen += 1
        baris_guru.append({"guru": guru, "absensi": a})

    return {
        "total_guru": guru_list.count(),
        "hadir_guru": hadir,
        "izin_guru": izin,
        "belum_absen_guru": belum_absen,
        "baris_guru": baris_guru,
    }


@admin_required
def index(request):
    school = get_school(request)
    if school is None:
        return render(request, "accounts/school_missing.html", {"page_title": "Dashboard Sekolah"})

    tab = request.GET.get("tab", "siswa")
    today = timezone.localdate()

    context = {
        "page_title": "Dashboard Sekolah",
        "tab": tab,
        "hari_sekolah": is_hari_sekolah(school, today),
    }
    if tab == "guru":
        context.update(_build_context_guru(school))
    else:
        context.update(_build_context_siswa(school))

    return render(request, "dashboard/index.html", context)


@admin_required
def live_checkin_partial(request):
    # Dipanggil HTMX (bukan navigasi biasa) -- cuma render potongan HTML
    # tabel live check-in, bukan halaman penuh. Ini yang bikin tombol
    # Refresh bisa update data tanpa reload seluruh halaman.
    school = get_school(request)
    context = _build_context_siswa(school)
    return render(request, "dashboard/_live_checkin.html", context)