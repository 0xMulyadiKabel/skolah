from django.urls import path

from . import views

app_name = "akademik"

urlpatterns = [
    path("siswa/", views.siswa_list, name="siswa_list"),
    path("siswa/tambah/", views.siswa_create, name="siswa_create"),
    path("siswa/<int:pk>/edit/", views.siswa_update, name="siswa_update"),
    path("siswa/nonaktifkan-massal/", views.siswa_bulk_nonaktifkan, name="siswa_bulk_nonaktifkan"),
    path("siswa/<int:pk>/buat-akun/", views.siswa_buat_akun, name="siswa_buat_akun"),

    path("kelas/", views.kelas_list, name="kelas_list"),
    path("kelas/tambah/", views.kelas_create, name="kelas_create"),
    path("kelas/<int:pk>/edit/", views.kelas_update, name="kelas_update"),

    path("akun/guru/", views.akun_guru_list, name="akun_guru_list"),
    path("akun/guru/tambah/", views.akun_guru_create, name="akun_guru_create"),
    path("akun/guru/<int:pk>/edit/", views.akun_guru_edit, name="akun_guru_edit"),
    path("akun/guru/<int:pk>/reset/", views.akun_guru_reset, name="akun_guru_reset"),
    path("akun/guru/<int:pk>/toggle/", views.akun_guru_toggle_active, name="akun_guru_toggle"),

    path("akun/orangtua/", views.akun_ortu_list, name="akun_ortu_list"),
    path("akun/orangtua/tambah/", views.akun_ortu_create, name="akun_ortu_create"),
    path("akun/orangtua/<int:pk>/edit/", views.akun_ortu_edit, name="akun_ortu_edit"),
    path("akun/orangtua/<int:pk>/reset/", views.akun_ortu_reset, name="akun_ortu_reset"),
    path("akun/orangtua/<int:pk>/toggle/", views.akun_ortu_toggle_active, name="akun_ortu_toggle"),
]