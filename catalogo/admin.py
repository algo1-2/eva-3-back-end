from django.contrib import admin

from .models import Especialidad, Prestacion

# Identidad corporativa del panel de administración.
admin.site.site_header = 'SaludVital - Panel de Control'
admin.site.site_title = 'SaludVital Admin'
admin.site.index_title = 'Gestión Operativa de Recursos y Servicios'


@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'icono', 'activa', 'total_prestaciones')
    list_filter = ('activa',)
    search_fields = ('nombre', 'descripcion')
    list_editable = ('activa',)

    @admin.display(description='N° de prestaciones')
    def total_prestaciones(self, obj):
        return obj.prestaciones.count()


@admin.register(Prestacion)
class PrestacionAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'especialidad', 'arancel', 'cupos_diarios', 'estado', 'activo')
    list_filter = ('especialidad', 'estado', 'activo')
    search_fields = ('codigo', 'nombre', 'descripcion', 'especialidad__nombre')
    list_editable = ('arancel', 'cupos_diarios', 'estado', 'activo')
    list_select_related = ('especialidad',)
    prepopulated_fields = {'slug': ('nombre',)}
    list_per_page = 20
    fieldsets = (
        ('Identificación', {'fields': ('codigo', 'nombre', 'slug', 'especialidad')}),
        ('Descripción clínica', {'fields': ('descripcion', 'requisitos', 'imagen')}),
        ('Valores y disponibilidad', {'fields': ('arancel', 'duracion_minutos', 'cupos_diarios', 'estado')}),
        ('Vigencia', {'fields': ('activo',)}),
    )
