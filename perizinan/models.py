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

    dibuat_pada = models.DateTimeField(auto_now_add=True)
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pengajuan Izin"
        verbose_name_plural = "Pengajuan Izin"
        ordering = ["-dibuat_pada"]

    def __str__(self):
        return f"{self.siswa.nama} - {self.get_jenis_display()} ({self.get_status_display()})"