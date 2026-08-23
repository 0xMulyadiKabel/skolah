from django.contrib import admin

from .models import PengajuanIzin


@admin.register(PengajuanIzin)
class PengajuanIzinAdmin(admin.ModelAdmin):
    list_display = ("siswa", "jenis", "diajukan_oleh", "tanggal_mulai", "tanggal_selesai", "status")
    list_filter = ("status", "jenis", "diajukan_oleh")
    search_fields = ("siswa__nama",)
    date_hierarchy = "tanggal_mulai"

    actions = ["setujui_izin", "tolak_izin"]

    @admin.action(description="Setujui pengajuan izin terpilih")
    def setujui_izin(self, request, queryset):
        queryset.update(status=PengajuanIzin.Status.DISETUJUI)

    @admin.action(description="Tolak pengajuan izin terpilih")
    def tolak_izin(self, request, queryset):
        queryset.update(status=PengajuanIzin.Status.DITOLAK)