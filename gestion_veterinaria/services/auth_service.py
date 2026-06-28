from django.shortcuts import redirect


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

        try:
            return usuario.perfilusuario.rol == "ADMIN"
        except Exception:
            return False
        
    @staticmethod
    def es_operador(usuario):

        try:
            return (
                usuario.perfilusuario.rol
                in AuthService.ROLES_OPERADOR
            )
        except Exception:
            return False