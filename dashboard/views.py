from django.shortcuts import render
from django.utils import timezone

from absensi.models import AbsensiHarian
from accounts.utils import get_school
from accounts.views import admin_required
from akademik.models import Siswa


def _build_context(request):
    school = get_school(request)
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
        "hadir": hadir,
        "izin": izin,
        "belum_absen": belum_absen,
        "live_checkin": live_checkin,
    }


@admin_required
def index(request):
    if get_school(request) is None:
        return render(request, "accounts/school_missing.html", {"page_title": "Dashboard Sekolah"})
    context = _build_context(request)
    context["page_title"] = "Dashboard Sekolah"
    return render(request, "dashboard/index.html", context)


@admin_required
def live_checkin_partial(request):
    # Dipanggil HTMX (bukan navigasi biasa) -- cuma render potongan HTML
    # tabel live check-in, bukan halaman penuh. Ini yang bikin tombol
    # Refresh bisa update data tanpa reload seluruh halaman.
    context = _build_context(request)
    return render(request, "dashboard/_live_checkin.html", context)