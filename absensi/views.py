import csv
from datetime import date

from django.http import HttpResponse
from django.shortcuts import render

from accounts.models import School
from accounts.views import admin_required
from akademik.models import Kelas, Siswa

from .models import AbsensiHarian


def _get_school(request):
    return request.user.school or School.objects.first()


def _hitung_rekap(school):
    today = date.today()
    awal_bulan = today.replace(day=1)

    rows = []
    for kelas in Kelas.objects.filter(school=school).order_by("nama_kelas"):
        total_siswa = Siswa.objects.filter(kelas=kelas, aktif=True).count()
        absensi = AbsensiHarian.objects.filter(
            siswa__kelas=kelas, tanggal__gte=awal_bulan, tanggal__lte=today
        )
        hadir = absensi.filter(status__in=["hadir", "terlambat"]).count()
        izin = absensi.filter(status="izin").count()
        alpa = absensi.filter(status="alpa").count()
        total_tercatat = hadir + izin + alpa
        persen = round((hadir / total_tercatat) * 100) if total_tercatat else 0
        rows.append(dict(kelas=kelas, total_siswa=total_siswa, hadir=hadir, izin=izin, alpa=alpa, persen=persen))
    return rows, awal_bulan


@admin_required
def laporan_sekolah(request):
    school = _get_school(request)
    rows, awal_bulan = _hitung_rekap(school)
    context = {
        "page_title": "Laporan Kehadiran Sekolah",
        "rows": rows,
        "periode_label": awal_bulan.strftime("%B %Y"),
    }
    return render(request, "absensi/laporan_sekolah.html", context)


@admin_required
def laporan_export_csv(request):
    school = _get_school(request)
    rows, awal_bulan = _hitung_rekap(school)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="laporan_{awal_bulan.strftime("%Y_%m")}.csv"'
    writer = csv.writer(response)
    writer.writerow(["Kelas", "Total Siswa", "Hadir", "Izin/Sakit", "Alpa", "% Kehadiran"])
    for r in rows:
        writer.writerow([r["kelas"].nama_kelas, r["total_siswa"], r["hadir"], r["izin"], r["alpa"], f'{r["persen"]}%'])
    return response