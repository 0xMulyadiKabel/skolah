from django.contrib import admin

from .models import Guru, Kelas, OrangTua, Siswa


@admin.register(Guru)
class GuruAdmin(admin.ModelAdmin):
    list_display = ("nama", "email", "school")
    search_fields = ("nama", "email")
    list_filter = ("school",)


@admin.register(Kelas)
class KelasAdmin(admin.ModelAdmin):
    list_display = ("nama_kelas", "wali_kelas", "school")
    list_filter = ("school",)


@admin.register(Siswa)
class SiswaAdmin(admin.ModelAdmin):
    list_display = ("nama", "nis", "kelas", "jenis_kelamin", "aktif")
    search_fields = ("nama", "nis")
    list_filter = ("kelas", "aktif", "jenis_kelamin")


@admin.register(OrangTua)
class OrangTuaAdmin(admin.ModelAdmin):
    list_display = ("nama", "no_hp", "school")
    search_fields = ("nama", "no_hp")
    filter_horizontal = ("anak",)