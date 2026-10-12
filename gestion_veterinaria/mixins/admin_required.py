from django.contrib.auth.mixins import AccessMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from ..services.auth_service import AuthService


class AdminRequiredMixin(AccessMixin):

    def dispatch(
        self,
        request: HttpRequest,
        *args,
        **kwargs
    ) -> HttpResponse:

        if not request.user.is_authenticated:
            return redirect("login")

        if not AuthService.es_admin(request.user):
            return redirect("menu_operador")

        return super().dispatch(
            request,
            *args,
            **kwargs
        )