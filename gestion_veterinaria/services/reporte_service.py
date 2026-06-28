from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, time

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

        hoy = timezone.now().date()

        inicio_dia = datetime.combine(
            hoy,
            time.min
        )

        fin_dia = datetime.combine(
            hoy,
            time.max
        )

        return (
            HistoriaClinica.objects
            .filter(
                fecha_consulta__range=(
                    inicio_dia,
                    fin_dia
                )
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
    def top_especies(total_completadas, limite=3):

        total_completadas = HistoriaClinica.objects.filter(
            estado="C"
        ).count()

        if total_completadas == 0:
            total_completadas = 1

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
                "nombre": item["mascota__especie"].capitalize(),
                "cantidad": item["total"],
                "porcentaje": int(
                    (item["total"] / total_completadas) * 100
                )
            })

        return especies