# Simpan sebagai: guru/views.py

from datetime import date

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from absensi.forms import KoreksiAbsensiForm
from absensi.models import AbsensiHarian
from absensi.utils import catat_koreksi_absensi
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
    siswa_list = Siswa.objects.filter(kelas=kelas, aktif=True).order_by("nama")
    total_siswa = siswa_list.count()

    absensi_map = {
        a.siswa_id: a
        for a in AbsensiHarian.objects.filter(siswa__kelas=kelas, tanggal=today)
    }

    baris = []
    hadir = izin = belum_absen = 0
    for siswa in siswa_list:
        a = absensi_map.get(siswa.id)
        if a and a.status in [AbsensiHarian.Status.HADIR, AbsensiHarian.Status.TERLAMBAT]:
            hadir += 1
        elif a and a.status == AbsensiHarian.Status.IZIN:
            izin += 1
        elif not a:
            belum_absen += 1
        baris.append({"siswa": siswa, "absensi": a})

    context = {
        "page_title": "Kelas Saya",
        "kelas": kelas,
        "kelas_list": kelas_list,
        "total_siswa": total_siswa,
        "hadir": hadir,
        "izin": izin,
        "belum_absen": belum_absen,
        "baris": baris,
    }
    return render(request, "guru/dashboard.html", context)


@guru_required
def koreksi_absensi(request, siswa_id):
    guru = _guru_profile(request)
    kelas_ids = guru.kelas_diampu.values_list("id", flat=True)
    siswa = get_object_or_404(Siswa, pk=siswa_id, kelas_id__in=kelas_ids)

    tanggal_str = request.GET.get("tanggal")
    tanggal = date.fromisoformat(tanggal_str) if tanggal_str else date.today()
    absensi_ada = AbsensiHarian.objects.filter(siswa=siswa, tanggal=tanggal).first()

    if request.method == "POST":
        form = KoreksiAbsensiForm(request.POST)
        if form.is_valid():
            catat_koreksi_absensi(
                siswa=siswa, tanggal=tanggal,
                status=form.cleaned_data["status"],
                jam_masuk=form.cleaned_data["jam_masuk"],
                jam_pulang=form.cleaned_data["jam_pulang"],
                catatan=form.cleaned_data["catatan"],
                user=request.user,
            )
            messages.success(request, f"Kehadiran {siswa.nama} tanggal {tanggal} berhasil dikoreksi.")
            return redirect("guru:dashboard")
    else:
        initial = {}
        if absensi_ada:
            initial = {"status": absensi_ada.status, "jam_masuk": absensi_ada.jam_masuk, "jam_pulang": absensi_ada.jam_pulang}
        form = KoreksiAbsensiForm(initial=initial)

    context = {
        "page_title": f"Koreksi Absensi \u2014 {siswa.nama}",
        "form": form, "siswa": siswa, "tanggal": tanggal, "absensi_ada": absensi_ada,
    }
    return render(request, "guru/koreksi_absensi.html", context)


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
        izin_obj.last_modified_by = request.user
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
        izin_obj.last_modified_by = request.user
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
    awal_str = request.GET.get("awal")
    akhir_str = request.GET.get("akhir")
    try:
        awal = date.fromisoformat(awal_str) if awal_str else today.replace(day=1)
    except ValueError:
        awal = today.replace(day=1)
    try:
        akhir = date.fromisoformat(akhir_str) if akhir_str else today
    except ValueError:
        akhir = today
    if akhir < awal:
        awal, akhir = akhir, awal

    rows = []
    for siswa in Siswa.objects.filter(kelas=kelas, aktif=True).order_by("nama"):
        absensi = AbsensiHarian.objects.filter(siswa=siswa, tanggal__gte=awal, tanggal__lte=akhir)
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
        "awal": awal,
        "akhir": akhir,
    }
    return render(request, "guru/laporan.html", context)