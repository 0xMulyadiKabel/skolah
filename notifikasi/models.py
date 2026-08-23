from django.conf import settings
from django.db import models

from akademik.models import Siswa


class Notifikasi(models.Model):
    """
    Satu baris = satu notifikasi yang tampil di tab 'Notifikasi' portal
    Orang Tua. Dibuat sistem otomatis (bukan diketik manual), lalu (kalau
    integrasi WhatsApp API sudah dipilih -- lihat CLAUDE.md bagian 6, masih
    belum final) juga dikirim sebagai pesan WhatsApp memakai isi yang sama.
    """

    class Jenis(models.TextChoices):
        ABSEN_MASUK = "absen_masuk", "Absen Masuk"
        SHOLAT_HADIR = "sholat_hadir", "Hadir Sholat Berjamaah"
        SHOLAT_ALPA = "sholat_alpa", "Tidak Ikut Sholat Tanpa Keterangan"
        IZIN_DISETUJUI = "izin_disetujui", "Pengajuan Izin Disetujui"
        IZIN_DITOLAK = "izin_ditolak", "Pengajuan Izin Ditolak"
        BELUM_ABSEN = "belum_absen", "Belum Absen Sampai Batas Waktu"

    penerima = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifikasi_list",
        help_text="User Orang Tua yang menerima notifikasi ini.",
    )
    siswa = models.ForeignKey(
        Siswa, on_delete=models.CASCADE, related_name="notifikasi_terkait",
        help_text="Notifikasi ini soal anak yang mana.",
    )
    jenis = models.CharField(max_length=20, choices=Jenis.choices)
    judul = models.CharField(max_length=150)
    deskripsi = models.CharField(max_length=255, blank=True)

    sudah_dibaca = models.BooleanField(default=False)
    terkirim_whatsapp = models.BooleanField(
        default=False,
        help_text="Menandakan sudah/belum terkirim via WhatsApp API (bukan cuma tercatat di sistem).",
    )

    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notifikasi"
        verbose_name_plural = "Notifikasi"
        ordering = ["-dibuat_pada"]

    def __str__(self):
        return f"{self.judul} - {self.siswa.nama}"