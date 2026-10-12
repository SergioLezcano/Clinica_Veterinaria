from django.shortcuts import redirect
from ..models import PerfilUsuario


class AuthService:

    ROLES_OPERADOR = (
        "OPER",
        "OPERADOR",
        "OPERER",
    )

    @staticmethod
    def redireccionar_por_rol(usuario):

        if not usuario.is_authenticated:
            return redirect("login")

        if usuario.is_superuser or usuario.is_staff:
            PerfilUsuario.objects.get_or_create(
                user=usuario,
                defaults={"rol": "ADMIN"}
            )
            return redirect("menu_administrador")

        try:
            perfil = usuario.perfilusuario

            if perfil.rol == "ADMIN":
                return redirect("menu_administrador")

            if perfil.rol in AuthService.ROLES_OPERADOR:
                return redirect("menu_operador")

        except Exception:
            pass

        return redirect("login")
    
    @staticmethod
    def es_admin(usuario):

        if not usuario or not usuario.is_authenticated:
            return False

        if usuario.is_superuser or usuario.is_staff:
            return True

        try:
            return usuario.perfilusuario.rol == "ADMIN"
        except Exception:
            return False
        
    @staticmethod
    def es_operador(usuario):

        if not usuario or not usuario.is_authenticated:
            return False

        try:
            return (
                usuario.perfilusuario.rol
                in AuthService.ROLES_OPERADOR
            )
        except Exception:
            return False