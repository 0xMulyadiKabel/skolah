from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import School
from accounts.views import admin_required

from .models import PengajuanIzin


def _get_school(request):
    return request.user.school or School.objects.first()


@admin_required
def izin_list(request):
    school = _get_school(request)
    status = request.GET.get("status", "")

    izin_qs = (
        PengajuanIzin.objects.filter(siswa__school=school)
        .select_related("siswa", "siswa__kelas", "ditinjau_oleh")
        .order_by("-dibuat_pada")
    )
    if status:
        izin_qs = izin_qs.filter(status=status)

    context = {
        "page_title": "Approval Pengajuan Izin",
        "izin_list": izin_qs,
        "status_selected": status,
    }
    return render(request, "perizinan/izin_list.html", context)


@admin_required
def izin_setujui(request, pk):
    izin = get_object_or_404(PengajuanIzin, pk=pk, siswa__school=_get_school(request))
    if request.method == "POST":
        izin.status = PengajuanIzin.Status.DISETUJUI
        izin.save()
        messages.success(request, f"Pengajuan izin {izin.siswa.nama} disetujui.")
    return redirect("perizinan:izin_list")


@admin_required
def izin_tolak(request, pk):
    izin = get_object_or_404(PengajuanIzin, pk=pk, siswa__school=_get_school(request))
    if request.method == "POST":
        izin.status = PengajuanIzin.Status.DITOLAK
        izin.save()
        messages.success(request, f"Pengajuan izin {izin.siswa.nama} ditolak.")
    return redirect("perizinan:izin_list")


@admin_required
def izin_detail(request, pk):
    izin = get_object_or_404(
        PengajuanIzin.objects.select_related("siswa", "siswa__kelas", "ditinjau_oleh"),
        pk=pk, siswa__school=_get_school(request),
    )
    return render(request, "perizinan/izin_detail.html", {"page_title": "Detail Pengajuan Izin", "izin": izin})