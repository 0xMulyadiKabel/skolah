from django.db import models

from accounts.models import School
from akademik.models import Siswa


class SesiSholat(models.Model):
    class NamaSholat(models.TextChoices):
        SUBUH = "subuh", "Subuh"
        DZUHUR = "dzuhur", "Dzuhur"
        ASHAR = "ashar", "Ashar"
        MAGHRIB = "maghrib", "Maghrib"
        ISYA = "isya", "Isya"

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="sesi_sholat_list")
    nama_sholat = models.CharField(max_length=10, choices=NamaSholat.choices)
    aktif = models.BooleanField(default=False)
    jendela_mulai = models.TimeField(null=True, blank=True)
    jendela_selesai = models.TimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Sesi Sholat"
        verbose_name_plural = "Sesi Sholat"
        unique_together = ("school", "nama_sholat")

    def __str__(self):
        status = "aktif" if self.aktif else "nonaktif"
        return f"{self.get_nama_sholat_display()} ({status})"


class AbsensiHarian(models.Model):
    class Status(models.TextChoices):
        HADIR = "hadir", "Hadir Tepat Waktu"
        TERLAMBAT = "terlambat", "Terlambat"
        ALPA = "alpa", "Tanpa Keterangan"
        IZIN = "izin", "Izin/Sakit"

    class Metode(models.TextChoices):
        QR_LOKASI = "qr_lokasi", "QR Code + Lokasi GPS"
        BARCODE_KARTU = "barcode_kartu", "Barcode Kartu Siswa"

    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE, related_name="absensi_harian")
    tanggal = models.DateField()

    jam_masuk = models.TimeField(null=True, blank=True)
    metode_masuk = models.CharField(max_length=20, choices=Metode.choices, null=True, blank=True)
    lokasi_valid_masuk = models.BooleanField(default=False)

    jam_pulang = models.TimeField(null=True, blank=True)
    metode_pulang = models.CharField(max_length=20, choices=Metode.choices, null=True, blank=True)
    lokasi_valid_pulang = models.BooleanField(default=False)

    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ALPA)

    class Meta:
        verbose_name = "Absensi Harian"
        verbose_name_plural = "Absensi Harian"
        unique_together = ("siswa", "tanggal")
        ordering = ["-tanggal"]

    def __str__(self):
        return f"{self.siswa.nama} - {self.tanggal} ({self.get_status_display()})"


class AbsensiSholat(models.Model):
    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE, related_name="absensi_sholat")
    sesi_sholat = models.ForeignKey(SesiSholat, on_delete=models.CASCADE)
    tanggal = models.DateField()
    waktu_absen = models.TimeField(null=True, blank=True)
    hadir = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Absensi Sholat"
        verbose_name_plural = "Absensi Sholat"
        unique_together = ("siswa", "sesi_sholat", "tanggal")
        ordering = ["-tanggal"]

    def __str__(self):
        return f"{self.siswa.nama} - {self.sesi_sholat.get_nama_sholat_display()} - {self.tanggal}"


class HalanganSholat(models.Model):
    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE, related_name="halangan_sholat")
    tanggal_mulai = models.DateField()
    tanggal_selesai = models.DateField()
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Halangan Sholat"
        verbose_name_plural = "Halangan Sholat"
        ordering = ["-tanggal_mulai"]

    def __str__(self):
        return f"{self.siswa.nama}: {self.tanggal_mulai} s/d {self.tanggal_selesai}"