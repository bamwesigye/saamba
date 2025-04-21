from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from django.utils import timezone
from .models import BetLink, Market, Selections, Event, EventSelection, EventOdds, Bookmakers
from .forms import EventOddsForm, ScoreEntryForm
from .settlement import process_selections

# Create your views here.

# Home View
def home(request):
    # Start with all future events ordered by event_time
    queryset = Event.objects.filter(event_time__gt=timezone.now()).order_by('event_time')
    
    # Get search and filter parameters from GET request
    search_query = request.GET.get('search', '')
    tournament = request.GET.get('tournament', '')
    
    # Apply search filter if provided
    if search_query:
        queryset = queryset.filter(
            Q(home_team__icontains=search_query) | 
            Q(away_team__icontains=search_query) |
            Q(tournament__icontains=search_query)
        )
    
    # Apply tournament filter if provided
    if tournament:
        queryset = queryset.filter(tournament=tournament)
    
    # Context for the template
    context = {
        'events': queryset,
        'tournaments': Event.objects.values_list('tournament', flat=True).distinct().order_by('tournament'),
        'current_search': search_query,
        'current_tournament': tournament,
    }
    return render(request, 'core/home.html', context)

# Market CRUD Views
class MarketListView(ListView):
    model = Market
    context_object_name = 'markets'
    template_name = 'core/market_list.html'

class MarketDetailView(DetailView):
    model = Market
    context_object_name = 'market'
    template_name = 'core/market_detail.html'

class MarketCreateView(CreateView):
    model = Market
    fields = '__all__'
    template_name = 'core/market_form.html'
    success_url = reverse_lazy('core:market_list')

class MarketUpdateView(UpdateView):
    model = Market
    fields = '__all__'
    template_name = 'core/market_form.html'
    success_url = reverse_lazy('core:market_list')

class MarketDeleteView(DeleteView):
    model = Market
    context_object_name = 'market'
    template_name = 'core/market_confirm_delete.html'
    success_url = reverse_lazy('core:market_list')


# Selections CRUD Views
class SelectionsListView(ListView):
    model = Selections
    context_object_name = 'selections_list'
    template_name = 'core/selections_list.html'

class SelectionsDetailView(DetailView):
    model = Selections
    context_object_name = 'selection'
    template_name = 'core/selections_detail.html'

class SelectionsCreateView(CreateView):
    model = Selections
    fields = '__all__'
    template_name = 'core/selections_form.html'
    success_url = reverse_lazy('core:selections_list')

class SelectionsUpdateView(UpdateView):
    model = Selections
    fields = '__all__'
    template_name = 'core/selections_form.html'
    success_url = reverse_lazy('core:selections_list')

class SelectionsDeleteView(DeleteView):
    model = Selections
    context_object_name = 'selection'
    template_name = 'core/selections_confirm_delete.html'
    success_url = reverse_lazy('core:selections_list')


# BetLink CRUD Views
class BetLinkListView(ListView):
    model = BetLink
    context_object_name = 'betlinks'
    template_name = 'core/betlink_list.html'

class BetLinkDetailView(DetailView):
    model = BetLink
    context_object_name = 'betlink'
    template_name = 'core/betlink_detail.html'

class BetLinkCreateView(CreateView):
    model = BetLink
    fields = ['league_code', 'link_url', 'league', 'country', 'Level', 'order', 'bookmaker'] # Or '__all__'
    template_name = 'core/betlink_form.html'
    success_url = reverse_lazy('core:betlink_list')

class BetLinkUpdateView(UpdateView):
    model = BetLink
    fields = ['league_code', 'link_url', 'league', 'country', 'Level', 'order', 'bookmaker'] # Or '__all__'
    template_name = 'core/betlink_form.html'
    success_url = reverse_lazy('core:betlink_list')

class BetLinkDeleteView(DeleteView):
    model = BetLink
    context_object_name = 'betlink'
    template_name = 'core/betlink_confirm_delete.html'
    success_url = reverse_lazy('core:betlink_list')


# Event Views
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Prefetch, Max, F

class EventListView(ListView):
    model = Event
    context_object_name = 'events'
    template_name = 'core/event_list.html'
    paginate_by = 20  # Add pagination for better performance with large datasets
    
    def get_queryset(self):
        # Show only future events
        queryset = Event.objects.filter(event_time__gt=timezone.now()).order_by('event_time')
        
        # Get search and filter parameters from GET request
        search_query = self.request.GET.get('search', '')
        tournament = self.request.GET.get('tournament', '')
        
        # Apply search filter if provided
        if search_query:
            queryset = queryset.filter(
                Q(home_team__icontains=search_query) | 
                Q(away_team__icontains=search_query) |
                Q(tournament__icontains=search_query)
            )
        
        # Apply tournament filter if provided
        if tournament:
            queryset = queryset.filter(tournament=tournament)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add unique tournaments for the filter dropdown
        context['tournaments'] = Event.objects.values_list('tournament', flat=True).distinct().order_by('tournament')
        
        # Add current filters to context for form persistence
        context['current_search'] = self.request.GET.get('search', '')
        context['current_tournament'] = self.request.GET.get('tournament', '')
        
        return context

class CompletedEventListView(ListView):
    model = Event
    context_object_name = 'events'
    template_name = 'core/completed_event_list.html'
    paginate_by = 20
    
    def get_queryset(self):
        # Get events where event_time is in the past
        queryset = Event.objects.filter(
            event_time__lt=timezone.now()
        ).order_by('-event_time')  # Most recent completed events first
        
        # Get search and filter parameters from GET request
        search_query = self.request.GET.get('search', '')
        tournament = self.request.GET.get('tournament', '')
        settled_status = self.request.GET.get('settled', '')
        
        # Apply search filter if provided
        if search_query:
            queryset = queryset.filter(
                Q(home_team__icontains=search_query) | 
                Q(away_team__icontains=search_query) |
                Q(tournament__icontains=search_query)
            )
        
        # Apply tournament filter if provided
        if tournament:
            queryset = queryset.filter(tournament=tournament)
            
        # Apply scores_confirmed filter if provided
        if settled_status:
            if settled_status == 'confirmed':
                queryset = queryset.filter(scores_confirmed=True)
            elif settled_status == 'pending':
                queryset = queryset.filter(scores_confirmed=False)
                
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add unique tournaments for the filter dropdown
        context['tournaments'] = Event.objects.values_list('tournament', flat=True).distinct().order_by('tournament')
        
        # Add current filters to context for form persistence
        context['current_search'] = self.request.GET.get('search', '')
        context['current_tournament'] = self.request.GET.get('tournament', '')
        context['current_settled'] = self.request.GET.get('settled', '')
        
        return context

class EventDetailView(DetailView):
    model = Event
    context_object_name = 'event'
    template_name = 'core/event_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object
        
        # Check if the event has started (odds updates should not be allowed)
        context['event_started'] = event.event_time <= timezone.now()
        
        # Get all bookmakers
        bookmakers = Bookmakers.objects.all()
        context['bookmakers'] = bookmakers
        
        # Get all event selections for this event with the latest odds for each bookmaker
        event_selections = EventSelection.objects.filter(event=event)
        
        # For each selection, get odds history grouped by bookmaker
        selections_with_odds = []
        
        # Get unique markets for this event
        unique_markets = list(set([es.selection.market for es in event_selections]))
        unique_markets.sort(key=lambda m: m.id)  # Sort markets by ID
        context['markets'] = unique_markets
        
        # Group selections by market
        selections_by_market = {}
        for market in unique_markets:
            selections_by_market[market.id] = []
        
        for selection in event_selections:
            # Get all odds for this selection
            odds = EventOdds.objects.filter(event_selection=selection).order_by('-entered_at')
            
            # Group odds by bookmaker
            bookmaker_odds = {}
            for bookmaker in bookmakers:
                bookmaker_odds[bookmaker.id] = {
                    'bookmaker': bookmaker,
                    'latest_odd': odds.filter(bookmaker=bookmaker).first(),
                    'history': odds.filter(bookmaker=bookmaker).order_by('-entered_at')[:10],  # Last 10 odds
                    'form': EventOddsForm(initial={'event_selection': selection, 'bookmaker': bookmaker}),
                }
            
            selection_data = {
                'selection': selection,
                'bookmaker_odds': bookmaker_odds,
            }
            
            # Add to both flat list and market-grouped dictionary
            selections_with_odds.append(selection_data)
            selections_by_market[selection.selection.market.id].append(selection_data)
        
        context['selections_with_odds'] = selections_with_odds
        context['selections_by_market'] = selections_by_market
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Prevent odds updates for events that have already started
        if self.object.event_time <= timezone.now():
            messages.error(request, 'Cannot update odds for events that have already started!')
            return redirect('core:event_detail', pk=self.object.pk)
        
        # Process the form submission for updating odds
        form = EventOddsForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Odds updated successfully!')
        else:
            messages.error(request, 'Error updating odds!')
            
        return redirect('core:event_detail', pk=self.object.pk)

# Score Entry Form
from django.forms import Form, IntegerField, BooleanField, ValidationError

class ScoreEntryForm(Form):
    hthg = IntegerField(label='Home Team - Half Time', required=True, min_value=0)
    htag = IntegerField(label='Away Team - Half Time', required=True, min_value=0)
    fthg = IntegerField(label='Home Team - Full Time', required=True, min_value=0)
    ftag = IntegerField(label='Away Team - Full Time', required=True, min_value=0)
    confirm_scores = BooleanField(label='Confirm Scores and Settle Selections', required=False)
    
    def clean(self):
        cleaned_data = super().clean()
        # Validate that full-time scores are consistent with half-time scores
        hthg = cleaned_data.get('hthg')
        htag = cleaned_data.get('htag')
        fthg = cleaned_data.get('fthg')
        ftag = cleaned_data.get('ftag')
        
        if hthg is not None and htag is not None and fthg is not None and ftag is not None:
            if fthg < hthg:
                raise ValidationError("Full-time home goals cannot be less than half-time home goals")
            if ftag < htag:
                raise ValidationError("Full-time away goals cannot be less than half-time away goals")
        
        return cleaned_data

# Event Score Entry View
def event_score_entry(request, pk):
    event = get_object_or_404(Event, pk=pk)
    
    # Check if event is in the past
    if event.event_time > timezone.now():
        messages.error(request, "Cannot enter scores for future events")
        return redirect('core:completed_event_list')
    
    if request.method == 'POST':
        form = ScoreEntryForm(request.POST)
        
        if form.is_valid():
            # Update event scores
            event.hthg = form.cleaned_data['hthg']
            event.htag = form.cleaned_data['htag']
            event.fthg = form.cleaned_data['fthg']
            event.ftag = form.cleaned_data['ftag']
            
            # Only mark as confirmed if checkbox is checked
            if form.cleaned_data['confirm_scores']:
                event.scores_confirmed = True
            else:
                messages.success(request, f"Scores saved for {event.home_team} vs {event.away_team} but not confirmed yet")
            
            # Save the event with the updated scores first
            event.save()
            
            # Process selections if scores are confirmed
            if event.scores_confirmed:
                # Force refresh from database to ensure we have the latest event data
                event.refresh_from_db()
                settlement_results = process_selections(event)
                messages.success(request, f"Scores confirmed and selections settled for {event.home_team} vs {event.away_team}.")
            
            return redirect('core:completed_event_list')
    else:
        # Pre-populate with existing scores if available
        initial_data = {}
        if event.hthg is not None:
            initial_data['hthg'] = event.hthg
        if event.htag is not None:
            initial_data['htag'] = event.htag
        if event.fthg is not None:
            initial_data['fthg'] = event.fthg
        if event.ftag is not None:
            initial_data['ftag'] = event.ftag
            
        form = ScoreEntryForm(initial=initial_data)
    
    context = {
        'event': event,
        'form': form,
    }
    
    return render(request, 'core/event_score_entry.html', context)

def manage(request):
    # Simple view for management links
    return render(request, 'core/manage.html')
