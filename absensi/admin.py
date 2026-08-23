from django.contrib import admin

from .models import AbsensiHarian, AbsensiSholat, HalanganSholat, SesiSholat


@admin.register(SesiSholat)
class SesiSholatAdmin(admin.ModelAdmin):
    list_display = ("nama_sholat", "school", "aktif", "jendela_mulai", "jendela_selesai")
    list_filter = ("school", "aktif")


@admin.register(AbsensiHarian)
class AbsensiHarianAdmin(admin.ModelAdmin):
    list_display = ("siswa", "tanggal", "jam_masuk", "jam_pulang", "status")
    list_filter = ("status", "tanggal")
    search_fields = ("siswa__nama", "siswa__nis")
    date_hierarchy = "tanggal"


@admin.register(AbsensiSholat)
class AbsensiSholatAdmin(admin.ModelAdmin):
    list_display = ("siswa", "sesi_sholat", "tanggal", "hadir")
    list_filter = ("sesi_sholat", "hadir", "tanggal")
    search_fields = ("siswa__nama",)


@admin.register(HalanganSholat)
class HalanganSholatAdmin(admin.ModelAdmin):
    list_display = ("siswa", "tanggal_mulai", "tanggal_selesai")
    search_fields = ("siswa__nama",)