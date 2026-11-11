import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Perfil


def validar_rut(rut):
    limpio = re.sub(r'[.\s]', '', rut).upper()
    if not re.fullmatch(r'\d{7,8}-[\dK]', limpio):
        raise forms.ValidationError('Formato de RUT inválido. Ej.: 12345678-5')
    cuerpo, dv = limpio.split('-')
    suma, factor = 0, 2
    for d in reversed(cuerpo):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    esperado = 11 - (suma % 11)
    esperado = '0' if esperado == 11 else 'K' if esperado == 10 else str(esperado)
    if dv != esperado:
        raise forms.ValidationError('El dígito verificador del RUT no es válido.')
    return limpio


class RegistroForm(UserCreationForm):
    first_name = forms.CharField(label='Nombre', max_length=50)
    last_name = forms.CharField(label='Apellido', max_length=50)
    email = forms.EmailField(label='Correo electrónico')
    rut = forms.CharField(label='RUT', max_length=12)
    telefono = forms.CharField(label='Teléfono', max_length=20, required=False)
    prevision = forms.ChoiceField(label='Previsión', choices=Perfil.Prevision.choices)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            clase = 'form-select' if isinstance(campo.widget, forms.Select) else 'form-control'
            campo.widget.attrs['class'] = clase

    def clean_rut(self):
        rut = validar_rut(self.cleaned_data['rut'])
        if Perfil.objects.filter(rut=rut).exists():
            raise forms.ValidationError('Este RUT ya está registrado.')
        return rut

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este correo ya está registrado.')
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            Perfil.objects.create(
                usuario=user, rut=self.cleaned_data['rut'],
                telefono=self.cleaned_data['telefono'],
                prevision=self.cleaned_data['prevision'])
        return user


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs['class'] = 'form-control'
