from django.contrib import admin

from .models import Notifikasi


@admin.register(Notifikasi)
class NotifikasiAdmin(admin.ModelAdmin):
    list_display = ("judul", "siswa", "penerima", "jenis", "sudah_dibaca", "terkirim_whatsapp", "dibuat_pada")
    list_filter = ("jenis", "sudah_dibaca", "terkirim_whatsapp")
    search_fields = ("judul", "siswa__nama")
    date_hierarchy = "dibuat_pada"