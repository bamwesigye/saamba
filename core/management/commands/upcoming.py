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


from .calculate import analyze_goals, get_date_diff
from .betpawa import Betpawa

class Command(BaseCommand):
    help = 'Get upcoming matches'

    def add_arguments(self, parser):
        parser.add_argument('--events', type=int, default=30, help='Events Threshold')
      
    def handle(self, *args, **kwargs):
        events_threshold = kwargs['events']
        betpawa = Betpawa(over_threshold=0.5, events_threshold=events_threshold)
        betpawa.get_upcoming()
        time.sleep(2)
