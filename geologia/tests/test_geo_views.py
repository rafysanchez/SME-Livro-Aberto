import pytest

from datetime import date

from model_mommy import mommy
from rest_framework.test import APITestCase

from django.test import RequestFactory
from django.urls import reverse

from budget_execution.models import Execucao, GndGeologia, Subfuncao, Subgrupo
from geologia.serializers import GeologiaDownloadSerializer, GeologiaSerializer


class TestHomeView(APITestCase):

    def get(self, subfuncao_id=None):
        url = reverse('geologia:home')
        if subfuncao_id:
            url += '?subfuncao_id={}'.format(subfuncao_id)
        return self.client.get(url)

    def test_serializes_geologia_data(self):
        mommy.make(Execucao, subgrupo__id=1, _quantity=2)
        execucoes = Execucao.objects.all()
        serializer = GeologiaSerializer(execucoes)

        response = self.get()
        assert serializer.data == response.data

    def test_filters_execucoes_without_subgrupo(self):
        mommy.make(Execucao, subgrupo=None, _quantity=2)
        mommy.make(Execucao, subgrupo__id=1, _quantity=2)
        execucoes = Execucao.objects.filter(subgrupo__isnull=False)
        serializer = GeologiaSerializer(execucoes)

        response = self.get()
        assert serializer.data == response.data

    def test_serializes_geologia_data_with_subfuncao(self):
        mommy.make(Execucao, subgrupo__id=1, subfuncao__id=1, _quantity=2)
        mommy.make(Execucao, subgrupo__id=1, subfuncao__id=2, _quantity=1)
        execucoes = Execucao.objects.all()

        serializer = GeologiaSerializer(execucoes, subfuncao_id=1)

        response = self.get(subfuncao_id=1)
        assert serializer.data == response.data


class TestDownloadView(APITestCase):

    def get(self, chart):
        url = self.base_url(chart)
        return self.client.get(url)

    def base_url(self, chart):
        return reverse('geologia:download', args=[chart])

    @pytest.fixture(autouse=True, scope='class')
    def initial(self):
        gnd1 = mommy.make(GndGeologia)
        gnd2 = mommy.make(GndGeologia)
        subgrupo1 = mommy.make(Subgrupo, id=1, grupo__id=1)
        subgrupo2 = mommy.make(Subgrupo, id=2, grupo__id=1)
        subfuncao = mommy.make(Subfuncao, id=1, desc="sub")

        mommy.make(Execucao,
                   gnd_geologia=gnd1,
                   subgrupo=subgrupo1,
                   subfuncao=subfuncao,
                   year=date(2018, 1, 1),
                   orcado_atualizado=1,
                   _quantity=2)
        mommy.make(Execucao,
                   gnd_geologia=gnd2,
                   subgrupo=subgrupo2,
                   elemento__id=1,
                   subfuncao=subfuncao,
                   year=date(2018, 1, 1),
                   orcado_atualizado=1,
                   _quantity=2)

        # not expected
        mommy.make(Execucao,
                   gnd_geologia=gnd1,
                   subgrupo=None,
                   subfuncao=subfuncao,
                   year=date(2017, 1, 1),
                   orcado_atualizado=1,
                   _quantity=2)

    def prepare_expected_data(self, chart):
        factory = RequestFactory()

        execucoes = Execucao.objects.filter(subgrupo__isnull=False)
        request = factory.get(self.base_url(chart))

        return GeologiaDownloadSerializer(
            execucoes, chart=chart, many=True,
            context={'request': request}).data

    def test_uses_correct_renderer(self):
        response = self.get('camadas')
        assert 'csv' == response.accepted_renderer.format

    def test_downloads_camadas_chart_data(self):
        expected = self.prepare_expected_data('camadas')
        data = self.get('camadas').data
        assert expected == data

    def test_downloads_subfuncao_chart_data(self):
        expected = self.prepare_expected_data('subfuncao')
        data = self.get('subfuncao').data
        assert expected == data

    def test_downloads_subgrupo_chart_data(self):
        expected = self.prepare_expected_data('subgrupo')
        data = self.get('subgrupo').data
        assert expected == data
