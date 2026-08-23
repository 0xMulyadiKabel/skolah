from django.contrib.auth.models import AbstractUser
from django.db import models


class School(models.Model):
    class MetodeVerifikasi(models.TextChoices):
        QR_DAN_LOKASI = "qr_lokasi", "QR Code + Lokasi GPS"
        LOKASI_SAJA = "lokasi", "Lokasi GPS Saja"
        QR_SAJA = "qr", "QR Code Saja"

    nama = models.CharField(max_length=150)
    alamat = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)

    jam_masuk = models.TimeField(default="06:45")
    jam_pulang = models.TimeField(default="15:30")
    toleransi_keterlambatan_menit = models.PositiveSmallIntegerField(default=15)
    radius_geofence_meter = models.PositiveSmallIntegerField(default=100)
    metode_verifikasi = models.CharField(
        max_length=15, choices=MetodeVerifikasi.choices, default=MetodeVerifikasi.QR_DAN_LOKASI
    )

    # Hari aktif sekolah -- disimpan sebagai 7 boolean terpisah (bukan satu
    # field JSON/array) supaya gampang dipakai langsung di query & filter
    # Django Admin, dan gampang dibaca siapapun yang buka database manual.
    aktif_senin = models.BooleanField(default=True)
    aktif_selasa = models.BooleanField(default=True)
    aktif_rabu = models.BooleanField(default=True)
    aktif_kamis = models.BooleanField(default=True)
    aktif_jumat = models.BooleanField(default=True)
    aktif_sabtu = models.BooleanField(default=False)
    aktif_minggu = models.BooleanField(default=False)

    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sekolah"
        verbose_name_plural = "Sekolah"

    def __str__(self):
        return self.nama


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin Sekolah"
        GURU = "guru", "Guru / Wali Kelas"
        ORANG_TUA = "orang_tua", "Orang Tua"
        SISWA = "siswa", "Siswa"

    role = models.CharField(max_length=20, choices=Role.choices)
    school = models.ForeignKey(
        School, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"