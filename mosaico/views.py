from datetime import date
from itertools import groupby

from rest_framework import generics
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response

from budget_execution.models import Execucao
from mosaico.serializers import (
    ElementoSerializer,
    GrupoSerializer,
    ProgramaSerializer,
    ProjetoAtividadeSerializer,
    SubelementoSerializer,
    SubfuncaoSerializer,
    SubgrupoSerializer,
)


# `Simples` visualization views

class BaseListView(generics.ListAPIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'mosaico/base.html'

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        tseries_qs = self.get_timeseries_queryset()
        tseries_data = self.prepare_timeseries_data(tseries_qs)
        return Response({'breadcrumb': self.breadcrumb,
                         'execucoes': serializer.data,
                         'timeseries': tseries_data})

    # TODO: move this logic to somewhere else
    def prepare_timeseries_data(self, qs):
        ret = {}
        for year, execucoes in groupby(qs, lambda e: e.year):
            execucoes = list(execucoes)
            orcado_total = sum(e.orcado_atualizado for e in execucoes)
            empenhado_total = sum(e.empenhado_liquido for e in execucoes
                                  if e.empenhado_liquido)
            ret[year.strftime('%Y')] = {
                "orcado": orcado_total,
                "empenhado": empenhado_total,
            }

        return ret

    @property
    def breadcrumb(self):
        raise NotImplemented


class GruposListView(BaseListView):
    serializer_class = GrupoSerializer

    def get_queryset(self):
        year = self.kwargs['year']
        return Execucao.objects.filter(year=date(year, 1, 1))

    def filter_queryset(self, qs):
        qs = super().filter_queryset(qs)
        return qs.distinct('subgrupo__grupo_id')

    def get_timeseries_queryset(self):
        return Execucao.objects.all().order_by('year')

    @property
    def breadcrumb(self):
        return [{"name": f'Ano {self.kwargs["year"]}', 'url': 'url'}]


class SubgruposListView(BaseListView):
    serializer_class = SubgrupoSerializer
    _breadcrumb = ""

    def get_queryset(self):
        year = self.kwargs['year']
        grupo_id = self.kwargs['grupo_id']
        ret = Execucao.objects \
            .filter(year=date(year, 1, 1), subgrupo__grupo_id=grupo_id)
        if ret:
            self._breadcrumb = self.create_breadcrumb(ret[0])
        return ret

    def filter_queryset(self, qs):
        qs = super().filter_queryset(qs)
        return qs.distinct('subgrupo')

    def get_timeseries_queryset(self):
        grupo_id = self.kwargs['grupo_id']
        return Execucao.objects.filter(subgrupo__grupo_id=grupo_id) \
            .order_by('year')

    def create_breadcrumb(self, obj):
        return [
            {"name": f'Ano {self.kwargs["year"]}', 'url': 'url'},
            {"name": obj.subgrupo.grupo.desc, 'url': 'url'}
        ]

    @property
    def breadcrumb(self):
        return self._breadcrumb


class ElementosListView(BaseListView):
    serializer_class = ElementoSerializer
    _breadcrumb = ""

    def get_queryset(self):
        year = self.kwargs['year']
        subgrupo_id = self.kwargs['subgrupo_id']
        ret = Execucao.objects \
            .filter(year=date(year, 1, 1), subgrupo_id=subgrupo_id)
        if ret:
            self._breadcrumb = self.create_breadcrumb(ret[0])
        return ret

    def filter_queryset(self, qs):
        qs = super().filter_queryset(qs)
        return qs.distinct('elemento')

    def get_timeseries_queryset(self):
        subgrupo_id = self.kwargs['subgrupo_id']
        return Execucao.objects.filter(subgrupo_id=subgrupo_id) \
            .order_by('year')

    def create_breadcrumb(self, obj):
        return [
            {"name": f'Ano {self.kwargs["year"]}', 'url': 'url'},
            {"name": obj.subgrupo.grupo.desc, 'url': 'url'},
            {"name": obj.subgrupo.desc, 'url': 'url'}
        ]

    @property
    def breadcrumb(self):
        return self._breadcrumb


class SubelementosListView(BaseListView):
    serializer_class = SubelementoSerializer
    _breadcrumb = ""

    def get_queryset(self):
        year = self.kwargs['year']
        subgrupo_id = self.kwargs['subgrupo_id']
        elemento_id = self.kwargs['elemento_id']
        ret = Execucao.objects \
            .filter(year=date(year, 1, 1), subgrupo_id=subgrupo_id,
                    elemento_id=elemento_id)
        if ret:
            self._breadcrumb = self.create_breadcrumb(ret[0])
        return ret

    def filter_queryset(self, qs):
        qs = super().filter_queryset(qs)
        return qs.distinct('subelemento')

    def get_timeseries_queryset(self):
        subgrupo_id = self.kwargs['subgrupo_id']
        elemento_id = self.kwargs['elemento_id']
        return Execucao.objects \
            .filter(subgrupo_id=subgrupo_id, elemento_id=elemento_id) \
            .order_by('year')

    def create_breadcrumb(self, obj):
        return [
            {"name": f'Ano {self.kwargs["year"]}', 'url': 'url'},
            {"name": obj.subgrupo.grupo.desc, 'url': 'url'},
            {"name": obj.subgrupo.desc, 'url': 'url'},
            {"name": obj.elemento.desc, 'url': 'url'}
        ]

    @property
    def breadcrumb(self):
        return self._breadcrumb


# `Técnico` visualization views

class SubfuncoesListView(BaseListView):
    serializer_class = SubfuncaoSerializer

    def get_queryset(self):
        year = self.kwargs['year']
        return Execucao.objects.filter(year=date(year, 1, 1))

    def filter_queryset(self, qs):
        qs = super().filter_queryset(qs)
        return qs.distinct('subfuncao')

    def get_timeseries_queryset(self):
        return Execucao.objects.all().order_by('year')

    @property
    def breadcrumb(self):
        return [{"name": f'Ano {self.kwargs["year"]}', 'url': 'url'}]


class ProgramasListView(BaseListView):
    serializer_class = ProgramaSerializer
    _breadcrumb = ""

    def get_queryset(self):
        year = self.kwargs['year']
        subfuncao_id = self.kwargs['subfuncao_id']
        ret = Execucao.objects \
            .filter(year=date(year, 1, 1), subfuncao_id=subfuncao_id)
        if ret:
            self._breadcrumb = self.create_breadcrumb(ret[0])
        return ret

    def filter_queryset(self, qs):
        qs = super().filter_queryset(qs)
        return qs.distinct('programa')

    def get_timeseries_queryset(self):
        subfuncao_id = self.kwargs['subfuncao_id']
        return Execucao.objects \
            .filter(subfuncao_id=subfuncao_id) \
            .order_by('year')

    def create_breadcrumb(self, obj):
        return [
            {"name": f'Ano {self.kwargs["year"]}', 'url': 'url'},
            {"name": obj.subfuncao.desc, 'url': 'url'}
        ]

    @property
    def breadcrumb(self):
        return self._breadcrumb


class ProjetosAtividadesListView(BaseListView):
    serializer_class = ProjetoAtividadeSerializer
    _breadcrumb = ""

    def get_queryset(self):
        year = self.kwargs['year']
        subfuncao_id = self.kwargs['subfuncao_id']
        programa_id = self.kwargs['programa_id']
        ret = Execucao.objects \
            .filter(year=date(year, 1, 1), subfuncao_id=subfuncao_id,
                    programa_id=programa_id)
        if ret:
            self._breadcrumb = self.create_breadcrumb(ret[0])
        return ret

    def filter_queryset(self, qs):
        qs = super().filter_queryset(qs)
        return qs.distinct('projeto')

    def get_timeseries_queryset(self):
        subfuncao_id = self.kwargs['subfuncao_id']
        programa_id = self.kwargs['programa_id']
        return Execucao.objects \
            .filter(subfuncao_id=subfuncao_id, programa_id=programa_id) \
            .order_by('year')

    def create_breadcrumb(self, obj):
        return [
            {"name": f'Ano {self.kwargs["year"]}', 'url': 'url'},
            {"name": obj.subfuncao.desc, 'url': 'url'},
            {"name": obj.programa.desc, 'url': 'url'}
        ]

    @property
    def breadcrumb(self):
        return self._breadcrumb
