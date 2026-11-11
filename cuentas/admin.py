from django.contrib import admin

from .models import Perfil


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rut', 'telefono', 'rol', 'prevision')
    list_filter = ('rol', 'prevision')
    search_fields = ('usuario__username', 'usuario__email', 'rut')
    list_editable = ('rol', 'prevision')
    list_select_related = ('usuario',)
    fieldsets = (
        ('Usuario', {'fields': ('usuario',)}),
        ('Datos personales', {'fields': ('rut', 'telefono')}),
        ('Rol y previsión', {'fields': ('rol', 'prevision')}),
    )
