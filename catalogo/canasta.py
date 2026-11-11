"""
Canasta de exámenes almacenada en request.session (sin persistencia en BD).

Estructura en sesión:
    request.session['canasta']    = {'<id_prestacion>': cantidad, ...}
    request.session['prevision']  = 'FONASA' | 'ISAPRE' | 'PARTICULAR'
"""
from decimal import Decimal, ROUND_HALF_UP

from .models import Prestacion

CLAVE = 'canasta'
CLAVE_PREVISION = 'prevision'
MAX_POR_ITEM = 5  # Tope de unidades de una misma prestación por solicitud.


def _canasta(request):
    return request.session.get(CLAVE, {})


def _guardar(request, canasta):
    request.session[CLAVE] = canasta
    request.session.modified = True


def prevision_actual(request):
    """Previsión elegida en sesión; por defecto la del perfil o Particular."""
    if CLAVE_PREVISION in request.session:
        return request.session[CLAVE_PREVISION]
    perfil = getattr(request.user, 'perfil', None) if request.user.is_authenticated else None
    return perfil.prevision if perfil else 'PARTICULAR'


def fijar_prevision(request, prevision):
    from cuentas.models import Perfil
    if prevision in Perfil.COBERTURA:
        request.session[CLAVE_PREVISION] = prevision
        request.session.modified = True
        return True
    return False


def cantidad_total(request):
    return sum(_canasta(request).values())


def agregar(request, prestacion, cantidad=1):
    """Agrega validando vigencia, estado y cupos. Devuelve (ok, mensaje)."""
    if not prestacion.reservable:
        return False, f'«{prestacion.nombre}» no está disponible para agendar.'
    canasta = _canasta(request)
    clave = str(prestacion.pk)
    nueva = canasta.get(clave, 0) + cantidad
    limite = min(prestacion.cupos_diarios, MAX_POR_ITEM)
    if nueva > limite:
        return False, f'Solo puedes agendar hasta {limite} unidad(es) de «{prestacion.nombre}» (cupos disponibles).'
    canasta[clave] = nueva
    _guardar(request, canasta)
    return True, f'«{prestacion.nombre}» agregada a tu canasta.'


def modificar(request, prestacion, cantidad):
    """Fija la cantidad exacta; 0 elimina el ítem. Devuelve (ok, mensaje)."""
    canasta = _canasta(request)
    clave = str(prestacion.pk)
    if clave not in canasta:
        return False, 'La prestación no está en tu canasta.'
    if cantidad <= 0:
        return quitar(request, prestacion)
    limite = min(prestacion.cupos_diarios, MAX_POR_ITEM)
    if cantidad > limite:
        return False, f'Máximo {limite} unidad(es) por cupos disponibles.'
    canasta[clave] = cantidad
    _guardar(request, canasta)
    return True, 'Cantidad actualizada.'


def quitar(request, prestacion):
    canasta = _canasta(request)
    if canasta.pop(str(prestacion.pk), None) is None:
        return False, 'La prestación no estaba en tu canasta.'
    _guardar(request, canasta)
    return True, f'«{prestacion.nombre}» eliminada de la canasta.'


def vaciar(request):
    request.session.pop(CLAVE, None)
    request.session.modified = True


def _redondeo(valor):
    return valor.quantize(Decimal('1'), rounding=ROUND_HALF_UP)


def detalle(request):
    """Calcula líneas y totales a partir de la sesión y precios vigentes en BD."""
    from cuentas.models import Perfil

    canasta = _canasta(request)
    prevision = prevision_actual(request)
    cobertura = Decimal(Perfil.COBERTURA.get(prevision, 0)) / 100

    prestaciones = (Prestacion.objects.select_related('especialidad')
                    .filter(pk__in=[int(k) for k in canasta]))
    lineas, subtotal, bonificacion, minutos = [], Decimal('0'), Decimal('0'), 0
    for p in prestaciones:
        cant = canasta[str(p.pk)]
        sub = p.arancel * cant
        bonif = _redondeo(sub * cobertura)
        lineas.append({'prestacion': p, 'cantidad': cant, 'subtotal': sub,
                       'bonificacion': bonif, 'copago': sub - bonif})
        subtotal += sub
        bonificacion += bonif
        minutos += p.duracion_minutos * cant
    return {
        'lineas': lineas,
        'subtotal': subtotal,
        'bonificacion': bonificacion,
        'copago_total': subtotal - bonificacion,
        'duracion_total': minutos,
        'prevision': prevision,
        'cobertura_pct': int(cobertura * 100),
        'cantidad_total': sum(canasta.values()),
    }
