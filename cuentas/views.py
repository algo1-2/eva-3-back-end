from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import LoginForm, RegistroForm


class IngresoView(LoginView):
    template_name = 'cuentas/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f'Bienvenido/a, {form.get_user().get_username()}.')
        return super().form_valid(form)


def registro(request):
    if request.user.is_authenticated:
        return redirect('catalogo:lista')
    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Cuenta creada correctamente. ¡Bienvenido/a a SaludVital!')
        return redirect('catalogo:lista')
    return render(request, 'cuentas/registro.html', {'form': form})


@require_POST
def salir(request):
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('catalogo:lista')
