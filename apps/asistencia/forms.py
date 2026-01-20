from django import forms
from .models import Vacacion, LicenciaMedica, User

class VacacionForm(forms.ModelForm):
    class Meta:
        model = Vacacion
        fields = ['trabajador', 'inicio', 'fin', 'comentario']
        widgets = {
            'inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'comentario': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'trabajador': forms.Select(attrs={'class': 'form-select'}),
        }

class LicenciaForm(forms.ModelForm):
    class Meta:
        model = LicenciaMedica
        fields = ['trabajador', 'inicio', 'fin', 'tipo', 'documento']
        widgets = {
            'inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'trabajador': forms.Select(attrs={'class': 'form-select'}),
            'documento': forms.FileInput(attrs={'class': 'form-control'}),
        }