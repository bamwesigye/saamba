from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import BetLink, Market, Selections, Event, EventSelection, EventOdds, Bookmakers

# Create your views here.

# Home View
def home(request):
    # Start with all events ordered by event_time
    queryset = Event.objects.all().order_by('event_time')
    
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
from django.forms import ModelForm, HiddenInput
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Prefetch, Max, F, Q
from django.utils import timezone

# Manage View
def manage(request):
    # Simple view for management links
    return render(request, 'core/manage.html')

class EventListView(ListView):
    model = Event
    context_object_name = 'events'
    template_name = 'core/event_list.html'
    paginate_by = 20  # Add pagination for better performance with large datasets
    
    def get_queryset(self):
        queryset = Event.objects.all().order_by('event_time')
        
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

class EventOddsForm(ModelForm):
    class Meta:
        model = EventOdds
        fields = ['event_selection', 'bookmaker', 'odd']
        widgets = {
            'event_selection': HiddenInput(),
            'bookmaker': HiddenInput(),
        }

class EventDetailView(DetailView):
    model = Event
    context_object_name = 'event'
    template_name = 'core/event_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object
        
        # Get all bookmakers
        bookmakers = Bookmakers.objects.all()
        context['bookmakers'] = bookmakers
        
        # Get all event selections for this event with the latest odds for each bookmaker
        event_selections = EventSelection.objects.filter(event=event)
        
        # For each selection, get odds history grouped by bookmaker
        selections_with_odds = []
        
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
            
            selections_with_odds.append({
                'selection': selection,
                'bookmaker_odds': bookmaker_odds,
            })
        
        context['selections_with_odds'] = selections_with_odds
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Process the form submission for updating odds
        form = EventOddsForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Odds updated successfully!')
        else:
            messages.error(request, 'Error updating odds!')
            
        return redirect('core:event_detail', pk=self.object.pk)
