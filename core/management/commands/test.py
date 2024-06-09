from django.core.management.base import BaseCommand
from django.utils import timezone

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

from core.models import BetLink

from .betpawa import Betpawa


class Command(BaseCommand):
    help = 'test functionality in betpawa'

    def add_arguments(self, parser):
        parser.add_argument('--events', type=int, default=30, help='Events Threshold')
        parser.add_argument('--overs', type=float, default=1.5, help='Overs Threshold')
        parser.add_argument('--diff', type=int, default=3, help='Overs Threshold')
        parser.add_argument('--tickets', type=int, default=5, help='number of bets per gane')
        parser.add_argument('--min_odds', type=float, default=1.2, help='Minimum Odds')
        parser.add_argument('--max_odds', type=float, default=7.0, help='Maximum Odds')


    def handle(self, *args, **kwargs):
        events_threshold = kwargs['events']
        overs_threshold = kwargs['overs']
        betpawa = Betpawa(events_threshold, overs_threshold)
        event_links = betpawa.get_event_urls('https://www.betpawa.ug/popular')
        print("links gotten = ", len(event_links))
        for link in event_links:
            betpawa.get_event_data(link)
