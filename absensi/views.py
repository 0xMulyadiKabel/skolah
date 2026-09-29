# Simpan sebagai: absensi/views.py

import csv
import json
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.utils import get_school
from accounts.views import admin_required, kiosk_required
from akademik.models import Kelas, Guru, Siswa

from .forms import HariLiburForm
from .models import AbsensiGuru, AbsensiHarian, AbsensiSholat, HariLibur, SesiSholat
from .utils import is_hari_sekolah


def _parse_rentang_tanggal(request):
    """
    Baca ?awal=YYYY-MM-DD&akhir=YYYY-MM-DD dari querystring. Default ke
    bulan berjalan kalau tidak diisi (backward-compatible sama perilaku
    lama), tapi sekarang Admin BISA pilih rentang bebas -- bukan cuma
    terbatas 1 bulan.
    """
    today = date.today()
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
    return awal, akhir


def _hitung_rekap_siswa(school, awal, akhir):
    rows = []
    for kelas in Kelas.objects.filter(school=school).order_by("nama_kelas"):
        total_siswa = Siswa.objects.filter(kelas=kelas, aktif=True).count()
        # __gte/__lte inklusif di kedua ujung -- tanggal awal & akhir ikut
        # kehitung, bukan kelewat. Ini poin yang eksplisit diminta di
        # catatan perbaikan (batas tanggal jangan sampai terlewat).
        absensi = AbsensiHarian.objects.filter(siswa__kelas=kelas, tanggal__gte=awal, tanggal__lte=akhir)
        hadir = absensi.filter(status__in=["hadir", "terlambat"]).count()
        izin = absensi.filter(status="izin").count()
        alpa = absensi.filter(status="alpa").count()
        total_tercatat = hadir + izin + alpa
        persen = round((hadir / total_tercatat) * 100) if total_tercatat else 0
        rows.append(dict(kelas=kelas, total_siswa=total_siswa, hadir=hadir, izin=izin, alpa=alpa, persen=persen))
    return rows


def _hitung_rekap_guru(school, awal, akhir):
    rows = []
    for guru in Guru.objects.filter(school=school).order_by("nama"):
        absensi = AbsensiGuru.objects.filter(guru=guru, tanggal__gte=awal, tanggal__lte=akhir)
        hadir = absensi.filter(status__in=["hadir", "terlambat"]).count()
        izin = absensi.filter(status="izin").count()
        alpa = absensi.filter(status="alpa").count()
        total_tercatat = hadir + izin + alpa
        persen = round((hadir / total_tercatat) * 100) if total_tercatat else 0
        rows.append(dict(guru=guru, hadir=hadir, izin=izin, alpa=alpa, persen=persen))
    return rows


@admin_required
def laporan_sekolah(request):
    school = get_school(request)
    tab = request.GET.get("tab", "siswa")
    awal, akhir = _parse_rentang_tanggal(request)

    context = {
        "page_title": "Laporan Kehadiran Sekolah",
        "tab": tab,
        "awal": awal,
        "akhir": akhir,
    }
    if tab == "guru":
        context["rows_guru"] = _hitung_rekap_guru(school, awal, akhir)
    else:
        context["rows_siswa"] = _hitung_rekap_siswa(school, awal, akhir)

    return render(request, "absensi/laporan_sekolah.html", context)


@admin_required
def laporan_export_csv(request):
    school = get_school(request)
    tab = request.GET.get("tab", "siswa")
    awal, akhir = _parse_rentang_tanggal(request)

    response = HttpResponse(content_type="text/csv")
    nama_file = f'laporan_{tab}_{awal.isoformat()}_sd_{akhir.isoformat()}.csv'
    response["Content-Disposition"] = f'attachment; filename="{nama_file}"'
    writer = csv.writer(response)

    if tab == "guru":
        rows = _hitung_rekap_guru(school, awal, akhir)
        writer.writerow(["Guru", "Hadir", "Izin/Sakit", "Alpa", "% Kehadiran"])
        for r in rows:
            writer.writerow([r["guru"].nama, r["hadir"], r["izin"], r["alpa"], f'{r["persen"]}%'])
    else:
        rows = _hitung_rekap_siswa(school, awal, akhir)
        writer.writerow(["Kelas", "Total Siswa", "Hadir", "Izin/Sakit", "Alpa", "% Kehadiran"])
        for r in rows:
            writer.writerow([r["kelas"].nama_kelas, r["total_siswa"], r["hadir"], r["izin"], r["alpa"], f'{r["persen"]}%'])

    return response


# ================= KALENDER AKADEMIK / HARI LIBUR =================

@admin_required
def hari_libur_list(request):
    school = get_school(request)
    libur_list = HariLibur.objects.filter(school=school).order_by("-tanggal")
    return render(request, "absensi/hari_libur_list.html", {"page_title": "Kalender Akademik", "libur_list": libur_list})


@admin_required
def hari_libur_create(request):
    school = get_school(request)
    if request.method == "POST":
        form = HariLiburForm(request.POST)
        if form.is_valid():
            libur = form.save(commit=False)
            libur.school = school
            try:
                libur.save()
                messages.success(request, f"Hari libur {libur.tanggal} berhasil ditambahkan.")
                return redirect("absensi:hari_libur_list")
            except IntegrityError:
                messages.error(request, "Tanggal tersebut sudah terdaftar sebagai hari libur.")
    else:
        form = HariLiburForm()
    return render(request, "absensi/hari_libur_form.html", {"page_title": "Tambah Hari Libur", "form": form})


@admin_required
def hari_libur_delete(request, pk):
    school = get_school(request)
    libur = get_object_or_404(HariLibur, pk=pk, school=school)
    if request.method == "POST":
        libur.delete()
        messages.success(request, "Hari libur berhasil dihapus.")
    return redirect("absensi:hari_libur_list")


# ================= KIOSK ABSEN (device bersama, scan QR kartu siswa) =================

def _sesi_sholat_aktif_saat_ini(school):
    """Cari sesi sholat yang jendela waktunya mencakup jam sekarang, dari
    sesi-sesi yang diaktifkan Admin UNTUK HARI INI. None kalau nggak ada
    sesi aktif detik ini (baik soal jam maupun soal hari)."""
    today = timezone.localdate()
    now_time = timezone.localtime().time()
    kandidat = SesiSholat.objects.filter(
        school=school, aktif=True, jendela_mulai__lte=now_time, jendela_selesai__gte=now_time,
    )
    for sesi in kandidat:
        if sesi.aktif_pada_tanggal(today):
            return sesi
    return None


@kiosk_required
def kiosk_gerbang(request):
    school = get_school(request)
    return render(request, "absensi/kiosk_gerbang.html", {"page_title": "Kiosk Absen Gerbang", "school": school})


@kiosk_required
def kiosk_gerbang_submit(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "pesan": "Metode tidak diizinkan."}, status=405)

    school = get_school(request)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "pesan": "Data tidak valid."}, status=400)

    kode = str(data.get("nis", "")).strip()
    today = timezone.localdate()

    if not is_hari_sekolah(school, today):
        return JsonResponse({"ok": False, "pesan": "Hari ini bukan hari sekolah aktif."})

    siswa = Siswa.objects.filter(school=school, nis=kode, aktif=True).first()
    if siswa:
        return _catat_absen_siswa_kiosk(siswa, school, today)

    # Bukan kartu siswa -- coba cek apakah ini kartu Guru (kartu Guru
    # isinya username akun mereka, bukan NISN).
    guru = Guru.objects.filter(school=school, user__username=kode).first()
    if guru:
        return _catat_absen_guru_kiosk(guru, school, today)

    return JsonResponse({"ok": False, "pesan": f"Kartu '{kode}' tidak dikenali (bukan siswa maupun guru aktif)."})


def _catat_absen_siswa_kiosk(siswa, school, today):
    now = timezone.localtime().time()
    absensi, _ = AbsensiHarian.objects.get_or_create(siswa=siswa, tanggal=today)

    # lokasi_valid otomatis True -- device ini fisiknya menetap di gerbang
    # sekolah, jadi tidak perlu cek GPS terpisah kayak metode selfie.
    if not absensi.jam_masuk:
        absensi.jam_masuk = now
        absensi.metode_masuk = AbsensiHarian.Metode.BARCODE_KARTU
        absensi.lokasi_valid_masuk = True
        batas_telat_dt = datetime.combine(today, school.jam_masuk) + timedelta(minutes=school.toleransi_keterlambatan_menit)
        absensi.status = AbsensiHarian.Status.HADIR if now <= batas_telat_dt.time() else AbsensiHarian.Status.TERLAMBAT
        absensi.save()
        return JsonResponse({"ok": True, "nama": siswa.nama, "pesan": f"[Siswa] Absen masuk pukul {now.strftime('%H:%M')}"})

    elif not absensi.jam_pulang:
        absensi.jam_pulang = now
        absensi.metode_pulang = AbsensiHarian.Metode.BARCODE_KARTU
        absensi.lokasi_valid_pulang = True
        absensi.save()
        return JsonResponse({"ok": True, "nama": siswa.nama, "pesan": f"[Siswa] Absen pulang pukul {now.strftime('%H:%M')}"})

    else:
        return JsonResponse({"ok": False, "nama": siswa.nama, "pesan": "Sudah absen masuk & pulang hari ini."})


def _catat_absen_guru_kiosk(guru, school, today):
    now = timezone.localtime().time()
    absensi, _ = AbsensiGuru.objects.get_or_create(guru=guru, tanggal=today)

    if not absensi.jam_masuk:
        absensi.jam_masuk = now
        absensi.metode_masuk = AbsensiGuru.Metode.BARCODE_KARTU
        batas_telat_dt = datetime.combine(today, school.jam_masuk) + timedelta(minutes=school.toleransi_keterlambatan_menit)
        absensi.status = AbsensiGuru.Status.HADIR if now <= batas_telat_dt.time() else AbsensiGuru.Status.TERLAMBAT
        absensi.save()
        return JsonResponse({"ok": True, "nama": guru.nama, "pesan": f"[Guru] Absen masuk pukul {now.strftime('%H:%M')}"})

    elif not absensi.jam_pulang:
        absensi.jam_pulang = now
        absensi.metode_pulang = AbsensiGuru.Metode.BARCODE_KARTU
        absensi.save()
        return JsonResponse({"ok": True, "nama": guru.nama, "pesan": f"[Guru] Absen pulang pukul {now.strftime('%H:%M')}"})

    else:
        return JsonResponse({"ok": False, "nama": guru.nama, "pesan": "Sudah absen masuk & pulang hari ini."})


@kiosk_required
def kiosk_sholat(request):
    school = get_school(request)
    sesi = _sesi_sholat_aktif_saat_ini(school)
    return render(request, "absensi/kiosk_sholat.html", {"page_title": "Kiosk Absen Sholat", "school": school, "sesi": sesi})


@kiosk_required
def kiosk_sholat_submit(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "pesan": "Metode tidak diizinkan."}, status=405)

    school = get_school(request)
    sesi = _sesi_sholat_aktif_saat_ini(school)
    if not sesi:
        return JsonResponse({"ok": False, "pesan": "Tidak ada sesi sholat yang aktif saat ini."})

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "pesan": "Data tidak valid."}, status=400)

    nis = str(data.get("nis", "")).strip()
    siswa = Siswa.objects.filter(school=school, nis=nis, aktif=True).first()
    if not siswa:
        return JsonResponse({"ok": False, "pesan": f"Kartu dengan NISN {nis} tidak dikenali atau siswa nonaktif."})

    today = timezone.localdate()
    now = timezone.localtime().time()
    absensi_sholat, created = AbsensiSholat.objects.get_or_create(
        siswa=siswa, sesi_sholat=sesi, tanggal=today,
        defaults={"waktu_absen": now, "hadir": True, "lokasi_valid": True},
    )
    if not created:
        return JsonResponse({"ok": False, "nama": siswa.nama, "pesan": f"Sudah tercatat hadir sholat {sesi.get_nama_sholat_display()}."})

    return JsonResponse({"ok": True, "nama": siswa.nama, "pesan": f"Absen sholat {sesi.get_nama_sholat_display()} pukul {now.strftime('%H:%M')}"})


# ================= AKSES FOTO & BUKTI IZIN (TERPROTEKSI) =================
# Sebelum ini, /media/ dilayani Nginx langsung tanpa login -- siapapun yang
# tahu/nebak URL-nya bisa buka foto siswa atau surat sakit. Sekarang SEMUA
# akses foto/bukti WAJIB lewat view ini, yang ngecek hak akses dulu sebelum
# streaming file-nya. Nginx TIDAK BOLEH lagi expose /media/ langsung.

from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404


def _bisa_lihat_data_siswa(user, siswa):
    """True kalau user ini berhak lihat data (foto/bukti) milik siswa
    tsb: Admin sekolah yang sama, Guru wali kelas siswa itu, siswa itu
    sendiri, atau Orang Tua yang terhubung ke siswa itu."""
    if user.role == "admin":
        return siswa.school_id == user.school_id
    if user.role == "guru":
        try:
            return siswa.kelas_id in user.guru.kelas_diampu.values_list("id", flat=True)
        except Exception:
            return False
    if user.role == "siswa":
        try:
            return user.siswa.id == siswa.id
        except Exception:
            return False
    if user.role == "orang_tua":
        try:
            return user.orangtua.anak.filter(id=siswa.id).exists()
        except Exception:
            return False
    return False


def _bisa_lihat_data_guru(user, guru):
    """True kalau user ini berhak lihat data (foto/bukti) milik guru
    tsb: Admin sekolah yang sama, atau guru itu sendiri."""
    if user.role == "admin":
        return guru.school_id == user.school_id
    if user.role == "guru":
        try:
            return user.guru.id == guru.id
        except Exception:
            return False
    return False


def _serve_file(field_file):
    if not field_file:
        raise Http404("Belum ada file.")
    try:
        return FileResponse(field_file.open("rb"))
    except FileNotFoundError:
        raise Http404("File tidak ditemukan di server.")


@login_required
def foto_absensi_harian(request, pk, field):
    absensi = get_object_or_404(AbsensiHarian, pk=pk)
    if not _bisa_lihat_data_siswa(request.user, absensi.siswa):
        raise Http404()
    file_field = absensi.foto_masuk if field == "masuk" else absensi.foto_pulang
    return _serve_file(file_field)


@login_required
def foto_absensi_sholat(request, pk):
    absensi = get_object_or_404(AbsensiSholat, pk=pk)
    if not _bisa_lihat_data_siswa(request.user, absensi.siswa):
        raise Http404()
    return _serve_file(absensi.foto)


@login_required
def foto_absensi_guru(request, pk, field):
    absensi = get_object_or_404(AbsensiGuru, pk=pk)
    if not _bisa_lihat_data_guru(request.user, absensi.guru):
        raise Http404()
    file_field = absensi.foto_masuk if field == "masuk" else absensi.foto_pulang
    return _serve_file(file_field)


@login_required
def bukti_izin_siswa(request, pk):
    from perizinan.models import PengajuanIzin

    izin = get_object_or_404(PengajuanIzin, pk=pk)
    if not _bisa_lihat_data_siswa(request.user, izin.siswa):
        raise Http404()
    return _serve_file(izin.bukti)


@login_required
def bukti_izin_guru(request, pk):
    from perizinan.models import PengajuanIzinGuru

    izin = get_object_or_404(PengajuanIzinGuru, pk=pk)
    if not _bisa_lihat_data_guru(request.user, izin.guru):
        raise Http404()
    return _serve_file(izin.bukti)