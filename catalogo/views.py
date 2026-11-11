from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import canasta as cs
from .forms import PrestacionForm
from .models import Especialidad, Prestacion

es_personal = user_passes_test(lambda u: u.is_active and u.is_staff, login_url='cuentas:login')

ORDENES = {
    'nombre': 'nombre',
    'precio_asc': 'arancel',
    'precio_desc': '-arancel',
    'duracion': 'duracion_minutos',
}


def lista(request):
    q = request.GET.get('q', '').strip()
    esp = request.GET.get('especialidad', '')
    orden = request.GET.get('orden', 'nombre')

    qs = Prestacion.objects.select_related('especialidad').filter(activo=True)
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(codigo__icontains=q) | Q(descripcion__icontains=q))
    if esp.isdigit():
        qs = qs.filter(especialidad_id=int(esp))
    qs = qs.order_by(ORDENES.get(orden, 'nombre'))

    page = Paginator(qs, 6).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    return render(request, 'catalogo/lista.html', {
        'page': page,
        'especialidades': Especialidad.objects.filter(activa=True),
        'q': q, 'esp': esp, 'orden': orden,
        'querystring': params.urlencode(),
    })


def detalle(request, slug):
    prestacion = get_object_or_404(
        Prestacion.objects.select_related('especialidad'), slug=slug, activo=True)
    return render(request, 'catalogo/detalle.html', {'p': prestacion})


@login_required
@es_personal
def gestion(request):
    q = request.GET.get('q', '').strip()
    qs = Prestacion.objects.select_related('especialidad')
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(codigo__icontains=q))
    page = Paginator(qs, 10).get_page(request.GET.get('page'))
    return render(request, 'catalogo/gestion.html', {'page': page, 'q': q})


@login_required
@es_personal
def crear(request):
    form = PrestacionForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        p = form.save()
        messages.success(request, f'Prestación «{p.nombre}» creada correctamente.')
        return redirect('catalogo:gestion')
    return render(request, 'catalogo/form.html', {'form': form, 'titulo': 'Nueva prestación'})


@login_required
@es_personal
def editar(request, pk):
    p = get_object_or_404(Prestacion, pk=pk)
    form = PrestacionForm(request.POST or None, request.FILES or None, instance=p)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Prestación «{p.nombre}» actualizada.')
        return redirect('catalogo:gestion')
    return render(request, 'catalogo/form.html', {'form': form, 'titulo': f'Editar: {p.nombre}', 'p': p})


@login_required
@es_personal
def eliminar(request, pk):
    p = get_object_or_404(Prestacion, pk=pk)
    if request.method == 'POST':
        p.activo = False
        p.save(update_fields=['activo', 'actualizado'])
        messages.warning(request, f'«{p.nombre}» fue dada de baja (puede reactivarse).')
        return redirect('catalogo:gestion')
    return render(request, 'catalogo/confirmar_baja.html', {'p': p})


@login_required
@es_personal
@require_POST
def reactivar(request, pk):
    p = get_object_or_404(Prestacion, pk=pk)
    p.activo = True
    p.save(update_fields=['activo', 'actualizado'])
    messages.success(request, f'«{p.nombre}» reactivada.')
    return redirect('catalogo:gestion')


def _cantidad(request, defecto=1):
    try:
        return int(request.POST.get('cantidad', defecto))
    except (TypeError, ValueError):
        return defecto


def _volver(request, defecto='catalogo:canasta'):
    destino = request.POST.get('next', '')
    if destino.startswith('/') and not destino.startswith('//'):
        return redirect(destino)
    return redirect(defecto)


def canasta_ver(request):
    return render(request, 'catalogo/canasta.html', {'c': cs.detalle(request)})


@require_POST
def canasta_agregar(request, pk):
    p = get_object_or_404(Prestacion, pk=pk)
    ok, msg = cs.agregar(request, p, max(1, _cantidad(request)))
    (messages.success if ok else messages.error)(request, msg)
    return _volver(request, 'catalogo:lista')


@require_POST
def canasta_modificar(request, pk):
    p = get_object_or_404(Prestacion, pk=pk)
    ok, msg = cs.modificar(request, p, _cantidad(request))
    (messages.success if ok else messages.error)(request, msg)
    return redirect('catalogo:canasta')


@require_POST
def canasta_quitar(request, pk):
    p = get_object_or_404(Prestacion, pk=pk)
    ok, msg = cs.quitar(request, p)
    (messages.info if ok else messages.error)(request, msg)
    return redirect('catalogo:canasta')


@require_POST
def canasta_vaciar(request):
    cs.vaciar(request)
    messages.info(request, 'Tu canasta fue vaciada.')
    return redirect('catalogo:canasta')


@require_POST
def canasta_prevision(request):
    if cs.fijar_prevision(request, request.POST.get('prevision', '')):
        messages.success(request, 'Previsión actualizada; copago recalculado.')
    else:
        messages.error(request, 'Previsión no válida.')
    return redirect('catalogo:canasta')


@login_required
@require_POST
def canasta_confirmar(request):
    c = cs.detalle(request)
    if not c['lineas']:
        messages.error(request, 'Tu canasta está vacía.')
        return redirect('catalogo:canasta')
    ahora = timezone.localtime()
    comprobante = f'SV-{ahora:%Y%m%d%H%M%S}-{request.user.pk}'
    cs.vaciar(request)
    return render(request, 'catalogo/comprobante.html', {
        'c': c, 'comprobante': comprobante, 'fecha': ahora})
