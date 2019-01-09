from django.db.models import Sum


class GeologiaSerializer:

    def __init__(self, queryset, subfuncao_id=None, *args, **kwargs):
        self.queryset = queryset
        self._subfuncao_id = int(subfuncao_id) if subfuncao_id else subfuncao_id

    @property
    def data(self):
        return {
            'camadas': self.prepare_data(),
            'subfuncao': self.prepare_data(subfuncao_id=self._subfuncao_id),
            'subgrupo': self.prepare_subgrupo_data(),
        }

    # Charts 1 and 2 (camadas and subfuncao)
    def prepare_data(self, subfuncao_id=None):
        qs = self.queryset

        ret = {
            'orcado': [],
            'empenhado': [],
        }

        # filtering for chart 2 (by subfuncao)
        if subfuncao_id:
            qs = qs.filter(subfuncao_id=subfuncao_id)
            ret['subfuncao_id'] = subfuncao_id

        years = qs.order_by('year').values('year').distinct()

        for year_dict in years:
            year = year_dict['year']
            year_qs = qs.filter(year=year)

            ret['orcado'].append(self._get_orcado_data_by_year(year_qs))
            ret['empenhado'].append(self._get_empenhado_data_by_year(year_qs))

        return ret

    def _get_orcado_data_by_year(self, qs):
        year = qs[0].year

        orcado_by_gnd = qs.values('gnd_gealogia__desc', 'gnd_gealogia__slug') \
            .annotate(orcado=Sum('orcado_atualizado'))
        orcado_total = qs.aggregate(total=Sum('orcado_atualizado'))
        orcado_total = orcado_total['total']

        orcado_gnds = self._get_orcado_gnds_list(orcado_by_gnd, orcado_total)

        return {
            "year": year.strftime("%Y"),
            "total": orcado_total,
            "gnds": orcado_gnds,
        }

    def _get_empenhado_data_by_year(self, qs):
        year = qs[0].year

        empenhado_by_gnd = qs \
            .values('gnd_gealogia__desc', 'gnd_gealogia__slug') \
            .annotate(empenhado=Sum('empenhado_liquido'))
        empenhado_total = qs.aggregate(total=Sum('empenhado_liquido'))
        empenhado_total = empenhado_total['total']

        empenhado_gnds = self._get_empenhado_gnds_list(empenhado_by_gnd,
                                                       empenhado_total)

        return {
            "year": year.strftime("%Y"),
            "total": empenhado_total,
            "gnds": empenhado_gnds,
        }

    # Chart 3: Subgrupo
    def prepare_subgrupo_data(self):
        qs = self.queryset.filter(year__year__gte=2010)

        years = qs.order_by('year').values('year').distinct()

        ret = {
            'orcado': [],
            'empenhado': [],
        }
        for year_dict in years:
            year = year_dict['year']
            year_qs = qs.filter(year=year)

            ret['orcado'].append(self.get_subgrupo_year_orcado_data(year_qs))
            ret['empenhado'].append(
                self.get_subgrupo_year_empenhado_data(year_qs))

        return ret

    def get_subgrupo_year_orcado_data(self, qs):
        year = qs[0].year
        subgrupos = qs.order_by('subgrupo_id').values('subgrupo_id') \
            .distinct()

        ret = {
            'year': year.strftime('%Y'),
            'subgrupos': [],
        }

        for subgrupo in subgrupos:
            qs_subgrupo = qs.filter(subgrupo=subgrupo['subgrupo_id'])
            ret['subgrupos'].append(
                self.get_subgrupo_orcado_data(qs_subgrupo))

        return ret

    def get_subgrupo_year_empenhado_data(self, qs):
        year = qs[0].year
        subgrupos = qs.order_by('subgrupo_id').values('subgrupo_id') \
            .distinct()

        ret = {
            'year': year.strftime('%Y'),
            'subgrupos': [],
        }

        for subgrupo in subgrupos:
            qs_subgrupo = qs.filter(subgrupo=subgrupo['subgrupo_id'])
            ret['subgrupos'].append(
                self.get_subgrupo_empenhado_data(qs_subgrupo))

        return ret

    def get_subgrupo_orcado_data(self, qs):
        subgrupo = qs[0].subgrupo

        orcado_by_gnd = qs.values('gnd_gealogia__desc', 'gnd_gealogia__slug') \
            .annotate(orcado=Sum('orcado_atualizado'))
        orcado_total = qs.aggregate(total=Sum('orcado_atualizado'))
        orcado_total = orcado_total['total']

        orcado_gnds = self._get_orcado_gnds_list(orcado_by_gnd, orcado_total)

        return {
            "subgrupo": subgrupo.desc,
            "total": orcado_total,
            "gnds": orcado_gnds,
        }

    def get_subgrupo_empenhado_data(self, qs):
        subgrupo = qs[0].subgrupo

        empenhado_by_gnd = qs \
            .values('gnd_gealogia__desc', 'gnd_gealogia__slug') \
            .annotate(empenhado=Sum('empenhado_liquido'))
        empenhado_total = qs.aggregate(total=Sum('empenhado_liquido'))
        empenhado_total = empenhado_total['total']

        empenhado_gnds = self._get_empenhado_gnds_list(empenhado_by_gnd,
                                                       empenhado_total)

        return {
            "subgrupo": subgrupo.desc,
            "total": empenhado_total,
            "gnds": empenhado_gnds,
        }

    def _get_orcado_gnds_list(self, orcado_by_gnd, orcado_total):
        return [
            {
                "name": gnd['gnd_gealogia__desc'],
                "slug": gnd['gnd_gealogia__slug'],
                "value": gnd['orcado'],
                "percent": self._calculate_percent(
                    gnd['orcado'], orcado_total)
            }
            for gnd in orcado_by_gnd
        ]

    def _get_empenhado_gnds_list(self, empenhado_by_gnd, empenhado_total):
        return [
            {
                "name": gnd['gnd_gealogia__desc'],
                "slug": gnd['gnd_gealogia__slug'],
                "value": gnd['empenhado'],
                "percent": self._calculate_percent(
                    gnd['empenhado'], empenhado_total),
            }
            for gnd in empenhado_by_gnd
        ]

    def _calculate_percent(self, value, total):
        if value is None or not total:
            return 0
        return value / total


class GeologiaDownloadSerializer:

    def __init__(self, queryset, chart, *args, **kwargs):
        self.queryset = queryset
        self.chart = chart

    @property
    def data(self):
        if self.chart == 'camadas':
            return self.prepare_camadas_data()
        elif self.chart == 'subfuncao':
            return self.prepare_subfuncao_data()

    def prepare_camadas_data(self):
        qs = self.queryset.order_by('year')

        data_by_gnd = qs.values('gnd_gealogia__desc', 'year__year') \
            .annotate(orcado=Sum('orcado_atualizado')) \
            .annotate(empenhado=Sum('empenhado_liquido'))

        orcado_values = qs.values('year__year') \
            .annotate(total=Sum('orcado_atualizado'))
        orcado_total = {v['year__year']: v['total'] for v in orcado_values}

        empenhado_values = qs.values('year__year') \
            .annotate(total=Sum('empenhado_liquido'))
        empenhado_total = {v['year__year']: v['total']
                           for v in empenhado_values}

        return self._get_gnds_list(data_by_gnd, orcado_total, empenhado_total)

    def prepare_subfuncao_data(self):
        qs = self.queryset.order_by('year')

        subfuncoes = qs.order_by('subfuncao_id').values('subfuncao_id') \
            .distinct()
        ret = []
        for subfuncao in subfuncoes:
            qs_subfuncao = qs.filter(subfuncao=subfuncao['subfuncao_id'])
            ret += self._get_subfuncao_values(qs_subfuncao)

        return ret

    def _get_subfuncao_values(self, qs):
        data_by_gnd = qs.values('gnd_gealogia__desc', 'year__year',
                                'subfuncao__desc') \
            .annotate(orcado=Sum('orcado_atualizado')) \
            .annotate(empenhado=Sum('empenhado_liquido'))

        orcado_values = qs.values('year__year') \
            .annotate(total=Sum('orcado_atualizado'))
        orcado_total = {v['year__year']: v['total'] for v in orcado_values}

        empenhado_values = qs.values('year__year') \
            .annotate(total=Sum('empenhado_liquido'))
        empenhado_total = {v['year__year']: v['total']
                           for v in empenhado_values}

        return self._get_gnds_list(data_by_gnd, orcado_total, empenhado_total)

    def _get_gnds_list(self, data_by_gnd, orcado_total_by_year,
                       empenhado_total_by_year):
        ret = []
        for gnd in data_by_gnd:
            year = gnd['year__year']
            orcado_total = orcado_total_by_year[year]
            empenhado_total = empenhado_total_by_year[year]

            gnd_dict = {
                "ano": year,
                "gnd": gnd['gnd_gealogia__desc'],
                "orcado": gnd['orcado'],
                "orcado_total": orcado_total,
                "orcado_percentual": self._calculate_percent(
                    gnd['orcado'], orcado_total),
                "empenhado": gnd['empenhado'],
                "empenhado_total": empenhado_total,
                "empenhado_percentual": self._calculate_percent(
                    gnd['empenhado'], empenhado_total),
            }
            if 'subfuncao__desc' in gnd:
                gnd_dict["subfuncao"] = gnd['subfuncao__desc']

            ret.append(gnd_dict)

        return ret

    def _calculate_percent(self, value, total):
        if value is None or not total:
            return 0
        return value / total
