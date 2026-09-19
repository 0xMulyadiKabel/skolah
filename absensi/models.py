# Simpan sebagai: absensi/models.py

from django.conf import settings
from django.db import models

from accounts.models import School
from akademik.models import Guru, Siswa


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
        SELFIE_LOKASI = "selfie_lokasi", "Selfie + Lokasi GPS"
        BARCODE_KARTU = "barcode_kartu", "Barcode Kartu Siswa"

    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE, related_name="absensi_harian")
    tanggal = models.DateField()

    jam_masuk = models.TimeField(null=True, blank=True)
    metode_masuk = models.CharField(max_length=20, choices=Metode.choices, null=True, blank=True)
    lokasi_valid_masuk = models.BooleanField(default=False)
    foto_masuk = models.ImageField(
        upload_to="absensi_selfie/%Y/%m/%d/", null=True, blank=True,
        help_text="Selfie saat absen masuk, buat bukti visual kalau ada kecurigaan/perlu dicek manual guru piket.",
    )

    jam_pulang = models.TimeField(null=True, blank=True)
    metode_pulang = models.CharField(max_length=20, choices=Metode.choices, null=True, blank=True)
    lokasi_valid_pulang = models.BooleanField(default=False)
    foto_pulang = models.ImageField(upload_to="absensi_selfie/%Y/%m/%d/", null=True, blank=True)

    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ALPA)

    # Jejak koreksi manual -- diisi cuma kalau baris ini pernah diubah/dibuat
    # lewat fitur Koreksi Absensi (bukan hasil scan QR siswa sendiri). Ini
    # yang jadi bukti akuntabilitas: siapa yang override, kapan, kenapa.
    dikoreksi_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="absensi_dikoreksi",
    )
    dikoreksi_pada = models.DateTimeField(null=True, blank=True)
    catatan_koreksi = models.CharField(max_length=255, blank=True)

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
    foto = models.ImageField(upload_to="absensi_sholat_selfie/%Y/%m/%d/", null=True, blank=True)
    lokasi_valid = models.BooleanField(default=False)

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


class HariLibur(models.Model):
    """
    Kalender Akademik. Tanggal yang terdaftar di sini dianggap BUKAN hari
    sekolah aktif, meskipun jatuh di hari yang biasanya aktif (mis. Senin
    libur nasional). Dipakai supaya Dashboard/Laporan tidak salah anggap
    siswa 'belum absen' di hari yang memang tidak ada sekolah.
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="hari_libur_list")
    tanggal = models.DateField()
    keterangan = models.CharField(max_length=200)

    class Meta:
        verbose_name = "Hari Libur"
        verbose_name_plural = "Hari Libur"
        unique_together = ("school", "tanggal")
        ordering = ["-tanggal"]

    def __str__(self):
        return f"{self.tanggal} \u2014 {self.keterangan}"


class AbsensiGuru(models.Model):
    """
    Kehadiran Guru -- sengaja model TERPISAH dari AbsensiHarian (siswa),
    bukan digabung pakai polymorphic/generic FK. Alasannya: kebutuhan Guru
    lebih sederhana (cuma masuk/pulang, tanpa sholat jamaah, tanpa lokasi
    GPS/selfie -- cuma kartu lewat Kiosk), jadi struktur terpisah lebih
    jelas dibanding maksain satu tabel buat dua kebutuhan yang beda bentuk.
    """

    class Status(models.TextChoices):
        HADIR = "hadir", "Hadir Tepat Waktu"
        TERLAMBAT = "terlambat", "Terlambat"
        ALPA = "alpa", "Tanpa Keterangan"
        IZIN = "izin", "Izin/Sakit"

    class Metode(models.TextChoices):
        BARCODE_KARTU = "barcode_kartu", "Kartu (Kiosk)"

    guru = models.ForeignKey(Guru, on_delete=models.CASCADE, related_name="absensi_guru")
    tanggal = models.DateField()

    jam_masuk = models.TimeField(null=True, blank=True)
    metode_masuk = models.CharField(max_length=20, choices=Metode.choices, null=True, blank=True)

    jam_pulang = models.TimeField(null=True, blank=True)
    metode_pulang = models.CharField(max_length=20, choices=Metode.choices, null=True, blank=True)

    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ALPA)

    # Jejak koreksi manual -- sama pola seperti AbsensiHarian, Admin bisa
    # override kalau ada kendala (kartu hilang, kiosk error, dsb).
    dikoreksi_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="absensi_guru_dikoreksi",
    )
    dikoreksi_pada = models.DateTimeField(null=True, blank=True)
    catatan_koreksi = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Absensi Guru"
        verbose_name_plural = "Absensi Guru"
        unique_together = ("guru", "tanggal")
        ordering = ["-tanggal"]

    def __str__(self):
        return f"{self.guru.nama} - {self.tanggal} ({self.get_status_display()})"