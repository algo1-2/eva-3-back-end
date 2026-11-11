from django.urls import path

from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('prestacion/<slug:slug>/', views.detalle, name='detalle'),

    path('gestion/', views.gestion, name='gestion'),
    path('gestion/nueva/', views.crear, name='crear'),
    path('gestion/<int:pk>/editar/', views.editar, name='editar'),
    path('gestion/<int:pk>/baja/', views.eliminar, name='eliminar'),
    path('gestion/<int:pk>/reactivar/', views.reactivar, name='reactivar'),

    path('canasta/', views.canasta_ver, name='canasta'),
    path('canasta/agregar/<int:pk>/', views.canasta_agregar, name='canasta_agregar'),
    path('canasta/modificar/<int:pk>/', views.canasta_modificar, name='canasta_modificar'),
    path('canasta/quitar/<int:pk>/', views.canasta_quitar, name='canasta_quitar'),
    path('canasta/vaciar/', views.canasta_vaciar, name='canasta_vaciar'),
    path('canasta/prevision/', views.canasta_prevision, name='canasta_prevision'),
    path('canasta/confirmar/', views.canasta_confirmar, name='canasta_confirmar'),
]
