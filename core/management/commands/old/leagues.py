from django.core.management.base import BaseCommand
from django.utils import timezone

import time, requests, html, os

# selenium 4
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from core.models import BetLink


from .calculate import analyze_goals, get_date_diff
from .betpawa import Betpawa

class Command(BaseCommand):
    help = 'Get upcoming matches'

    def add_arguments(self, parser):
        parser.add_argument('--events', type=int, default=30, help='Events Threshold')
      
    def handle(self, *args, **kwargs):
        events_threshold = kwargs['events']
        betpawa = Betpawa(over_threshold=2.5, events_threshold=events_threshold)
        leagues = BetLink.objects.all().order_by('?')
        for league in leagues:
            events_links =betpawa.get_event_urls(league.link_url)
            div_value = league.model_value            
            for event_link in events_links:
                betpawa.get_model_prediction(event_link,div=div_value)
                time.sleep(2)
        betpawa.create_code()
        betpawa.place_bet(20)

