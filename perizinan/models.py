# Simpan sebagai: perizinan/models.py

from django.conf import settings
from django.db import models

from akademik.models import Guru, Siswa


class PengajuanIzin(models.Model):
    class DiajukanOleh(models.TextChoices):
        SISWA = "siswa", "Siswa"
        ORANG_TUA = "orang_tua", "Orang Tua"

    class Jenis(models.TextChoices):
        SAKIT = "sakit", "Sakit"
        IZIN_KELUARGA = "izin_keluarga", "Izin Keperluan Keluarga"
        LAINNYA = "lainnya", "Izin Lainnya"

    class Status(models.TextChoices):
        MENUNGGU = "menunggu", "Menunggu"
        DISETUJUI = "disetujui", "Disetujui"
        DITOLAK = "ditolak", "Ditolak"

    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE, related_name="pengajuan_izin")
    diajukan_oleh = models.CharField(max_length=15, choices=DiajukanOleh.choices)
    diajukan_oleh_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    jenis = models.CharField(max_length=20, choices=Jenis.choices)
    tanggal_mulai = models.DateField()
    tanggal_selesai = models.DateField()
    keterangan = models.TextField(blank=True)
    bukti = models.FileField(upload_to="bukti_izin/%Y/%m/", null=True, blank=True)

    status = models.CharField(max_length=15, choices=Status.choices, default=Status.MENUNGGU)
    ditinjau_oleh = models.ForeignKey(
        Guru, on_delete=models.SET_NULL, null=True, blank=True, related_name="izin_ditinjau"
    )
    catatan_peninjau = models.TextField(blank=True)

    # Audit trail sederhana -- "Submitted By" itu sudah kepenuhi lewat
    # diajukan_oleh + diajukan_oleh_user di atas. Ini "Last Modified By":
    # siapa TERAKHIR menyentuh record ini (bisa siswa, orang tua, guru,
    # atau admin), penting kalau nanti ada dispute soal siapa ubah apa.
    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="izin_terakhir_diubah",
    )

    dibuat_pada = models.DateTimeField(auto_now_add=True)
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pengajuan Izin"
        verbose_name_plural = "Pengajuan Izin"
        ordering = ["-dibuat_pada"]

    def __str__(self):
        return f"{self.siswa.nama} - {self.get_jenis_display()} ({self.get_status_display()})"


class PengajuanIzinGuru(models.Model):
    """
    Pengajuan izin Guru. Beda dari PengajuanIzin (siswa): approver-nya
    Admin (bukan sesama guru), makanya ditinjau_oleh pakai User langsung
    (bisa Admin), bukan model Guru.
    """

    class Jenis(models.TextChoices):
        SAKIT = "sakit", "Sakit"
        IZIN_KELUARGA = "izin_keluarga", "Izin Keperluan Keluarga"
        LAINNYA = "lainnya", "Izin Lainnya"

    class Status(models.TextChoices):
        MENUNGGU = "menunggu", "Menunggu"
        DISETUJUI = "disetujui", "Disetujui"
        DITOLAK = "ditolak", "Ditolak"

    guru = models.ForeignKey(Guru, on_delete=models.CASCADE, related_name="pengajuan_izin")
    jenis = models.CharField(max_length=20, choices=Jenis.choices)
    tanggal_mulai = models.DateField()
    tanggal_selesai = models.DateField()
    keterangan = models.TextField(blank=True)
    bukti = models.FileField(upload_to="bukti_izin_guru/%Y/%m/", null=True, blank=True)

    status = models.CharField(max_length=15, choices=Status.choices, default=Status.MENUNGGU)
    ditinjau_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="izin_guru_ditinjau",
    )
    catatan_peninjau = models.TextField(blank=True)

    dibuat_pada = models.DateTimeField(auto_now_add=True)
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pengajuan Izin Guru"
        verbose_name_plural = "Pengajuan Izin Guru"
        ordering = ["-dibuat_pada"]

    def __str__(self):
        return f"{self.guru.nama} - {self.get_jenis_display()} ({self.get_status_display()})"