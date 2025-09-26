from rest_framework import generics
from logs.models import Log
from logs.serializers import LogSerializer
from django.utils.dateparse import parse_datetime


class LogListView(generics.ListAPIView):
    """Listar logs con filtros por action, related_model y fecha"""

    queryset = Log.objects.all()
    serializer_class = LogSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        request = self.request

        # Filtrar por action
        action = request.query_params.get("action")
        if action:
            queryset = queryset.filter(action=action)

        # Filtrar por modelo relacionado
        related_model = request.query_params.get("related_model")
        if related_model:
            queryset = queryset.filter(related_model__iexact=related_model)

        # Filtrar por fecha (created_at)
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset
