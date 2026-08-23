from django import forms

from .models import School

INPUT_CLASS = "w-full px-3 py-2.5 rounded-lg border border-gray-200 focus:border-emerald-700 focus:outline-none text-sm"


class SchoolSettingsForm(forms.ModelForm):
    class Meta:
        model = School
        fields = [
            "jam_masuk", "jam_pulang", "toleransi_keterlambatan_menit",
            "metode_verifikasi", "radius_geofence_meter",
            "aktif_senin", "aktif_selasa", "aktif_rabu", "aktif_kamis",
            "aktif_jumat", "aktif_sabtu", "aktif_minggu",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "h-4 w-4 rounded border-gray-300"
            else:
                field.widget.attrs["class"] = INPUT_CLASS