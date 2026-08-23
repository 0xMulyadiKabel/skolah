from .models import School


def get_school(request):
    """
    Kembalikan sekolah yang dikelola admin yang sedang login, atau None
    kalau belum ada School sama sekali di database (fresh install).
    Semua view di app lain (akademik, absensi, perizinan, dashboard)
    pakai fungsi ini, BUKAN nulis versi sendiri-sendiri lagi.
    """
    return request.user.school or School.objects.first()