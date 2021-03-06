import json
from urllib.request import urlopen

from django.db.models import Q, F
from django.core.management.base import BaseCommand

from apps.core.models import Recorrido

BASE_URL = 'http://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&sensor=false'


class Command(BaseCommand):
    stats = {'succeed': 0, 'failed': 0}
    queryset = Recorrido.objects.filter(
        Q(inicio='') | Q(fin='') | Q(inicio=F('fin'))
    )

    @staticmethod
    def geocode(point):
        """Returns the address corresponding to given geographical point"""
        req = urlopen(BASE_URL.format(lng=point[0], lat=point[1]))
        data = json.loads(req.read())
        address = data['results'][0]['formatted_address']
        return ','.join(address.split(',')[:2])

    def handle(self, *args, **options):
        for recorrido in self.queryset:
            inicio = (recorrido.ruta.x[0], recorrido.ruta.y[0])
            fin = (recorrido.ruta.x[-1], recorrido.ruta.y[-1])

            recorrido.inicio = self.geocode(inicio)
            recorrido.fin = self.geocode(fin)

            if recorrido.inicio == recorrido.fin:
                # rondin, tomar punto medio como fin
                fin = (
                    recorrido.ruta.x[len(recorrido.ruta.x) // 2],
                    recorrido.ruta.y[len(recorrido.ruta.y) // 2]
                )
                recorrido.fin = self.geocode(fin)

            try:
                recorrido.save()
                print('OK: {}: {} -> {}'.format(recorrido.id, recorrido.inicio, recorrido.fin))
                self.stats['succeed'] += 1
            except Exception as e:
                print("Skipped: {0}".format(e))
                self.stats['failed'] += 1

        print("Done!", self.stats)
