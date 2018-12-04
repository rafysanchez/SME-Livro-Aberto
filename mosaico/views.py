from datetime import date

from rest_framework import generics

from budget_execution.models import Execucao
from mosaico.serializers import ElementoSerializer, GrupoSerializer, \
    SubelementoSerializer, SubgrupoSerializer


class GruposList(generics.ListAPIView):
    serializer_class = GrupoSerializer

    def get_queryset(self):
        year = self.kwargs['year']
        return Execucao.objects.filter(year=date(year, 1, 1)) \
            .distinct('subgrupo__grupo')


class SubgruposList(generics.ListAPIView):
    serializer_class = SubgrupoSerializer

    def get_queryset(self):
        year = self.kwargs['year']
        grupo_id = self.kwargs['grupo_id']
        return Execucao.objects \
            .filter(year=date(year, 1, 1), subgrupo__grupo_id=grupo_id) \
            .distinct('subgrupo')


class ElementosList(generics.ListAPIView):
    serializer_class = ElementoSerializer

    def get_queryset(self):
        year = self.kwargs['year']
        subgrupo_id = self.kwargs['subgrupo_id']
        return Execucao.objects \
            .filter(year=date(year, 1, 1), subgrupo_id=subgrupo_id) \
            .distinct('elemento')


class SubelementosList(generics.ListAPIView):
    serializer_class = SubelementoSerializer

    def get_queryset(self):
        year = self.kwargs['year']
        subgrupo_id = self.kwargs['subgrupo_id']
        elemento_id = self.kwargs['elemento_id']
        return Execucao.objects \
            .filter(year=date(year, 1, 1), subgrupo_id=subgrupo_id,
                    elemento_id=elemento_id) \
            .distinct('subelemento')
