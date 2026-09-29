# Simpan sebagai: accounts/forms.py

from django import forms

from .models import School

INPUT_CLASS = "w-full px-3 py-2.5 rounded-lg border border-gray-200 focus:border-emerald-700 focus:outline-none text-sm"
KOORDINAT_CLASS = "px-3 py-2 rounded-lg border border-gray-200 text-xs font-mono"
KOORDINAT_FIELDS = {"latitude", "longitude", "latitude_masjid", "longitude_masjid"}


class SchoolSettingsForm(forms.ModelForm):
    class Meta:
        model = School
        fields = [
            "jam_masuk", "jam_pulang", "toleransi_keterlambatan_menit",
            "metode_verifikasi",
            "latitude", "longitude", "radius_geofence_meter",
            "latitude_masjid", "longitude_masjid", "radius_masjid_meter",
            "aktif_senin", "aktif_selasa", "aktif_rabu", "aktif_kamis",
            "aktif_jumat", "aktif_sabtu", "aktif_minggu",
        ]
        widgets = {
            "latitude": forms.NumberInput(attrs={"step": "0.0000001"}),
            "longitude": forms.NumberInput(attrs={"step": "0.0000001"}),
            "latitude_masjid": forms.NumberInput(attrs={"step": "0.0000001"}),
            "longitude_masjid": forms.NumberInput(attrs={"step": "0.0000001"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in KOORDINAT_FIELDS:
                # localize=False WAJIB di sini -- tanpa ini, Django render
                # angka desimal pakai KOMA (karena LANGUAGE_CODE='id') tapi
                # minta submit balik pakai TITIK, round-trip-nya gagal
                # sendiri persis kayak bug yang kejadian kemarin.
                field.localize = False
                field.widget.attrs["class"] = KOORDINAT_CLASS
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "h-4 w-4 rounded border-gray-300"
            else:
                field.widget.attrs["class"] = INPUT_CLASS
            field.widget.attrs["id"] = f"id_{name}"  # dipakai tombol "Pakai lokasi saya"