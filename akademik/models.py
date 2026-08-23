from django.conf import settings
from django.db import models

from accounts.models import School


class Guru(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="guru_list")
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nama = models.CharField(max_length=150)
    email = models.EmailField()

    class Meta:
        verbose_name = "Guru"
        verbose_name_plural = "Guru"

    def __str__(self):
        return self.nama


class Kelas(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="kelas_list")
    nama_kelas = models.CharField(max_length=30)
    wali_kelas = models.ForeignKey(
        Guru, on_delete=models.SET_NULL, null=True, blank=True, related_name="kelas_diampu"
    )

    class Meta:
        verbose_name = "Kelas"
        verbose_name_plural = "Kelas"
        unique_together = ("school", "nama_kelas")

    def __str__(self):
        return self.nama_kelas


class Siswa(models.Model):
    class JenisKelamin(models.TextChoices):
        LAKI = "L", "Laki-laki"
        PEREMPUAN = "P", "Perempuan"

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="siswa_list")
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    nis = models.CharField(max_length=20, null=True, blank=True)
    kode_kartu = models.CharField(
        max_length=50, null=True, blank=True,
        help_text="Kode unik barcode yang tercetak di kartu siswa fisik (metode absen alternatif selain QR HP).",
    )
    nama = models.CharField(max_length=150)
    kelas = models.ForeignKey(Kelas, on_delete=models.PROTECT, related_name="siswa_list")
    jenis_kelamin = models.CharField(max_length=1, choices=JenisKelamin.choices)
    aktif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Siswa"
        verbose_name_plural = "Siswa"
        constraints = [
            models.UniqueConstraint(
                fields=["school", "nis"],
                name="unique_nis_per_school",
                condition=models.Q(nis__isnull=False),
            ),
            models.UniqueConstraint(
                fields=["school", "kode_kartu"],
                name="unique_kode_kartu_per_school",
                condition=models.Q(kode_kartu__isnull=False),
            ),
        ]

    def __str__(self):
        return f"{self.nama} ({self.kelas})"


class OrangTua(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="orangtua_list")
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nama = models.CharField(max_length=150)
    no_hp = models.CharField(max_length=20)
    anak = models.ManyToManyField(Siswa, related_name="orang_tua_list")

    class Meta:
        verbose_name = "Orang Tua"
        verbose_name_plural = "Orang Tua"

    def __str__(self):
        return self.nama