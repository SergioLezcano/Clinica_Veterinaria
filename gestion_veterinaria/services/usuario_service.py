from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404

from ..models import PerfilUsuario


class UsuarioService:
    """
    Servicio encargado de la gestión de usuarios operadores.
    """
    @staticmethod
    def obtener_operadores():

        return (
            PerfilUsuario.objects
            .select_related("user")
            .filter(
                rol__in=[
                    "OPER",
                    "OPERADOR",
                    "OPERER"
                ]
            )
        )

    @staticmethod
    @transaction.atomic
    def crear_operador(form):

        usuario = form.save(commit=False)

        usuario.set_password(
            form.cleaned_data["password"]
        )

        usuario.save()

        PerfilUsuario.objects.create(
            user=usuario,
            rol="OPER"
        )

        return usuario
    
    @staticmethod
    def obtener_usuario(usuario_id):

        return get_object_or_404(
            User,
            pk=usuario_id
        )
    
    @staticmethod
    @transaction.atomic
    def cambiar_estado(usuario_id):

        usuario = UsuarioService.obtener_usuario(
            usuario_id
        )

        usuario.is_active = not usuario.is_active

        usuario.save(
            update_fields=["is_active"]
        )

        return usuario