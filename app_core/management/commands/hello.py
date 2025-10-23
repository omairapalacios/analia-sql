from django.core.management.base import BaseCommand
class Command(BaseCommand):
    help = "Hello test"
    def handle(self, *a, **k):
        self.stdout.write(self.style.SUCCESS("Hello works"))
