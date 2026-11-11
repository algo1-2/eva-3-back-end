from django import forms

from .models import Prestacion


class PrestacionForm(forms.ModelForm):
    class Meta:
        model = Prestacion
        fields = ['especialidad', 'codigo', 'nombre', 'descripcion', 'requisitos',
                  'arancel', 'duracion_minutos', 'cupos_diarios', 'estado', 'imagen', 'activo']
        widgets = {
            'especialidad': forms.Select(attrs={'class': 'form-select'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej.: LAB-001'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'requisitos': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'arancel': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'duracion_minutos': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'cupos_diarios': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_codigo(self):
        codigo = self.cleaned_data['codigo'].strip().upper()
        qs = Prestacion.objects.filter(codigo__iexact=codigo)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe una prestación con este código.')
        return codigo

    def clean_arancel(self):
        arancel = self.cleaned_data['arancel']
        if arancel < 0:
            raise forms.ValidationError('El arancel no puede ser negativo.')
        return arancel

    def clean_cupos_diarios(self):
        cupos = self.cleaned_data['cupos_diarios']
        if cupos < 0:
            raise forms.ValidationError('Los cupos no pueden ser negativos.')
        return cupos

    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        if imagen and hasattr(imagen, 'size') and imagen.size > 2 * 1024 * 1024:
            raise forms.ValidationError('La imagen no puede superar los 2 MB.')
        return imagen
