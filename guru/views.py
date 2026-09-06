from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from absensi.models import AbsensiHarian
from accounts.views import guru_required
from akademik.models import Siswa
from perizinan.models import PengajuanIzin


def _guru_profile(request):
    # request.user.guru -- reverse accessor OneToOneField, sama pola
    # seperti request.user.siswa di app siswa.
    return request.user.guru


def _kelas_terpilih(request, guru):
    """Guru bisa jadi wali kelas lebih dari 1 kelas (jarang, tapi model
    mendukung). Kalau ada beberapa, pakai query param ?kelas=<id> buat
    pilih yang mana yang mau ditampilkan; default kelas pertama."""
    kelas_list = guru.kelas_diampu.all()
    kelas_id = request.GET.get("kelas")
    if kelas_id:
        dipilih = kelas_list.filter(pk=kelas_id).first()
        if dipilih:
            return dipilih, kelas_list
    return kelas_list.first(), kelas_list


@guru_required
def dashboard(request):
    guru = _guru_profile(request)
    kelas, kelas_list = _kelas_terpilih(request, guru)

    if not kelas:
        return render(request, "guru/tidak_ada_kelas.html", {"page_title": "Kelas Saya"})

    today = timezone.localdate()
    total_siswa = Siswa.objects.filter(kelas=kelas, aktif=True).count()
    absensi_hari_ini = AbsensiHarian.objects.filter(siswa__kelas=kelas, tanggal=today).select_related("siswa")

    hadir = absensi_hari_ini.filter(status__in=[AbsensiHarian.Status.HADIR, AbsensiHarian.Status.TERLAMBAT]).count()
    izin = absensi_hari_ini.filter(status=AbsensiHarian.Status.IZIN).count()
    belum_absen = total_siswa - absensi_hari_ini.count()

    context = {
        "page_title": "Kelas Saya",
        "kelas": kelas,
        "kelas_list": kelas_list,
        "total_siswa": total_siswa,
        "hadir": hadir,
        "izin": izin,
        "belum_absen": belum_absen,
        "absensi_hari_ini": absensi_hari_ini.exclude(jam_masuk__isnull=True).order_by("-jam_masuk"),
    }
    return render(request, "guru/dashboard.html", context)


@guru_required
def izin_list(request):
    guru = _guru_profile(request)
    status = request.GET.get("status", "")
    kelas_ids = guru.kelas_diampu.values_list("id", flat=True)

    izin_qs = (
        PengajuanIzin.objects.filter(siswa__kelas_id__in=kelas_ids)
        .select_related("siswa", "siswa__kelas")
        .order_by("-dibuat_pada")
    )
    if status:
        izin_qs = izin_qs.filter(status=status)

    context = {"page_title": "Approval Izin", "izin_list": izin_qs, "status_selected": status}
    return render(request, "guru/izin_list.html", context)


@guru_required
def izin_setujui(request, pk):
    guru = _guru_profile(request)
    kelas_ids = guru.kelas_diampu.values_list("id", flat=True)
    izin_obj = get_object_or_404(PengajuanIzin, pk=pk, siswa__kelas_id__in=kelas_ids)
    if request.method == "POST":
        izin_obj.status = PengajuanIzin.Status.DISETUJUI
        izin_obj.ditinjau_oleh = guru
        izin_obj.save()
        messages.success(request, f"Pengajuan izin {izin_obj.siswa.nama} disetujui.")
    return redirect("guru:izin_list")


@guru_required
def izin_tolak(request, pk):
    guru = _guru_profile(request)
    kelas_ids = guru.kelas_diampu.values_list("id", flat=True)
    izin_obj = get_object_or_404(PengajuanIzin, pk=pk, siswa__kelas_id__in=kelas_ids)
    if request.method == "POST":
        izin_obj.status = PengajuanIzin.Status.DITOLAK
        izin_obj.ditinjau_oleh = guru
        izin_obj.save()
        messages.success(request, f"Pengajuan izin {izin_obj.siswa.nama} ditolak.")
    return redirect("guru:izin_list")


@guru_required
def laporan(request):
    guru = _guru_profile(request)
    kelas, kelas_list = _kelas_terpilih(request, guru)

    if not kelas:
        return render(request, "guru/tidak_ada_kelas.html", {"page_title": "Laporan Kelas"})

    today = timezone.localdate()
    awal_bulan = today.replace(day=1)

    rows = []
    for siswa in Siswa.objects.filter(kelas=kelas, aktif=True).order_by("nama"):
        absensi = AbsensiHarian.objects.filter(siswa=siswa, tanggal__gte=awal_bulan, tanggal__lte=today)
        hadir = absensi.filter(status__in=["hadir", "terlambat"]).count()
        izin = absensi.filter(status="izin").count()
        alpa = absensi.filter(status="alpa").count()
        total = hadir + izin + alpa
        persen = round((hadir / total) * 100) if total else 0
        rows.append({"siswa": siswa, "hadir": hadir, "izin": izin, "alpa": alpa, "persen": persen})

    context = {
        "page_title": "Laporan Kelas",
        "kelas": kelas,
        "kelas_list": kelas_list,
        "rows": rows,
        "periode_label": awal_bulan.strftime("%B %Y"),
    }
    return render(request, "guru/laporan.html", context)