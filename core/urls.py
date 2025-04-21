# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'), 
    path('manage/', views.manage, name='manage'),

    # Market URLs
    path('markets/', views.MarketListView.as_view(), name='market_list'),
    path('markets/<int:pk>/', views.MarketDetailView.as_view(), name='market_detail'),
    path('markets/new/', views.MarketCreateView.as_view(), name='market_create'),
    path('markets/<int:pk>/edit/', views.MarketUpdateView.as_view(), name='market_update'),
    path('markets/<int:pk>/delete/', views.MarketDeleteView.as_view(), name='market_delete'),

    # Selections URLs
    path('selections/', views.SelectionsListView.as_view(), name='selections_list'),
    path('selections/<int:pk>/', views.SelectionsDetailView.as_view(), name='selections_detail'),
    path('selections/new/', views.SelectionsCreateView.as_view(), name='selections_create'),
    path('selections/<int:pk>/edit/', views.SelectionsUpdateView.as_view(), name='selections_update'),
    path('selections/<int:pk>/delete/', views.SelectionsDeleteView.as_view(), name='selections_delete'),

    # BetLink URLs
    path('betlinks/', views.BetLinkListView.as_view(), name='betlink_list'),
    path('betlinks/<int:pk>/', views.BetLinkDetailView.as_view(), name='betlink_detail'),
    path('betlinks/new/', views.BetLinkCreateView.as_view(), name='betlink_create'),
    path('betlinks/<int:pk>/edit/', views.BetLinkUpdateView.as_view(), name='betlink_update'),
    path('betlinks/<int:pk>/delete/', views.BetLinkDeleteView.as_view(), name='betlink_delete'),

    # Event URLs
    path('events/', views.EventListView.as_view(), name='event_list'),
    # Completed Events URL (for score entry) - needs to be before the detail view to avoid conflicts
    path('events/completed/', views.CompletedEventListView.as_view(), name='completed_event_list'),
    path('events/<int:pk>/scores/', views.event_score_entry, name='event_score_entry'),
    path('events/<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
]
