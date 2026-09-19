# Simpan sebagai: absensi/utils.py

import math

import requests
from django.core.cache import cache
from django.utils import timezone


def haversine_distance(lat1, lon1, lat2, lon2):
    """Jarak garis lurus (meter) antara dua titik koordinat GPS."""
    R = 6371000  # radius Bumi dalam meter
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


DAY_FIELD_MAP = {
    0: "aktif_senin", 1: "aktif_selasa", 2: "aktif_rabu", 3: "aktif_kamis",
    4: "aktif_jumat", 5: "aktif_sabtu", 6: "aktif_minggu",
}


def is_hari_sekolah(school, tanggal):
    """
    True kalau tanggal itu hari sekolah aktif -- artinya BUKAN hari yang
    di-nonaktifkan Admin di Pengaturan (mis. Sabtu/Minggu), DAN bukan
    tanggal yang terdaftar sebagai Hari Libur (mis. libur nasional yang
    kebetulan jatuh di hari kerja).
    """
    from .models import HariLibur

    field_name = DAY_FIELD_MAP[tanggal.weekday()]
    if not getattr(school, field_name):
        return False
    return not HariLibur.objects.filter(school=school, tanggal=tanggal).exists()


def catat_koreksi_absensi(siswa, tanggal, status, jam_masuk, jam_pulang, catatan, user):
    """
    Dipakai bareng oleh Guru dan Admin -- satu-satunya jalur resmi untuk
    'menimpa' data kehadiran secara manual. Selalu isi dikoreksi_oleh &
    dikoreksi_pada, supaya ada jejak akuntabilitas siapa yang override dan
    kapan (relevan untuk kasus GPS gagal, siswa lupa absen, dsb).
    """
    from django.utils import timezone

    from .models import AbsensiHarian

    absensi, _ = AbsensiHarian.objects.get_or_create(siswa=siswa, tanggal=tanggal)
    absensi.status = status
    if jam_masuk:
        absensi.jam_masuk = jam_masuk
    if jam_pulang:
        absensi.jam_pulang = jam_pulang
    absensi.dikoreksi_oleh = user
    absensi.dikoreksi_pada = timezone.now()
    absensi.catatan_koreksi = catatan
    absensi.save()
    return absensi


def get_jadwal_sholat(school):
    """
    Ambil jadwal sholat hari ini untuk lokasi sekolah, dari Aladhan API
    (method=20 = KEMENAG, metode resmi Kementerian Agama RI). Di-cache
    12 jam per sekolah per tanggal, supaya tidak nge-hit API tiap kali
    ada siswa buka Beranda. Kalau API gagal/timeout, kembalikan None --
    UI harus siap menampilkan fallback, bukan crash.
    """
    today_str = timezone.localdate().isoformat()
    cache_key = f"jadwal_sholat_{school.id}_{today_str}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        resp = requests.get(
            "https://api.aladhan.com/v1/timings",
            params={"latitude": float(school.latitude), "longitude": float(school.longitude), "method": 20},
            timeout=5,
        )
        resp.raise_for_status()
        timings = resp.json()["data"]["timings"]
        jadwal = [
            {"nama": "Subuh", "jam": timings["Fajr"]},
            {"nama": "Dzuhur", "jam": timings["Dhuhr"]},
            {"nama": "Ashar", "jam": timings["Asr"]},
            {"nama": "Maghrib", "jam": timings["Maghrib"]},
            {"nama": "Isya", "jam": timings["Isha"]},
        ]
        cache.set(cache_key, jadwal, 60 * 60 * 12)
        return jadwal
    except Exception:
        return None