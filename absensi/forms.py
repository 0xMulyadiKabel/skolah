# Simpan sebagai: absensi/forms.py

from django import forms

from .models import HariLibur

INPUT_CLASS = "w-full px-3 py-2.5 rounded-lg border border-gray-200 focus:border-emerald-700 focus:outline-none text-sm"


class HariLiburForm(forms.ModelForm):
    class Meta:
        model = HariLibur
        fields = ["tanggal", "keterangan"]
        widgets = {"tanggal": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASS


class KoreksiAbsensiForm(forms.Form):
    STATUS_CHOICES = [
        ("hadir", "Hadir Tepat Waktu"),
        ("terlambat", "Terlambat"),
        ("izin", "Izin/Sakit"),
        ("alpa", "Tanpa Keterangan"),
    ]
    status = forms.ChoiceField(choices=STATUS_CHOICES, label="Status")
    jam_masuk = forms.TimeField(required=False, label="Jam Masuk (opsional)", widget=forms.TimeInput(attrs={"type": "time"}))
    jam_pulang = forms.TimeField(required=False, label="Jam Pulang (opsional)", widget=forms.TimeInput(attrs={"type": "time"}))
    catatan = forms.CharField(required=True, label="Alasan Koreksi", widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASS