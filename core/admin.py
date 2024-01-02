from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import BetLink, Market, Selections, Bookmakers, Event, EventSelection, EventOdds

# Register your models here.
@admin.register(BetLink)
class BetLinkAdmin(admin.ModelAdmin):
    list_display = ['link_url','league','country', 'order','Level']
    list_editable = ['Level', 'order']
    search_fields = ['league','country']
    
@admin.register(Selections)
class SelectionsAdmin(admin.ModelAdmin):
    pass

@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    pass

@admin.register(Bookmakers)
class BookmakersAdmin(admin.ModelAdmin):
    pass

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    pass

@admin.register(EventSelection)
class EventSelectionAdmin(admin.ModelAdmin):
    pass


@admin.register(EventOdds)
class EventOddsAdmin(admin.ModelAdmin):
    pass
