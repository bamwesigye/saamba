from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import AccountBalance, BetpawaBets, BetLink, BetpawaMatch, Market, Selections, Bookmakers, Event, EventSelection, EventOdds, PlacedBets

# Register your models here.

@admin.register(BetpawaBets)
class BetpawaBetsAdmin(admin.ModelAdmin):
    list_display = ['event_time','event_link','event_match','event_tournament','selection','is_placed']
    list_filter= ['event_time','selection','event_tournament','is_placed']
    list_editable = ['is_placed']

@admin.register(BetLink)
class BetLinkAdmin(ImportExportModelAdmin):
    list_display_links = ['league_code']
    list_display = ['league_code','link_url','league','country', 'order','Level']
    list_editable = ['league','country', 'order','Level']
    search_fields = ['league','country']
    
@admin.register(Selections)
class SelectionsAdmin(admin.ModelAdmin):
    list_display = ['id','selection_code','selection','description']
    list_filter = ['market']

@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ['id','market_name']

@admin.register(Bookmakers)
class BookmakersAdmin(admin.ModelAdmin):
    list_display = ['name', 'url']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['id','event_time', 'event_link', 'home_team', 'away_team', 'tournament']
    list_filter = ['event_time', 'tournament']
    
@admin.register(EventSelection)
class EventSelectionAdmin(admin.ModelAdmin):    
    list_display = ['id','event', 'selection', 'get_market', 'is_settled', 'settled_at']
    list_filter = ['event', 'is_settled', 'selection__market']
    
    def get_market(self, obj):
        return obj.selection.market if obj.selection else None
    
    get_market.short_description = 'Market'

@admin.register(EventOdds)
class EventOddsAdmin(admin.ModelAdmin):
    list_display = ['id','event_selection', 'bookmaker', 'odd']
    list_filter = ['event_selection', 'bookmaker']
    list_editable = ['odd']

@admin.register(PlacedBets)
class PlacedBetsAdmin(admin.ModelAdmin):
    list_display = ['id','betcode','betlink','stake','odds','payout']
    list_display_links = ['betcode']

@admin.register(AccountBalance)
class AccountBalanceAdmin(admin.ModelAdmin):
    list_display = ['day','amount']


@admin.register(BetpawaMatch)
class BetpawaMatchAdmin(admin.ModelAdmin):
    list_display = ['match_link','match_time','home_team','away_team','is_settled']
    list_filter = ['match_time','tournament','is_settled']
    list_editable = ['is_settled']