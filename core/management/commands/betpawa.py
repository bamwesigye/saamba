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

class Command(BaseCommand):
    help = 'Displays current time'

    def add_arguments(self, parser):
        parser.add_argument('--events', type=int, default=30, help='Events Threshold')
        parser.add_argument('--overs', type=float, default=1.5, help='Overs Threshold')
        parser.add_argument('--diff', type=int, default=3, help='Overs Threshold')

    def handle(self, *args, **kwargs):
        events_threshold = kwargs['events']
        overs_threshold = kwargs['overs']
        diff = kwargs['diff']
        
        betpawa = Betpawa(events_threshold, overs_threshold, diff)

        # betpawa.login()
        while True:
            links = BetLink.objects.all().order_by('?')
            for link in tqdm(links, desc="Progress"):
                self.stdout.write(f"Working on {link.link_url} - {link.league}")
                betpawa.place_events(link.link_url)
            betpawa.create_code()
            # time.sleep(60*60*24)


# Set up Chrome options for headless mode
chrome_options = Options()
# chrome_options.add_argument("--headless")


from .calculate import analyze_goals, get_date_diff


class Betpawa:
    def __init__(self, events_threshold, over_threshold, diff, tickets=5):
        self.driver = webdriver.Chrome(options= chrome_options, service=ChromeService(ChromeDriverManager().install()))
        self.driver.get("https://betpawa.ug/")
        self.driver.maximize_window()
        self.events_counter = 0
        self.events_threshold = events_threshold
        self.over_threshold = over_threshold
        self.diff = diff
        self.tickets = tickets
        time.sleep(5)

    def login(self):
        self.driver.get("https://www.betpawa.ug/login")
        time.sleep(2)
        self.driver.find_element(By.CSS_SELECTOR,"#login-form-phoneNumber").send_keys("775236691")
        time.sleep(2)
        self.driver.find_element(By.CSS_SELECTOR,"#login-form-password-input").send_keys("34454392")
        time.sleep(5)
        self.driver.find_element(By.CSS_SELECTOR,'[data-test-id="logInButton"]').click()
        time.sleep(2)

    def get_odds(self,event_link):
        self.driver.get(event_link)
        time.sleep(2)
        odds = self.driver.find_elements(By.CLASS_NAME,"event-bet")
        for odd in odds:
            # print(odd.text)
            pass
    
    def place_events(self, link_url):
        try:
            self.driver.get(link_url)
            time.sleep(2)
            event_links = []
            events = self.driver.find_elements(By.CLASS_NAME,"event-match")       
            for event in events:
                event_links.append(event.get_attribute("href"))
            time.sleep(2)
            for event_link in event_links:
                self.get_statistics(event_link)
                print(f"{self.events_counter} counted vs {self.events_threshold} ")
                if self.events_counter > self.events_threshold:
                    time.sleep(2)
                    self.create_code()
                    self.events_counter = 0
                    time.sleep(2)
        except Exception as e:
            print("Failed to get league", e)

    def get_upcoming(self, events_limit):
        self.driver.get('https://www.betpawa.ug/upcoming?marketId=_1X2&categoryId=2')
        SCROLL_PAUSE_TIME = 2

        # Get scroll height
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        events = self.driver.find_elements(By.CLASS_NAME,"event-match")


    def get_statistics(self, event_link):
        driver = self.driver
        wait = WebDriverWait(driver, 20)
        try:
            driver.get(event_link)
            time.sleep(5)
            print(driver.current_url)
            match_date = driver.find_element(By.CSS_SELECTOR,'.event-header-date').text
            match_particpants = driver.find_element(By.CSS_SELECTOR,'.event-header-participants').text
            print(match_particpants)
            match_details = driver.find_element(By.CSS_SELECTOR,'.event-header-details').text
            print(match_details)
            date_diff, match_day = get_date_diff(match_date)
            print(match_date,'hours difference = ', date_diff)
            if date_diff <= self.diff :
                wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".event-statistics-text")))
                time.sleep(2)    
                driver.find_element(By.CSS_SELECTOR,".event-statistics-text").click() # change to wait until
                time.sleep(5)
                driver.find_element(By.CSS_SELECTOR,'[data-test-tab="lastmatches"]').click()
                time.sleep(5)
                home_goals = driver.find_elements(By.CLASS_NAME,"sr-hth-last-matches__score-home")
                goals_list = []
                for goal in home_goals:
                    goals_list.append(goal.text.replace("\n",""))
                home_goals = driver.find_elements(By.CLASS_NAME,"sr-hth-last-matches__score-away")
                for goal in home_goals:
                    goals_list.append(goal.text.replace("\n",""))
                time.sleep(2)
                driver.find_element(By.CSS_SELECTOR,'button.sr-slider-button6.srt-fill-neutral-2.srm-dir-right.srt-fill-text-secondary.sr-hth-inline-slidernavigation__arrow-container-2').click()
                time.sleep(2)
                away_goals = driver.find_elements(By.CLASS_NAME,"sr-hth-last-matches__score-home")
                for goal in away_goals:
                    goals_list.append(goal.text.replace("\n",""))
                away_goals = driver.find_elements(By.CLASS_NAME,"sr-hth-last-matches__score-away")
                for goal in away_goals:
                    goals_list.append(goal.text.replace("\n",""))
                time.sleep(2)
                goals_list = [x for x in goals_list if x]
                goals_list = [int(value) for value in goals_list]
                average = sum(goals_list) / len(goals_list)
                result, scores_list = analyze_goals(goal_list=goals_list, threshold=self.over_threshold)
                print("Goals_list:", goals_list)
                print("result:", result, 'Scores_list = ', scores_list)
                print("Average Goals:", average)
                time.sleep(2)
                # if average > 1.1:
                if result > 2.1:
                    odds_text = self.bet_place(4)
                    print(f" Over {self.over_threshold} selected, adding 1 to the counter")
                    match_bet = BetpawaBets(event_time = match_day, event_link=driver.current_url, event_match=match_particpants, event_tournament=match_details, selection=odds_text, event_data= str(scores_list))
                    self.events_counter = self.events_counter + 1
                    try:
                        match_bet.save()
                    except Exception as e:
                        print(e)

                elif result <-2.1 :
                # elif average <-1.1 :
                    odds_text = self.bet_place(5)
                    match_bet = BetpawaBets(event_time = match_day, event_link=driver.current_url, event_match=match_particpants, event_tournament=match_details, selection=odds_text, event_data= str(scores_list))
                    self.events_counter = self.events_counter + 1
                    print(f" Under {self.over_threshold} selected, adding 1 to the counter")
                    try:
                        match_bet.save()
                    except Exception as e:
                        print(e)                    
                else:
                    print("No Bet Selected, count is still ", self.events_counter)
            else:
                print(f'match is further than {self.diff} days')
        except Exception as e:
            print("failed to get match", e)
    
    def bet_place(self, bet):
        # 1 homewin
        # 2 draw
        # 3 Away Win
        # 4 over threshold
        # 5 under threshold
        match bet:
            case 4:
                try:
                    self.driver.find_element(By.CSS_SELECTOR,"[data-test-id='tabs-goals']").click()
                    time.sleep(2)
                    odd_select = self.driver.find_element(By.XPATH,f"//span[contains(text(),'Over ({self.over_threshold})')]")
                    odd_select.click()
                    time.sleep(1)
                    odd_text = odd_select.text
                    
                except:
                    print("No bet")
            
            case 5:
                try:
                    self.driver.find_element(By.CSS_SELECTOR,"[data-test-id='tabs-goals']").click()
                    time.sleep(2)
                    odd_select = self.driver.find_element(By.XPATH,f"//span[contains(text(),'Under ({self.over_threshold})')]")
                    odd_select.click()
                    time.sleep(1)
                    odd_text = odd_select.text
                except:
                    print("No bet")
            case _:
                print('No work here')

        return odd_text

    def create_code(self):
        time.sleep(2)
        #find a element with text booking code
        self.driver.find_element(By.XPATH,"//a[contains(text(),'Booking code ')]").click()
        time.sleep(2)
        code = self.driver.find_element(By.CSS_SELECTOR,".table.copy-bets")
        time.sleep(2)
        print(code.text)
        bet_code = code.text.split()
        bet_code = f"{bet_code[2]}"
        bet_odds = self.driver.find_element(By.CSS_SELECTOR,".side-bar.content").text
        current_time = datetime.now().strftime("%d%m%Y_%H%M%S")
        file_name = f"betcodes/{bet_code} - {current_time}.txt"
        with open(file_name, 'a') as file:
            file.write(f'{bet_code} \n\n\n{bet_odds}')
        self.send_sms(bet_code)
        print(f"\n\n\n sent {bet_code} \n\n\n")
        self.driver.get('https://www.betpawa.ug/')
        time.sleep(1)
        self.driver.find_element(By.XPATH,"//a[contains(text(),'Clear Betslip')]").click()
        time.sleep(1)

    def send_sms(self,bet_code):
        # Send the code to the sms api
        url = "https://www.egosms.co/api/v1/plain/"
        # The parameters to be sent to the ego sms api
        password = "UBTEB2022"
        username = "UBTEB"
        sender = "Frank"
        number = "256775236691"
        numbertwo = "256701580442"
        numberthree = "256704959857"
        numberfour = "256782496706"
        message = f"{bet_code}"
        parameters = {
            'username': html.escape(username),
            'password': html.escape(password),
            'number': html.escape(number),
            'message': html.escape(message),
            'sender': html.escape(sender)
        }
        timeout = 5
        parameterstwo = {
            'username': html.escape(username),
            'password': html.escape(password),
            'number': html.escape(numbertwo),
            'message': html.escape(message),
            'sender': html.escape(sender)
        }
        parametersthree = {
            'username': html.escape(username),
            'password': html.escape(password),
            'number': html.escape(numberthree),
            'message': html.escape(message),
            'sender': html.escape(sender)
        }
        parametersfour = {
            'username': html.escape(username),
            'password': html.escape(password),
            'number': html.escape(numberfour),
            'message': html.escape(message),
            'sender': html.escape(sender)
        }
        # Check for the internet connection and make the request
        try:
            # sending post request and saving response as response object
            r = requests.get(url=url, params=parameters, timeout=timeout)
            # r = requests.get(url=url, params=parameterstwo, timeout=timeout)
            # r = requests.get(url=url, params=parametersthree, timeout=timeout)
            # r = requests.get(url=url, params=parametersfour, timeout=timeout)
            response = r.text
            print(response)
        except(requests.ConnectionError, requests.Timeout) as exception:
            print("Check your internet connection")

    def place_bet(self, amount=10):
        time.sleep(1)
        self.driver.get('https://www.betpawa.ug/')
        time.sleep(1)
        self.driver.find_element(By.CSS_SELECTOR,"#betslip-form-stake-input").send_keys(amount)
        time.sleep(1)
        self.driver.find_element(By.CSS_SELECTOR,"#betslip-form-stake-input").send_keys(Keys.RETURN)
        time.sleep(1)
        
    def close(self):
        self.driver.close()

    def place_tickets(self, no_events, no_tickets):
        self.driver.get('https://www.betpawa.ug/')
        time.sleep(1)
        print("no of tickets = ", no_tickets, "events =", no_events)
        for i in range(no_tickets):
            current_time = timezone.now()
            events_to_place = BetpawaBets.objects.filter(event_time__gt=current_time,is_placed=False).order_by("?")[:no_events]
            print(events_to_place)
            for event in events_to_place:
                self.driver.get(event.event_link)
                time.sleep(3)
                print('\n\n\n',event,'\n\n\n')
                print('\n\n\n',event.selection,'\n',event.event_link,'\n\n\n')
                self.driver.find_element(By.CSS_SELECTOR,"[data-test-id='tabs-goals']").click()
                try:
                    time.sleep(3)
                    odd_select = self.driver.find_element(By.XPATH,f"//span[contains(text(),'{event.selection}')]")
                    odd_select.click()
                    event.is_placed=True
                    event.save()
                except Exception as e:
                    print(e)
                time.sleep(3)
            self.place_bet(5)

