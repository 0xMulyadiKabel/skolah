import hashlib
import hmac
import math

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone


def generate_daily_token(school_id):
    """
    Token QR hari ini untuk 1 sekolah. Dihitung dari school_id + tanggal +
    SECRET_KEY Django -- otomatis beda tiap hari tanpa perlu disimpan ke
    database atau di-generate ulang pakai cron job. Siapa pun yang tidak
    tahu SECRET_KEY tidak bisa menebak token besok.
    """
    today_str = timezone.localdate().isoformat()
    message = f"{school_id}:{today_str}"
    return hmac.new(settings.SECRET_KEY.encode(), message.encode(), hashlib.sha256).hexdigest()[:16]


def haversine_distance(lat1, lon1, lat2, lon2):
    """Jarak garis lurus (meter) antara dua titik koordinat GPS."""
    R = 6371000  # radius Bumi dalam meter
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


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