from datetime import date

from django.contrib import messages
from django.shortcuts import redirect, render

from absensi.models import AbsensiHarian, AbsensiSholat
from accounts.views import ortu_required
from notifikasi.models import Notifikasi
from perizinan.forms import PengajuanIzinForm
from perizinan.models import PengajuanIzin


def _ortu_profile(request):
    # request.user.orangtua -- reverse accessor OneToOneField, sama pola
    # seperti request.user.siswa / request.user.guru.
    return request.user.orangtua


def _anak_terpilih(request, ortu):
    """Orang tua bisa punya lebih dari 1 anak (M2M). Pakai query param
    ?anak=<id> buat pilih yang mana lagi ditampilkan, default anak pertama."""
    anak_list = ortu.anak.select_related("kelas").all().order_by("nama")
    anak_id = request.GET.get("anak")
    if anak_id:
        dipilih = anak_list.filter(pk=anak_id).first()
        if dipilih:
            return dipilih, anak_list
    return anak_list.first(), anak_list


@ortu_required
def beranda(request):
    ortu = _ortu_profile(request)
    anak, anak_list = _anak_terpilih(request, ortu)

    if not anak:
        return render(request, "ortu/tidak_ada_anak.html", {"page_title": "Beranda", "anak_list": anak_list})

    today = date.today()
    absensi_hari_ini = AbsensiHarian.objects.filter(siswa=anak, tanggal=today).first()

    bulan_ini = AbsensiHarian.objects.filter(siswa=anak, tanggal__year=today.year, tanggal__month=today.month)
    hadir = bulan_ini.filter(status__in=[AbsensiHarian.Status.HADIR, AbsensiHarian.Status.TERLAMBAT]).count()
    izin = bulan_ini.filter(status=AbsensiHarian.Status.IZIN).count()

    # "Aktivitas Terbaru" -- gabungan dari 3 sumber berbeda (absen harian,
    # absen sholat, keputusan izin), disatukan lalu diurutkan tanggal
    # terbaru. Sengaja disederhanakan (bukan query 1 tabel), karena memang
    # datanya lintas model.
    aktivitas = []
    for a in AbsensiHarian.objects.filter(siswa=anak).exclude(jam_masuk__isnull=True).order_by("-tanggal")[:5]:
        aktivitas.append({"icon": "✓", "judul": "Absen Masuk", "sub": a.jam_masuk.strftime("%H:%M"), "tanggal": a.tanggal, "warna": "success"})
    for s in AbsensiSholat.objects.filter(siswa=anak, hadir=True).select_related("sesi_sholat").order_by("-tanggal")[:5]:
        aktivitas.append({"icon": "🕌", "judul": f"Sholat {s.sesi_sholat.get_nama_sholat_display()} Berjamaah", "sub": "Hadir", "tanggal": s.tanggal, "warna": "success"})
    for i in PengajuanIzin.objects.filter(siswa=anak).exclude(status="menunggu").order_by("-diperbarui_pada")[:3]:
        judul = f"{'Disetujui' if i.status == 'disetujui' else 'Ditolak'}: {i.get_jenis_display()}"
        aktivitas.append({"icon": "✓" if i.status == "disetujui" else "✕", "judul": judul, "sub": "", "tanggal": i.tanggal_mulai, "warna": "success" if i.status == "disetujui" else "danger"})
    aktivitas.sort(key=lambda x: x["tanggal"], reverse=True)

    context = {
        "page_title": "Beranda",
        "anak": anak,
        "anak_list": anak_list,
        "absensi_hari_ini": absensi_hari_ini,
        "hadir": hadir,
        "izin": izin,
        "aktivitas": aktivitas[:5],
    }
    return render(request, "ortu/beranda.html", context)


@ortu_required
def riwayat(request):
    ortu = _ortu_profile(request)
    anak, anak_list = _anak_terpilih(request, ortu)

    if not anak:
        return render(request, "ortu/tidak_ada_anak.html", {"page_title": "Riwayat", "anak_list": anak_list})

    riwayat_qs = AbsensiHarian.objects.filter(siswa=anak).order_by("-tanggal")[:60]
    context = {"page_title": "Riwayat Kehadiran", "anak": anak, "anak_list": anak_list, "riwayat_list": riwayat_qs}
    return render(request, "ortu/riwayat.html", context)


@ortu_required
def izin(request):
    ortu = _ortu_profile(request)
    anak, anak_list = _anak_terpilih(request, ortu)

    if not anak:
        return render(request, "ortu/tidak_ada_anak.html", {"page_title": "Ajukan Izin", "anak_list": anak_list})

    if request.method == "POST":
        form = PengajuanIzinForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.siswa = anak
            pengajuan.diajukan_oleh = PengajuanIzin.DiajukanOleh.ORANG_TUA
            pengajuan.diajukan_oleh_user = request.user
            pengajuan.save()
            messages.success(request, f"Pengajuan izin untuk {anak.nama} berhasil dikirim, menunggu persetujuan wali kelas.")
            return redirect(f"{request.path}?anak={anak.id}")
    else:
        form = PengajuanIzinForm()

    riwayat_izin = PengajuanIzin.objects.filter(siswa=anak).select_related("ditinjau_oleh").order_by("-dibuat_pada")

    context = {
        "page_title": "Ajukan Izin", "anak": anak, "anak_list": anak_list,
        "form": form, "riwayat_izin": riwayat_izin,
    }
    return render(request, "ortu/izin.html", context)


@ortu_required
def notifikasi(request):
    semua_notif = Notifikasi.objects.filter(penerima=request.user)
    semua_notif.filter(sudah_dibaca=False).update(sudah_dibaca=True)
    notif_list = semua_notif.order_by("-dibuat_pada")[:50]
    return render(request, "ortu/notifikasi.html", {"page_title": "Notifikasi", "notif_list": notif_list})