from django.core.management.base import BaseCommand
from django.utils import timezone

import time, json, requests, html

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
    help = 'Displays current time'

    def handle(self, *args, **kwargs):
        betpawa = Betpawa(over_threshold=3.5)
        betpawa.login()        
        betpawa.get_upcoming()
        betpawa.place_bet(amount=500)



# Set up Chrome options for headless mode
chrome_options = Options()
# chrome_options.add_argument("--headless")


# get the current time
