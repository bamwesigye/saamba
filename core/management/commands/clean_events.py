from django.core.management.base import BaseCommand
from core.models import Event, EventSelection
from django.db import transaction

class Command(BaseCommand):
    help = 'Clean up events and event selections in the database'

    def add_arguments(self, parser):
        parser.add_argument('--selections-only', action='store_true', 
                            help='Delete only event selections, keep events')
        parser.add_argument('--all', action='store_true', 
                            help='Delete all events and their selections')

    @transaction.atomic
    def handle(self, *args, **options):
        selections_only = options['selections_only']
        delete_all = options['all']

        # Count records before deletion
        event_count = Event.objects.count()
        selection_count = EventSelection.objects.count()
        
        self.stdout.write(f"Before cleanup: {event_count} events, {selection_count} event selections")
        
        # Always delete selections
        EventSelection.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("All event selections deleted"))
        
        # Delete events if requested
        if delete_all:
            Event.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("All events deleted"))
        
        # Count records after deletion
        event_count = Event.objects.count()
        selection_count = EventSelection.objects.count()
        
        self.stdout.write(self.style.SUCCESS(
            f"After cleanup: {event_count} events, {selection_count} event selections"
        ))
