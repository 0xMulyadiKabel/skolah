import json
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie

from absensi.models import AbsensiHarian, AbsensiSholat, HalanganSholat, SesiSholat
from absensi.utils import generate_daily_token, get_jadwal_sholat, haversine_distance
from accounts.views import siswa_required
from perizinan.forms import PengajuanIzinForm
from perizinan.models import PengajuanIzin


def _siswa_profile(request):
    return request.user.siswa


@siswa_required
def beranda(request):
    siswa = _siswa_profile(request)
    today = date.today()

    absensi_hari_ini = AbsensiHarian.objects.filter(siswa=siswa, tanggal=today).first()

    bulan_ini = AbsensiHarian.objects.filter(siswa=siswa, tanggal__year=today.year, tanggal__month=today.month)
    hadir = bulan_ini.filter(status__in=[AbsensiHarian.Status.HADIR, AbsensiHarian.Status.TERLAMBAT]).count()
    izin = bulan_ini.filter(status=AbsensiHarian.Status.IZIN).count()
    alpa = bulan_ini.filter(status=AbsensiHarian.Status.ALPA).count()

    context = {
        "page_title": "Beranda",
        "siswa": siswa,
        "absensi_hari_ini": absensi_hari_ini,
        "hadir": hadir,
        "izin": izin,
        "alpa": alpa,
        "jadwal_sholat": get_jadwal_sholat(siswa.school),
    }
    return render(request, "siswa/beranda.html", context)


@siswa_required
def riwayat(request):
    siswa = _siswa_profile(request)
    status_filter = request.GET.get("status", "")

    riwayat_qs = AbsensiHarian.objects.filter(siswa=siswa).order_by("-tanggal")
    if status_filter:
        riwayat_qs = riwayat_qs.filter(status=status_filter)

    context = {"page_title": "Riwayat Kehadiran", "riwayat_list": riwayat_qs[:60], "status_filter": status_filter}
    return render(request, "siswa/riwayat.html", context)


# ================= ABSEN SEKOLAH (gerbang) =================

@ensure_csrf_cookie
@siswa_required
def absen(request):
    siswa = _siswa_profile(request)
    school = siswa.school
    today = timezone.localdate()

    sesi_aktif = SesiSholat.objects.filter(school=school, aktif=True).order_by("id")
    sudah_absen_sholat = set(
        AbsensiSholat.objects.filter(siswa=siswa, tanggal=today, hadir=True).values_list("sesi_sholat_id", flat=True)
    )
    halangan_aktif = HalanganSholat.objects.filter(
        siswa=siswa, tanggal_mulai__lte=today, tanggal_selesai__gte=today
    ).first()

    context = {
        "page_title": "Absen",
        "sesi_aktif": sesi_aktif,
        "sudah_absen_sholat": sudah_absen_sholat,
        "halangan_aktif": halangan_aktif,
        "tampilkan_halangan": siswa.jenis_kelamin == "P",
    }
    return render(request, "siswa/absen.html", context)


@siswa_required
def absen_submit(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "pesan": "Metode tidak diizinkan."}, status=405)

    siswa = _siswa_profile(request)
    school = siswa.school

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "pesan": "Data tidak valid."}, status=400)

    qr_token = data.get("qr_token", "")
    lat = data.get("latitude")
    lng = data.get("longitude")

    if school.metode_verifikasi in ["qr_lokasi", "qr"]:
        expected_token = generate_daily_token(school.id)
        if qr_token != expected_token:
            return JsonResponse({
                "ok": False,
                "pesan": "QR tidak valid atau sudah kedaluwarsa. Pastikan kamu scan QR di gerbang sekolah hari ini.",
            })

    lokasi_valid = True
    if school.metode_verifikasi in ["qr_lokasi", "lokasi"]:
        if lat is None or lng is None:
            return JsonResponse({"ok": False, "pesan": "Lokasi tidak terdeteksi. Aktifkan GPS dan izinkan akses lokasi di browser."})
        jarak = haversine_distance(float(lat), float(lng), float(school.latitude), float(school.longitude))
        lokasi_valid = jarak <= school.radius_geofence_meter
        if not lokasi_valid:
            return JsonResponse({
                "ok": False,
                "pesan": f"Kamu berada sekitar {int(jarak)}m dari sekolah, di luar radius yang diizinkan ({school.radius_geofence_meter}m).",
            })

    today = timezone.localdate()
    now = timezone.localtime().time()
    absensi, _ = AbsensiHarian.objects.get_or_create(siswa=siswa, tanggal=today)

    if not absensi.jam_masuk:
        absensi.jam_masuk = now
        absensi.metode_masuk = AbsensiHarian.Metode.QR_LOKASI
        absensi.lokasi_valid_masuk = lokasi_valid
        batas_telat_dt = datetime.combine(today, school.jam_masuk) + timedelta(minutes=school.toleransi_keterlambatan_menit)
        absensi.status = AbsensiHarian.Status.HADIR if now <= batas_telat_dt.time() else AbsensiHarian.Status.TERLAMBAT
        absensi.save()
        return JsonResponse({"ok": True, "pesan": f"Absen masuk berhasil dicatat pukul {now.strftime('%H:%M')}."})

    elif not absensi.jam_pulang:
        absensi.jam_pulang = now
        absensi.metode_pulang = AbsensiHarian.Metode.QR_LOKASI
        absensi.lokasi_valid_pulang = lokasi_valid
        absensi.save()
        return JsonResponse({"ok": True, "pesan": f"Absen pulang berhasil dicatat pukul {now.strftime('%H:%M')}."})

    else:
        return JsonResponse({"ok": False, "pesan": "Kamu sudah absen masuk dan pulang hari ini."})


# ================= ABSEN SHOLAT BERJAMAAH =================

@ensure_csrf_cookie
@siswa_required
def absen_sholat(request, sesi_id):
    siswa = _siswa_profile(request)
    sesi = get_object_or_404(SesiSholat, pk=sesi_id, school=siswa.school, aktif=True)
    context = {"page_title": f"Absen {sesi.get_nama_sholat_display()}", "sesi": sesi}
    return render(request, "siswa/absen_sholat.html", context)


@siswa_required
def absen_sholat_submit(request, sesi_id):
    if request.method != "POST":
        return JsonResponse({"ok": False, "pesan": "Metode tidak diizinkan."}, status=405)

    siswa = _siswa_profile(request)
    sesi = get_object_or_404(SesiSholat, pk=sesi_id, school=siswa.school, aktif=True)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "pesan": "Data tidak valid."}, status=400)

    expected_token = generate_daily_token(siswa.school.id)
    if data.get("qr_token", "") != expected_token:
        return JsonResponse({"ok": False, "pesan": "QR tidak valid atau sudah kedaluwarsa."})

    now_time = timezone.localtime().time()
    if sesi.jendela_mulai and sesi.jendela_selesai:
        if not (sesi.jendela_mulai <= now_time <= sesi.jendela_selesai):
            return JsonResponse({
                "ok": False,
                "pesan": f"Di luar jendela waktu sesi {sesi.get_nama_sholat_display()} "
                         f"({sesi.jendela_mulai.strftime('%H:%M')}\u2013{sesi.jendela_selesai.strftime('%H:%M')}).",
            })

    today = timezone.localdate()
    absensi_sholat, created = AbsensiSholat.objects.get_or_create(
        siswa=siswa, sesi_sholat=sesi, tanggal=today, defaults={"waktu_absen": now_time, "hadir": True},
    )
    if not created:
        return JsonResponse({"ok": False, "pesan": f"Kamu sudah tercatat hadir sholat {sesi.get_nama_sholat_display()} hari ini."})

    return JsonResponse({"ok": True, "pesan": f"Absen sholat {sesi.get_nama_sholat_display()} berhasil dicatat pukul {now_time.strftime('%H:%M')}."})


# ================= HALANGAN SHOLAT =================

@siswa_required
def halangan(request):
    siswa = _siswa_profile(request)

    if siswa.jenis_kelamin != "P":
        messages.error(request, "Fitur ini khusus untuk siswa putri.")
        return redirect("siswa:absen")

    today = timezone.localdate()
    halangan_aktif = HalanganSholat.objects.filter(
        siswa=siswa, tanggal_mulai__lte=today, tanggal_selesai__gte=today
    ).first()

    if request.method == "POST":
        tanggal_mulai = request.POST.get("tanggal_mulai")
        tanggal_selesai = request.POST.get("tanggal_selesai")
        if tanggal_mulai and tanggal_selesai:
            HalanganSholat.objects.create(siswa=siswa, tanggal_mulai=tanggal_mulai, tanggal_selesai=tanggal_selesai)
            messages.success(request, "Tercatat. Kamu tidak akan diminta absen sholat sampai tanggal yang dipilih.")
            return redirect("siswa:absen")

    context = {"page_title": "Ajukan Halangan", "halangan_aktif": halangan_aktif, "today": today}
    return render(request, "siswa/halangan.html", context)


# ================= PENGAJUAN IZIN =================

@siswa_required
def izin(request):
    siswa = _siswa_profile(request)

    if request.method == "POST":
        form = PengajuanIzinForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.siswa = siswa
            pengajuan.diajukan_oleh = PengajuanIzin.DiajukanOleh.SISWA
            pengajuan.diajukan_oleh_user = request.user
            pengajuan.save()
            messages.success(request, "Pengajuan izin berhasil dikirim, menunggu persetujuan wali kelas.")
            return redirect("siswa:izin")
    else:
        form = PengajuanIzinForm()

    riwayat_izin = PengajuanIzin.objects.filter(siswa=siswa).select_related("ditinjau_oleh").order_by("-dibuat_pada")

    context = {"page_title": "Pengajuan Izin", "form": form, "riwayat_izin": riwayat_izin}
    return render(request, "siswa/izin.html", context)