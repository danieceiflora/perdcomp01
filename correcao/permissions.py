from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages

from django.shortcuts import render

class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin que restringe o acesso a apenas administradores (staff ou superuser).
    Útil para views que só devem ser acessíveis por administradores.
    Exibe uma mensagem de acesso negado em vez de redirecionar.
    """
    permission_denied_message = "Acesso negado. Somente administradores podem acessar esta página."
    
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser)
    
    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return render(
            self.request, 
            'forbidden.html', 
            {'message': self.permission_denied_message},
            status=403
        )
