import pytest

from datetime import date

from model_mommy.mommy import make
from rest_framework.test import APITestCase

from django.test import RequestFactory
from django.urls import reverse

from budget_execution.models import Execucao, FonteDeRecursoGrupo, Subgrupo
from mosaico.serializers import (
    ElementoSerializer,
    GrupoSerializer,
    ProgramaSerializer,
    ProjetoAtividadeSerializer,
    SubelementoSerializer,
    SubgrupoSerializer,
    SubfuncaoSerializer,
)


class TestHomeView(APITestCase):
    def get(self):
        url = reverse('mosaico:home')
        return self.client.get(url)

    def test_redirect_to_most_recent_year(self):
        year = 1500
        redirect_url = reverse('mosaico:grupos', kwargs=dict(year=year))
        make('Execucao', year=date(year, 1, 1))
        response = self.get()
        self.assertRedirects(response, redirect_url,
                             fetch_redirect_response=False)

        year = 2018
        redirect_url = reverse('mosaico:grupos',
                               kwargs=dict(year=year))
        make('Execucao', year=date(year, 1, 1))
        response = self.get()
        self.assertRedirects(response, redirect_url,
                             fetch_redirect_response=False)

        year = 1998
        make('Execucao', year=date(year, 1, 1))
        response = self.get()
        self.assertRedirects(response, redirect_url,
                             fetch_redirect_response=False)


class TestBaseListView(APITestCase):
    def get(self, fonte_grupo_id=None):
        url = reverse('mosaico:grupos', args=[2018])
        return self.client.get(url)

    def test_returns_fonte_grupo_filters(self):
        fgs = [
            make(FonteDeRecursoGrupo, id=1, desc='fg1'),
            make(FonteDeRecursoGrupo, id=2, desc='fg2'),
            make(FonteDeRecursoGrupo, id=3, desc='fg3'),
        ]

        expected = [{fg.id: fg.desc} for fg in fgs]

        response = self.get()
        assert expected == response.data['fonte_grupo_filters']


class BaseTestCase(APITestCase):

    def url(self, fonte_grupo_id=None):
        url = self.base_url
        if fonte_grupo_id:
            url += '?fonte_grupo_id={}'.format(fonte_grupo_id)
        return url

    def get(self, fonte_grupo_id=None):
        url = self.url(fonte_grupo_id)
        return self.client.get(url)

    def get_serializer(self, execucoes, fonte_grupo_id=None):
        serializer = self.serializer_class

        factory = RequestFactory()
        request = factory.get(self.url(fonte_grupo_id=fonte_grupo_id))
        request.query_params = {}
        if fonte_grupo_id:
            request.query_params['fonte_grupo_id'] = fonte_grupo_id

        return serializer(execucoes, many=True, context={'request': request})


class TestGruposListView(BaseTestCase):

    @property
    def serializer_class(self):
        return GrupoSerializer

    @property
    def base_url(self):
        return reverse('mosaico:grupos', args=[2018])

    @pytest.fixture(autouse=True)
    def initial(self):
        make(Execucao,
             subgrupo__grupo__id=1,
             fonte_grupo__id=1,
             year=date(2018, 1, 1),
             _quantity=2)
        make(Execucao,
             subgrupo__grupo__id=2,
             fonte_grupo__id=1,
             year=date(2018, 1, 1),
             _quantity=2)
        make(Execucao,
             subgrupo__grupo__id=3,
             fonte_grupo__id=2,
             year=date(2018, 1, 1),
             _quantity=2)

    def test_serializes_execucoes_data(self):
        execucoes = Execucao.objects.all().distinct('subgrupo__grupo')
        serializer = self.get_serializer(execucoes)
        expected = serializer.data

        response = self.get()
        assert expected == response.data['execucoes']

    def test_filters_by_fonte_grupo_querystring_data(self):
        execucoes = Execucao.objects.filter(fonte_grupo__id=1) \
            .distinct('subgrupo__grupo')
        serializer = self.get_serializer(execucoes, fonte_grupo_id=1)
        expected = serializer.data

        response = self.get(fonte_grupo_id=1)
        data = response.data['execucoes']
        assert 2 == len(data)
        assert expected == data

    def test_view_works_when_queryset_is_empty(self):
        make(FonteDeRecursoGrupo, id=3)
        response = self.get(fonte_grupo_id=3)
        assert [] == response.data['execucoes']


class TestSubgruposListView(BaseTestCase):

    @property
    def serializer_class(self):
        return SubgrupoSerializer

    @property
    def base_url(self):
        return reverse('mosaico:subgrupos', args=[2018, 1])

    @pytest.fixture(autouse=True)
    def initial(self):
        subgrupo1 = make(Subgrupo, id=96, grupo__id=1)
        subgrupo2 = make(Subgrupo, id=97, grupo__id=1)
        subgrupo3 = make(Subgrupo, id=98, grupo__id=1)

        make(Execucao,
             subgrupo=subgrupo1,
             fonte_grupo__id=1,
             year=date(2018, 1, 1),
             _quantity=2)
        make(Execucao,
             subgrupo=subgrupo2,
             fonte_grupo__id=1,
             year=date(2018, 1, 1),
             _quantity=2)
        make(Execucao,
             subgrupo=subgrupo3,
             fonte_grupo__id=2,
             year=date(2018, 1, 1),
             _quantity=2)

    def test_serializes_execucoes_data(self):
        execucoes = Execucao.objects.all().distinct('subgrupo')
        serializer = self.get_serializer(execucoes)
        expected = serializer.data

        response = self.get()
        data = response.data['execucoes']
        assert 3 == len(data)
        assert expected == data

    def test_filters_by_fonte_grupo_querystring_data(self):
        execucoes = Execucao.objects.filter(fonte_grupo__id=1) \
            .distinct('subgrupo')
        serializer = self.get_serializer(execucoes, fonte_grupo_id=1)
        expected = serializer.data

        response = self.get(fonte_grupo_id=1)
        data = response.data['execucoes']
        assert 2 == len(data)
        assert expected == data

    def test_view_works_when_queryset_is_empty(self):
        make(FonteDeRecursoGrupo, id=3)
        response = self.get(fonte_grupo_id=3)
        assert [] == response.data['execucoes']


class TestElementosListView(BaseTestCase):

    @property
    def serializer_class(self):
        return ElementoSerializer

    @property
    def base_url(self):
        return reverse('mosaico:elementos', args=[2018, 1, 1])

    @pytest.fixture(autouse=True)
    def initial(self):
        subgrupo = make(Subgrupo, id=1, grupo__id=1)
        make(Execucao,
             elemento__id=1,
             subgrupo=subgrupo,
             fonte_grupo__id=1,
             year=date(2018, 1, 1),
             _quantity=2)
        make(Execucao,
             elemento__id=2,
             subgrupo=subgrupo,
             fonte_grupo__id=1,
             year=date(2018, 1, 1),
             _quantity=2)
        make(Execucao,
             elemento__id=3,
             subgrupo=subgrupo,
             fonte_grupo__id=2,
             year=date(2018, 1, 1),
             _quantity=2)

    def test_serializes_execucoes_data(self):
        execucoes = Execucao.objects.all().distinct('elemento')
        serializer = self.get_serializer(execucoes)
        expected = serializer.data

        response = self.get()
        data = response.data['execucoes']
        assert 3 == len(data)
        assert expected == data

    def test_filters_by_fonte_grupo_querystring_data(self):
        execucoes = Execucao.objects.filter(fonte_grupo__id=1) \
            .distinct('elemento')
        serializer = self.get_serializer(execucoes, fonte_grupo_id=1)
        expected = serializer.data

        response = self.get(fonte_grupo_id=1)
        data = response.data['execucoes']
        assert 2 == len(data)
        assert expected == data

    def test_view_works_when_queryset_is_empty(self):
        make(FonteDeRecursoGrupo, id=3)
        response = self.get(fonte_grupo_id=3)
        assert [] == response.data['execucoes']


class TestSubelementosListView(BaseTestCase):

    @property
    def serializer_class(self):
        return SubelementoSerializer

    @property
    def base_url(self):
        return reverse('mosaico:subelementos', args=[2018, 1, 1, 1])

    @pytest.fixture(autouse=True)
    def initial(self):
        subgrupo = make(Subgrupo, id=1, grupo__id=1)
        make(Execucao,
             subelemento__id=1,
             subelemento_friendly__id=1,
             elemento__id=1,
             subgrupo=subgrupo,
             fonte_grupo__id=1,
             year=date(2018, 1, 1),
             _quantity=2)
        make(Execucao,
             subelemento__id=2,
             subelemento_friendly__id=2,
             elemento__id=1,
             subgrupo=subgrupo,
             fonte_grupo__id=1,
             year=date(2018, 1, 1),
             _quantity=2)
        make(Execucao,
             subelemento__id=3,
             subelemento_friendly__id=3,
             elemento__id=1,
             subgrupo=subgrupo,
             fonte_grupo__id=2,
             year=date(2018, 1, 1),
             _quantity=2)

    def test_serializes_execucoes_data(self):
        execucoes = Execucao.objects.all().distinct('subelemento')
        serializer = self.get_serializer(execucoes)
        expected = serializer.data

        response = self.get()
        data = response.data['execucoes']
        assert 3 == len(data)
        assert expected == data

    def test_filters_by_fonte_grupo_querystring_data(self):
        execucoes = Execucao.objects.filter(fonte_grupo__id=1) \
            .distinct('subelemento')
        serializer = self.get_serializer(execucoes, fonte_grupo_id=1)
        expected = serializer.data

        response = self.get(fonte_grupo_id=1)
        data = response.data['execucoes']
        assert 2 == len(data)
        assert expected == data

    def test_view_works_when_queryset_is_empty(self):
        make(FonteDeRecursoGrupo, id=3)
        response = self.get(fonte_grupo_id=3)
        assert [] == response.data['execucoes']


class TestSubfuncaoListView(BaseTestCase):

    @property
    def serializer_class(self):
        return SubfuncaoSerializer

    @property
    def base_url(self):
        return reverse('mosaico:subfuncoes', args=[2018])

    @pytest.fixture(autouse=True)
    def initial(self):
        make(Execucao,
             subfuncao__id=1,
             fonte_grupo__id=1,
             year=date(2018, 1, 1),
             _quantity=2)
        make(Execucao,
             subfuncao__id=2,
             fonte_grupo__id=1,
             year=date(2018, 1, 1),
             _quantity=2)
        make(Execucao,
             subfuncao__id=3,
             fonte_grupo__id=2,
             year=date(2018, 1, 1),
             _quantity=2)

    def test_serializes_execucoes_data(self):
        execucoes = Execucao.objects.all().distinct('subfuncao')
        serializer = self.get_serializer(execucoes)
        expected = serializer.data

        response = self.get()
        data = response.data['execucoes']
        assert 3 == len(data)
        assert expected == data

    def test_filters_by_fonte_grupo_querystring_data(self):
        execucoes = Execucao.objects.filter(fonte_grupo__id=1) \
            .distinct('subfuncao')
        serializer = self.get_serializer(execucoes, fonte_grupo_id=1)
        expected = serializer.data

        response = self.get(fonte_grupo_id=1)
        data = response.data['execucoes']
        assert 2 == len(data)
        assert expected == data

    def test_view_works_when_queryset_is_empty(self):
        make(FonteDeRecursoGrupo, id=3)
        response = self.get(fonte_grupo_id=3)
        assert [] == response.data['execucoes']


class TestProgramasListView(BaseTestCase):

    @property
    def serializer_class(self):
        return ProgramaSerializer

    @property
    def base_url(self):
        return reverse('mosaico:programas', args=[2018, 1])

    @pytest.fixture(autouse=True)
    def initial(self):
        make(Execucao,
             programa__id=1,
             subfuncao__id=1,
             fonte_grupo__id=1,
             year=date(2018, 1, 1),
             _quantity=2)
        make(Execucao,
             programa__id=2,
             subfuncao__id=1,
             fonte_grupo__id=1,
             year=date(2018, 1, 1),
             _quantity=2)
        make(Execucao,
             programa__id=3,
             subfuncao__id=1,
             fonte_grupo__id=2,
             year=date(2018, 1, 1),
             _quantity=2)

    def test_serializes_execucoes_data(self):
        execucoes = Execucao.objects.all().distinct('programa')
        serializer = self.get_serializer(execucoes)
        expected = serializer.data

        response = self.get()
        data = response.data['execucoes']
        assert 3 == len(data)
        assert expected == data

    def test_filters_by_fonte_grupo_querystring_data(self):
        execucoes = Execucao.objects.filter(fonte_grupo__id=1) \
            .distinct('programa')
        serializer = self.get_serializer(execucoes, fonte_grupo_id=1)
        expected = serializer.data

        response = self.get(fonte_grupo_id=1)
        data = response.data['execucoes']
        assert 2 == len(data)
        assert expected == data

    def test_view_works_when_queryset_is_empty(self):
        make(FonteDeRecursoGrupo, id=3)
        response = self.get(fonte_grupo_id=3)
        assert [] == response.data['execucoes']


class TestProjetosAtividadesListView(APITestCase):

    def get(self, fonte_grupo_id=None):
        url = reverse('mosaico:projetos', args=[2018, 1, 1])
        if fonte_grupo_id:
            url += '?fonte_grupo_id={}'.format(fonte_grupo_id)
        return self.client.get(url)

    @pytest.fixture(autouse=True)
    def initial(self):
        make(Execucao,
             projeto__id=1,
             programa__id=1,
             subfuncao__id=1,
             fonte_grupo__id=1,
             year=date(2018, 1, 1),
             _quantity=2)
        make(Execucao,
             projeto__id=2,
             programa__id=1,
             subfuncao__id=1,
             fonte_grupo__id=1,
             year=date(2018, 1, 1),
             _quantity=2)
        make(Execucao,
             projeto__id=3,
             programa__id=1,
             subfuncao__id=1,
             fonte_grupo__id=2,
             year=date(2018, 1, 1),
             _quantity=2)

    def test_serializes_execucoes_data(self):
        execucoes = Execucao.objects.all().distinct('projeto')
        serializer = ProjetoAtividadeSerializer(execucoes, many=True)
        expected = serializer.data

        response = self.get()
        data = response.data['execucoes']
        assert 3 == len(data)
        assert expected == data

    def test_filters_by_fonte_grupo_querystring_data(self):
        execucoes = Execucao.objects.filter(fonte_grupo__id=1) \
            .distinct('projeto')
        serializer = ProjetoAtividadeSerializer(execucoes, many=True)
        expected = serializer.data

        response = self.get(fonte_grupo_id=1)
        data = response.data['execucoes']
        assert 2 == len(data)
        assert expected == data

    def test_view_works_when_queryset_is_empty(self):
        make(FonteDeRecursoGrupo, id=3)
        response = self.get(fonte_grupo_id=3)
        assert [] == response.data['execucoes']