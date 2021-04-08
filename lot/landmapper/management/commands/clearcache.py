from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache

class Command(BaseCommand):
    help = 'clears the entire django cache'

    def handle(self, *args, **options):
        cache.clear()
