from django.db.models import Count, Q
from django.utils import timezone

from ..models import HistoriaClinica


class ReporteService:

    @staticmethod
    def obtener_totales():

        return HistoriaClinica.objects.aggregate(
            completadas=Count(
                "id",
                filter=Q(estado="C")
            ),
            en_espera=Count(
                "id",
                filter=Q(estado="P")
            ),
            canceladas=Count(
                "id",
                filter=Q(estado="X")
            )
        )
    
    @staticmethod
    def obtener_movimiento_hoy():

        hoy = timezone.localdate()

        return (
            HistoriaClinica.objects
            .filter(
                fecha_consulta__date=hoy
            )
            .aggregate(
                atendidos=Count(
                    "id",
                    filter=Q(estado="C")
                ),
                espera=Count(
                    "id",
                    filter=Q(estado="P")
                )
            )
        )
    
    @staticmethod
    def top_especies(total_completadas=None, limite=3):

        if total_completadas is None:
            total_completadas = HistoriaClinica.objects.filter(
                estado="C"
            ).count()

        divisor = total_completadas if total_completadas > 0 else 1

        especies_data = (
            HistoriaClinica.objects
            .filter(estado="C")
            .values("mascota__especie")
            .annotate(total=Count("id"))
            .order_by("-total")[:limite]
        )

        especies = []

        for item in especies_data:

            especies.append({
                "nombre": (item["mascota__especie"] or "Sin especie").capitalize(),
                "cantidad": item["total"],
                "porcentaje": int(
                    (item["total"] / divisor) * 100
                )
            })

        return especies