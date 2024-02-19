from django.core.management.base import BaseCommand
from django.utils import timezone


# selenium 4
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time, json, requests, html
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from tqdm import tqdm
from datetime import datetime
from core.models import BetLink, BetpawaBets
from .betpawa import Betpawa
class Command(BaseCommand):
    help = 'Displays current time'

    def add_arguments(self, parser):
        parser.add_argument('--events', type=int, default=6, help='Events Threshold')
        parser.add_argument('--tickets', type=int, default=5, help='number of bets per gane')
        parser.add_argument('--overs', type=float, default=1.5, help='Overs Threshold')
        parser.add_argument('--diff', type=int, default=3, help='Difference Threshold')
        parser.add_argument('--min_odds', type=float, default=1.2, help='Minimum Odds')
        parser.add_argument('--max_odds', type=float, default=1.7, help='Maximum Odds')

    def handle(self, *args, **kwargs):
        events_threshold = kwargs['events']
        overs_threshold = kwargs['overs']
        tickets = kwargs['tickets']
        diff = kwargs['diff']
        min_odds = kwargs['min_odds']
        max_odds = kwargs['max_odds']
        betpawa = Betpawa(events_threshold, overs_threshold, diff,tickets=tickets, min_odds=min_odds, max_odds=max_odds)
        betpawa.login()
        time.sleep(1)
        betpawa.place_tickets(events_threshold,tickets)