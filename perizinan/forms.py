# Simpan sebagai: perizinan/forms.py

from django import forms

from .models import PengajuanIzin, PengajuanIzinGuru

INPUT_CLASS = "w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-emerald-700 focus:outline-none text-sm"


class PengajuanIzinForm(forms.ModelForm):
    class Meta:
        model = PengajuanIzin
        fields = ["jenis", "tanggal_mulai", "tanggal_selesai", "keterangan", "bukti"]
        widgets = {
            "tanggal_mulai": forms.DateInput(attrs={"type": "date"}),
            "tanggal_selesai": forms.DateInput(attrs={"type": "date"}),
            "keterangan": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs["class"] = INPUT_CLASS

    def clean(self):
        cleaned = super().clean()
        mulai = cleaned.get("tanggal_mulai")
        selesai = cleaned.get("tanggal_selesai")
        if mulai and selesai and selesai < mulai:
            raise forms.ValidationError("Tanggal selesai tidak boleh sebelum tanggal mulai.")
        return cleaned


class PengajuanIzinGuruForm(forms.ModelForm):
    class Meta:
        model = PengajuanIzinGuru
        fields = ["jenis", "tanggal_mulai", "tanggal_selesai", "keterangan", "bukti"]
        widgets = {
            "tanggal_mulai": forms.DateInput(attrs={"type": "date"}),
            "tanggal_selesai": forms.DateInput(attrs={"type": "date"}),
            "keterangan": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs["class"] = INPUT_CLASS

    def clean(self):
        cleaned = super().clean()
        mulai = cleaned.get("tanggal_mulai")
        selesai = cleaned.get("tanggal_selesai")
        if mulai and selesai and selesai < mulai:
            raise forms.ValidationError("Tanggal selesai tidak boleh sebelum tanggal mulai.")
        return cleaned