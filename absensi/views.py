import csv
from datetime import date

from django.http import HttpResponse
from django.shortcuts import render

from accounts.utils import get_school
from accounts.views import admin_required
from akademik.models import Kelas, Siswa

from .models import AbsensiHarian
from .utils import generate_daily_token


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
    school = get_school(request)
    rows, awal_bulan = _hitung_rekap(school)
    context = {
        "page_title": "Laporan Kehadiran Sekolah",
        "rows": rows,
        "periode_label": awal_bulan.strftime("%B %Y"),
    }
    return render(request, "absensi/laporan_sekolah.html", context)


@admin_required
def laporan_export_csv(request):
    school = get_school(request)
    rows, awal_bulan = _hitung_rekap(school)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="laporan_{awal_bulan.strftime("%Y_%m")}.csv"'
    writer = csv.writer(response)
    writer.writerow(["Kelas", "Total Siswa", "Hadir", "Izin/Sakit", "Alpa", "% Kehadiran"])
    for r in rows:
        writer.writerow([r["kelas"].nama_kelas, r["total_siswa"], r["hadir"], r["izin"], r["alpa"], f'{r["persen"]}%'])
    return response


@admin_required
def gerbang_qr(request):
    school = get_school(request)
    context = {"page_title": "Tampilan QR Gerbang", "school": school}
    return render(request, "absensi/gerbang_qr.html", context)


@admin_required
def gerbang_qr_image(request):
    import io

    import qrcode

    school = get_school(request)
    token = generate_daily_token(school.id)
    payload = f"ABSEN:{school.id}:{token}"

    img = qrcode.make(payload)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return HttpResponse(buf.getvalue(), content_type="image/png")