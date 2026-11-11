from . import canasta


def canasta_global(request):
    """Inyecta en todas las plantillas el contador de ítems de la canasta."""
    return {'canasta_cantidad': canasta.cantidad_total(request)}
