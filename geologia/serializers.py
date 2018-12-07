from django.db.models import Sum


class GeologiaSerializer:

    def __init__(self, queryset, *args, **kwargs):
        self.queryset = queryset

    @property
    def data(self):
        return {
            'gnd': self.prepare_gnd_data()
        }

    def prepare_gnd_data(self):
        qs = self.queryset

        years = qs.values('year').distinct()

        ret = {
            'orcado': [],
            'empenhado': [],
        }
        for year_dict in years:
            year = year_dict['year']
            year_qs = qs.filter(year=year)

            ret['orcado'].append(self.get_gnd_orcado_data(year_qs))
            ret['empenhado'].append(self.get_gnd_empenhado_data(year_qs))

        return ret

    def get_gnd_orcado_data(self, qs):
        year = qs[0].year

        orcado_by_gnd = qs.values('gnd_gealogia__desc') \
            .annotate(orcado=Sum('orcado_atualizado'))
        orcado_total = qs.aggregate(total=Sum('orcado_atualizado'))

        orcado_gnds = self._get_orcado_gnds_list(orcado_by_gnd, orcado_total)

        return {
            "year": year.strftime("%Y"),
            "total": orcado_total['total'],
            "gnds": orcado_gnds,
        }

    def get_gnd_empenhado_data(self, qs):
        year = qs[0].year

        empenhado_by_gnd = qs.values('gnd_gealogia__desc') \
            .annotate(empenhado=Sum('empenhado_liquido'))
        empenhado_total = qs.aggregate(total=Sum('empenhado_liquido'))

        empenhado_gnds = self._get_empenhado_gnds_list(empenhado_by_gnd,
                                                       empenhado_total)

        return {
            "year": year.strftime("%Y"),
            "total": empenhado_total['total'],
            "gnds": empenhado_gnds,
        }

    def _get_orcado_gnds_list(self, orcado_by_gnd, orcado_total):
        return [
            {
                "name": gnd['gnd_gealogia__desc'],
                "value": gnd['orcado'],
                "percent": gnd['orcado'] / orcado_total['total'],
            }
            for gnd in orcado_by_gnd
        ]

    def _get_empenhado_gnds_list(self, empenhado_by_gnd, empenhado_total):
        ret = []
        for gnd in empenhado_by_gnd:
            if gnd['empenhado'] is None:
                gnd['empenhado'] = 0

            ret.append({
                "name": gnd['gnd_gealogia__desc'],
                "value": gnd['empenhado'],
                "percent": gnd['empenhado'] / empenhado_total['total'],
            })

        return ret
