# Simpan sebagai: perizinan/utils.py

from django.utils import timezone


def cek_izin_overlap_aktif(siswa, tanggal_mulai, tanggal_selesai, exclude_pk=None):
    """
    True kalau siswa ini SUDAH punya pengajuan izin lain yang statusnya
    masih aktif (Menunggu/Disetujui) dan rentang tanggalnya tumpang-tindih
    dengan yang mau diajukan/diedit sekarang.

    Sengaja TIDAK menghitung pengajuan berstatus Ditolak -- sesuai business
    rule: kalau pengajuan sebelumnya ditolak, siswa/orang tua boleh
    mengajukan ulang untuk tanggal yang sama.
    """
    from .models import PengajuanIzin

    qs = PengajuanIzin.objects.filter(
        siswa=siswa,
        status__in=[PengajuanIzin.Status.MENUNGGU, PengajuanIzin.Status.DISETUJUI],
        tanggal_mulai__lte=tanggal_selesai,
        tanggal_selesai__gte=tanggal_mulai,
    )
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def terapkan_edit_pengajuan_izin(pengajuan, user):
    """
    Dipanggil SETELAH form.save(commit=False) tapi SEBELUM pengajuan.save()
    beneran, waktu siswa/orang tua mengedit pengajuan yang sudah ada.
    Efeknya: apapun status sebelumnya (Menunggu/Disetujui/Ditolak), begitu
    diedit datanya berubah, status WAJIB balik jadi Menunggu lagi -- guru
    harus approve ulang. Ini sesuai business rule eksplisit di catatan
    perbaikan: jangan pertahankan status Disetujui setelah data pengajuan
    berubah.
    """
    from .models import PengajuanIzin

    pengajuan.status = PengajuanIzin.Status.MENUNGGU
    pengajuan.ditinjau_oleh = None
    pengajuan.catatan_peninjau = ""
    pengajuan.last_modified_by = user
    return pengajuan