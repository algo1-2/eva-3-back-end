from . import canasta


def canasta_global(request):
    return {'canasta_cantidad': canasta.cantidad_total(request)}
