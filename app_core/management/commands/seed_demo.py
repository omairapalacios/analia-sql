from django.core.management.base import BaseCommand
from app_core.models import Agent, Indicator
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = "Seed demo data"

    def handle(self, *args, **kwargs):
        agents = [
            ('A001','Ana Ramos','Lima','Tarjetas','Lima'),
            ('A002','Luis Pérez','Arequipa','Préstamos','Sur'),
            ('A003','Sara Díaz','Lima','Seguros','Lima'),
        ]
        Agent.objects.all().delete()
        Indicator.objects.all().delete()

        obj_agents = []
        for code, name, site, camp, region in agents:
            obj_agents.append(Agent.objects.create(
                code=code, full_name=name, site=site, campaign=camp, region=region
            ))

        base = date.today()
        names = ['AHT','FCR','Productividad']
        for i in range(30):
            for n in names:
                Indicator.objects.create(
                    name=n,
                    campaign=random.choice(['Tarjetas','Préstamos','Seguros']),
                    date=base - timedelta(days=i),
                    value=round(random.uniform(60, 95), 2),
                    agent=random.choice(obj_agents)
                )
        self.stdout.write(self.style.SUCCESS("Seed listo"))
