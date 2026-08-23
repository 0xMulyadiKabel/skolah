from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import Guru, Kelas, OrangTua, Siswa

INPUT_CLASS = "w-full px-3 py-2.5 rounded-lg border border-gray-200 focus:border-emerald-700 focus:outline-none text-sm"


class AkunFormMixin:
    """
    Dipakai bareng oleh GuruAccountForm & OrangTuaAccountForm supaya validasi
    username dan password tidak ditulis dua kali. Bukan form sendiri --
    cuma kumpulan method clean_* yang di-"pinjam" lewat multiple inheritance.
    """

    def clean_username(self):
        username = self.cleaned_data["username"]
        if get_user_model().objects.filter(username=username).exists():
            raise forms.ValidationError("Username sudah dipakai, pilih yang lain.")
        return username

    def clean_password(self):
        password = self.cleaned_data["password"]
        try:
            # Ini fungsi bawaan Django, otomatis pakai aturan yang sudah
            # kita set di AUTH_PASSWORD_VALIDATORS (settings.py) -- minimal
            # panjang, tidak boleh mirip username, tidak boleh password umum
            # (mis. "password123", "12345678"), dan tidak boleh full angka.
            validate_password(password)
        except DjangoValidationError as exc:
            raise forms.ValidationError(exc.messages)
        return password


class SiswaForm(forms.ModelForm):
    class Meta:
        model = Siswa
        fields = ["nis", "kode_kartu", "nama", "kelas", "jenis_kelamin", "aktif"]

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school is not None:
            self.fields["kelas"].queryset = Kelas.objects.filter(school=school)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "h-4 w-4 rounded border-gray-300"
            else:
                field.widget.attrs["class"] = INPUT_CLASS


class GuruAccountForm(AkunFormMixin, forms.Form):
    username = forms.CharField(max_length=150, label="Username", validators=[UnicodeUsernameValidator()])
    password = forms.CharField(widget=forms.PasswordInput, label="Kata Sandi Awal")
    nama = forms.CharField(max_length=150, label="Nama Lengkap")
    email = forms.EmailField(label="Email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASS


class OrangTuaAccountForm(AkunFormMixin, forms.Form):
    username = forms.CharField(max_length=150, label="Username", validators=[UnicodeUsernameValidator()])
    password = forms.CharField(widget=forms.PasswordInput, label="Kata Sandi Awal")
    nama = forms.CharField(max_length=150, label="Nama Lengkap")
    no_hp = forms.CharField(max_length=20, label="No. HP / WhatsApp")
    anak = forms.ModelMultipleChoiceField(
        queryset=Siswa.objects.none(), label="Anak", widget=forms.SelectMultiple,
        help_text="Tahan Ctrl (atau Cmd di Mac) untuk pilih lebih dari satu anak.",
    )

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school is not None:
            self.fields["anak"].queryset = Siswa.objects.filter(school=school).order_by("nama")
        for name, field in self.fields.items():
            field.widget.attrs["class"] = INPUT_CLASS if name != "anak" else INPUT_CLASS + " h-40"


class GuruEditForm(forms.ModelForm):
    class Meta:
        model = Guru
        fields = ["nama", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASS


class OrangTuaEditForm(forms.ModelForm):
    class Meta:
        model = OrangTua
        fields = ["nama", "no_hp", "anak"]

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school is not None:
            self.fields["anak"].queryset = Siswa.objects.filter(school=school).order_by("nama")
        for name, field in self.fields.items():
            field.widget.attrs["class"] = INPUT_CLASS if name != "anak" else INPUT_CLASS + " h-40"


class KelasForm(forms.ModelForm):
    class Meta:
        model = Kelas
        fields = ["nama_kelas", "wali_kelas"]

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school is not None:
            self.fields["wali_kelas"].queryset = Guru.objects.filter(school=school)
        self.fields["wali_kelas"].required = False
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASS