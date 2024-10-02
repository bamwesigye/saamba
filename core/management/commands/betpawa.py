from django.core.management.base import BaseCommand
from django.utils import timezone


# selenium 4
import pyperclip
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


from sklearn.preprocessing import LabelEncoder


from tqdm import tqdm
from datetime import datetime
from core.models import AccountBalance, BetLink, BetpawaBets, PlacedBets, BetpawaMatch
from .calculate import analyze_goals, get_date_diff, convert_percentage_to_value


import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import joblib

class Command(BaseCommand):
    help = 'Betpawa Events Scraper'

    def add_arguments(self, parser):
        parser.add_argument('--events', type=int, default=30, help='Events Threshold')
        parser.add_argument('--overs', type=float, default=1.5, help='Overs Threshold')
        parser.add_argument('--diff', type=int, default=3, help='Overs Threshold')
        parser.add_argument('--tickets', type=int, default=5, help='number of bets per game')
        parser.add_argument('--min_odds', type=float, default=1.2, help='Minimum Odds')
        parser.add_argument('--max_odds', type=float, default=7.0, help='Maximum Odds')


    def handle(self, *args, **kwargs):
        events_threshold = kwargs['events']
        overs_threshold = kwargs['overs']
        diff = kwargs['diff']
        tickets = kwargs['tickets']
        min_odds = kwargs['min_odds']
        max_odds = kwargs['max_odds']
        # overs_list = [3.5,2.5,1.5,0.5]
        overs_list = [3.5,1.5,2.5]
        for over in overs_list:
            betpawa = Betpawa(events_threshold, over, diff,tickets=tickets, min_odds=min_odds, max_odds=max_odds)
            links = BetLink.objects.all().order_by('?')
            for link in tqdm(links, desc="Progress"):
                self.stdout.write(f"Working on {link.link_url} - {link.league}")
                betpawa.place_events(link.link_url)
            betpawa.create_code()
            betpawa.place_bet(amount=1)
        
        time.sleep(3)


# Set up Chrome options for headless mode
chrome_options = Options()
# chrome_options.add_argument("--headless")

class Betpawa:
    def __init__(self, events_threshold=35, over_threshold=3.5, diff=3, tickets=10, min_odds=1.2, max_odds=15.0):
        driver_path = ChromeDriverManager().install()
        if driver_path:
             driver_name = driver_path.split('/')[-1]
             if driver_name!="chromedriver":
                  driver_path = "/".join(driver_path.split('/')[:-1]+["chromedriver"])
                  os.chmod(driver_path, 0o755)
        self.driver = webdriver.Chrome(service=ChromeService(driver_path))
        # self.driver = webdriver.Chrome(options= chrome_options, service=ChromeService(ChromeDriverManager().install()))
        self.driver.get("https://betpawa.ug/")
        self.driver.maximize_window()
        self.events_counter = 0
        self.events_threshold = events_threshold
        self.over_threshold = over_threshold
        self.diff = diff
        self.tickets = tickets
        self.min_odds = min_odds
        self.max_odds = max_odds
        time.sleep(2)
        self.login()
        # time.sleep(2)
        # self.get_account_balance()


    def login(self):
        
        self.driver.get("https://www.betpawa.ug/login")
        time.sleep(2)
        self.driver.find_element(By.CSS_SELECTOR,"#login-form-phoneNumber").send_keys("775236691")
        time.sleep(2)
        self.driver.find_element(By.CSS_SELECTOR,"#login-form-password-input").send_keys("34454392")
        time.sleep(5)
        self.driver.find_element(By.CSS_SELECTOR,'[data-test-id="logInButton"]').click()
        time.sleep(4)

    def get_odds(self,event_link):
        self.driver.get(event_link)
        time.sleep(2)
        odds = self.driver.find_elements(By.CLASS_NAME,"event-bet")
        for odd in odds:
            # print(odd.text)
            pass
    
    def get_event_urls(self,urls_link):
        driver = self.driver
        wait = WebDriverWait(driver, 20)
        driver.get(urls_link)
        time.sleep(2)
        event_links = []
        events = self.driver.find_elements(By.CLASS_NAME,"event-match")       
        for event in events:
            event_links.append(event.get_attribute("href"))
        return event_links

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
                    self.place_bet(500)
                    time.sleep(2)
        except Exception as e:
            print("Failed to get league", e)

    def get_upcoming(self,diff=24):
        self.driver.get('https://www.betpawa.ug/upcoming?marketId=_1X2&categoryId=2')
        time.sleep(2)
        data = input("scroll down to the end and Press Enter to continue...")
        events = self.driver.find_elements(By.CLASS_NAME,"event-match")
        event_links = [event.get_attribute("href") for event in events]
        for event in event_links:
            self.get_statistics(event)
            print(f"{self.events_counter} counted vs {self.events_threshold} ")
            if self.events_counter > self.events_threshold:
                time.sleep(2)
                self.create_code()
                self.events_counter = 0
                self.place_bet(200)
                time.sleep(2)
        self.place_bet(200)

    def get_statistics(self, event_link,):
        driver = self.driver
        driver.set_window_size(1080,800)
        wait = WebDriverWait(driver, 20)
        
        try:
            driver.get(event_link)
            time.sleep(5)
            print(driver.current_url)
            # driver.execute_script("document.body.style.zoom='150%'")
            time.sleep(5)
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
                if result > 3.1:
                    odds_text = self.bet_place(4)
                    # odds_text = self.bet_place(5) # reverse selection
                    print(f" Over {self.over_threshold} selected, adding 1 to the counter")
                    match_bet = BetpawaBets(event_time = match_day, event_link=driver.current_url, event_match=match_particpants, event_tournament=match_details, selection=odds_text, event_data= str(scores_list))
                    self.events_counter = self.events_counter + 1
                    try:
                        match_bet.save()
                    except Exception as e:
                        print(e)
                elif result <- 3.1 :
                # elif average <-1.1 :
                    odds_text = self.bet_place(5)
                    # odds_text = self.bet_place(4) #reverse selection
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
    
    def get_stat_ht(self,event_link):
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
                if result > 3.1:
                    odds_text = self.bet_place(4)
                    # odds_text = self.bet_place(5) # reverse selection
                    print(f" Over {self.over_threshold} selected, adding 1 to the counter")
                    match_bet = BetpawaBets(event_time = match_day, event_link=driver.current_url, event_match=match_particpants, event_tournament=match_details, selection=odds_text, event_data= str(scores_list))
                    self.events_counter = self.events_counter + 1
                    try:
                        match_bet.save()
                    except Exception as e:
                        print(e)
                elif result <- 3.1 :
                # elif average <-1.1 :
                    odds_text = self.bet_place(5)
                    # odds_text = self.bet_place(4) #reverse selection
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
            case 1:
                try:
                    odd_select = self.driver.find_elements(By.CSS_SELECTOR,'.event-bet')
                    time.sleep(1)
                    odd_select = odd_select[0]
                    odd_select.click()
                    time.sleep(1)
                    odd_text = odd_select.text
                except:
                    print("Failed to bet")
            case 2:
                try:
                    odd_select = self.driver.find_elements(By.CSS_SELECTOR,'.event-bet')
                    time.sleep(1)
                    odd_select = odd_select[1]
                    odd_select.click()
                    time.sleep(1)
                    odd_text = odd_select.text
                except:
                    print("Failed to bet")
            case 3:
                try:
                    odd_select = self.driver.find_elements(By.CSS_SELECTOR,'.event-bet')
                    time.sleep(1)
                    odd_select = odd_select[2]
                    odd_select.click()
                    time.sleep(1)
                    odd_text = odd_select.text
                except:
                    print("Failed to bet")
            case 4:
                try:
                    # Locate and click the "Over 2.5" under Full Time with an exact match
                    odd_select = self.driver.find_element(By.XPATH, f"//*[text()='Over/Under | Full Time']/following::span[contains(text(),'Over ({self.over_threshold})')]")
                    odd_select.click()
                    time.sleep(1)
                    odd_text = odd_select.text                    
                except:
                    print("No bet")            
            case 5:
                try:
                    # Locate and click the "under 2.5" under Full Time with an exact match
                    odd_select = self.driver.find_element(By.XPATH, f"//*[text()='Over/Under | Full Time']/following::span[contains(text(),'Under ({self.over_threshold})')]")
                    odd_select.click()
                    time.sleep(1)
                    odd_text = odd_select.text   
                except:
                    print("No bet")
            case _:
                odd_select= None
                print('No work here')
        return odd_text

    def create_code(self):
        time.sleep(2)
        self.driver.find_element(By.XPATH,"//span[contains(text(),'Booking code')]").click()
        time.sleep(2)
        code = self.driver.find_element(By.CSS_SELECTOR,".clipboard-copy-text-small.copy-text-button").click()
        time.sleep(2)
        # print(code.text)
        bet_code = pyperclip.paste()
        # bet_code = f"{bet_code[2]}"
        # bet_odds = self.driver.find_element(By.CSS_SELECTOR,".side-bar.content").text
        current_time = datetime.now().strftime("%d%m%Y_%H%M%S")
        booking_link = f"https://www.betpawa.ug/?bookingCode={bet_code}"
        csv_file = 'betcodes/betpawa.csv'
        with open(csv_file, 'a') as file:
            file.write(f'{bet_code},{booking_link},{current_time}\n')
        print(f"\n\n\n saved {bet_code} \n\n\n")
        print(f"\n\n\n booking link -  https://www.betpawa.ug/?bookingCode={bet_code} \n\n\n")
        self.send_sms(booking_link)
        self.driver.get('https://www.betpawa.ug/')
        return bet_code
        34454392  
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
            r = requests.get(url=url, params=parameterstwo, timeout=timeout)
            r = requests.get(url=url, params=parametersthree, timeout=timeout)
            r = requests.get(url=url, params=parametersfour, timeout=timeout)
            response = r.text
            print(response)
        except(requests.ConnectionError, requests.Timeout) as exception:
            print("Check your internet connection")

    def place_bet(self, amount=200, betcode=None):
        bet_code = betcode
        wait = WebDriverWait(self.driver, 20)
        try:
            self.driver.get('https://www.betpawa.ug/')
            time.sleep(2)
            self.driver.find_element(By.CSS_SELECTOR,"#betslip-form-stake-input").click()
            time.sleep(1)
            self.driver.find_element(By.CSS_SELECTOR,"#betslip-form-stake-input").send_keys(amount)
            time.sleep(2)
            self.driver.find_element(By.CSS_SELECTOR,".place-bet").click()
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".open-details-container")))
            time.sleep(2)
            betslip_link = self.driver.find_element(By.CSS_SELECTOR,".open-details-container")
            print(betslip_link)
            betslip_link = betslip_link.find_element(By.TAG_NAME,'a').get_attribute('href')
            placedbet = PlacedBets(betcode=bet_code, betlink=betslip_link, stake=amount)
            placedbet.save()
            self.driver.get('https://www.betpawa.ug/')
        except Exception as e:
            print("No bets selected \n\n\n", e)
        
    def close(self):
        self.driver.close()

    def place_tickets(self, no_events, no_tickets, ):
        self.driver.get('https://www.betpawa.ug/')
        time.sleep(1)
        print("no of tickets = ", no_tickets, "events =", no_events)
        for i in range(no_tickets):
            current_time = timezone.now()
            print(self.min_odds,"min_odds", self.max_odds, "max odds")
            start_time = current_time + timezone.timedelta(hours=1.5)
            end_time = current_time + timezone.timedelta(hours=48)
            events_to_place = BetpawaBets.objects.filter(event_time__range=(start_time,end_time),is_placed=False).order_by("?")
            print(events_to_place.count(), "events to place")
            events_counter = 0
            for event in events_to_place:
                self.driver.get(event.event_link)
                print(f"\n\n\nplacing:  {event.selection} \n\n\n")
                time.sleep(3)
                try:
                    time.sleep(3)
                    odd_select = self.driver.find_element(By.XPATH, f"//*[text()='Over/Under | Full Time']/following::span[contains(text(),{event.selection})]")
                    odds_value = odd_select.find_element(By.XPATH,"..")
                    odds_value = float(odds_value.text[-4:])
                    print(event.event_match, " - ", event.selection, "odds=", odds_value)
                    if self.min_odds < odds_value < self.max_odds:
                        odd_select.click()
                        event.is_placed=True
                        event.save()
                        events_counter = events_counter + 1
                        print("\n placed event, odds are sufficient\n\n events placed = ", events_counter)
                    else:
                        print("skipping selection, Odds do not match \n\n Events still ", events_counter)
                except Exception as e:
                    print(e)
                if events_counter > no_events:
                    break
                time.sleep(3)
            self.place_bet(amount=500)

    def get_event_data(self, url):
        driver = self.driver
        wait = WebDriverWait(driver, 20)
        driver.get(url)
        time.sleep(2)
        print("match url = ", url)
        try:
                
            match_date = driver.find_element(By.CSS_SELECTOR,'.event-header-date').text
            date_diff, match_time = get_date_diff(match_date)
            print(match_time)
            match_particpants = driver.find_elements(By.CSS_SELECTOR,'.event-participant')
            match_particpants = [participant.text for participant in match_particpants]
            print(match_particpants)
            tournament = driver.find_element(By.CSS_SELECTOR,'.event-breadcrumb').text
            print(tournament)
            print(match_date,'hours difference = ', date_diff)
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".event-statistics-text")))
            time.sleep(2)    
            driver.find_element(By.CSS_SELECTOR,".event-statistics-text").click() # change to wait until
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-test-tab='teamstats']")))
            time.sleep(1)
            driver.find_element(By.CSS_SELECTOR,'[data-test-tab="teamstats"]').click()
            time.sleep(1)
            stats = driver.find_element(By.CSS_SELECTOR,'.widget-wrapper').text
            stats = stats.split('\n')
            print(stats)
            time.sleep(4)
            #driver.find_element(By.CSS_SELECTOR,'button.sr-slider-button6.srt-fill-neutral-2.srm-dir-right.srt-fill-text-secondary.sr-hth-inline-slidernavigation__arrow-container-2').click()
            #time.sleep(1)
            #stats_two = driver.find_element(By.CSS_SELECTOR,'.widget-wrapper').text
            #stats_two = stats_two.split('\n')
            #print(stats_two)
            match = BetpawaMatch(
                match_link = url,
                match_time=match_time,
                home_team = match_particpants[0],
                away_team = match_particpants[1],
                tournament = tournament,
                home_played = int(stats[8]),
                away_played = int(stats[10]),
                home_win_percentage = convert_percentage_to_value(stats[11]),
                away_win_percentage = convert_percentage_to_value(stats[13]),
                home_total_goals = int(stats[14]) if stats[14].isdigit() else None,
                away_total_goals = int(stats[16]) if stats[16].isdigit() else None,
                home_average_scored = float(stats[17]),
                away_average_scored = float(stats[19]),
                home_average_conceded = float(stats[20]),
                away_average_conceded = float(stats[22]),
                home_bts_percentage = convert_percentage_to_value(stats[23]),
                away_bts_percentage = convert_percentage_to_value(stats[25]),
                home_over_15 = convert_percentage_to_value(stats[30]),
                away_over_15 = convert_percentage_to_value(stats[32]),
                home_over_25 = convert_percentage_to_value(stats[33]),
                away_over_25 = convert_percentage_to_value(stats[35]),
                ht_home_over_05 = convert_percentage_to_value(stats[36]),
                ht_away_over_05 = convert_percentage_to_value(stats[38]),
                ht_home_over_15 = convert_percentage_to_value(stats[39]),
                ht_away_over_15 = convert_percentage_to_value(stats[41]),
                home_yellow_cards = int(stats[42]) if stats[42].isdigit() else None,
                away_yellow_cards = int(stats[44])if stats[44].isdigit() else None,
                home_total_cards = int(stats[45])if stats[45].isdigit() else None,
                away_total_cards = int(stats[47])if stats[47].isdigit() else None
            )
            try:
                match.save()
                print(match)
                time.sleep(1)
            except Exception as e:
                print('Invalid match Data Skipping or duplicate match',e)

        except Exception as e:
            print("failed to get match data\n\n",e)
    
    def get_account_balance(self):
        driver = self.driver
        wait = WebDriverWait(driver, 20)
        try:                
            # driver.get('https://www.betpawa.ug/bets/settled')
            time.sleep(2)
            balance = driver.find_element(By.CSS_SELECTOR,'.balance').text
            balance = balance.split(' ')[-1]
            balance = balance.replace(',','')
            balance = float(balance)
            print(" Current balance = ",balance)
            acc_bal = AccountBalance(day = datetime.now(),amount=balance)
            acc_bal.save()
        except Exception as e:
            print("Account balance",30)
            balance = 0
        return balance
    
    def get_model_prediction(self, event_link,div=0):
        #load the model
        model = joblib.load('ftr_prediction_model.joblib')
        le = LabelEncoder()
        #navigate to page
        
        driver = self.driver
        wait = WebDriverWait(driver, 20)
        driver = self.driver
        wait = WebDriverWait(driver, 20)
        driver.get(event_link)
        time.sleep(2)
        print("match url = ", event_link)
        try:                                
            match_date = driver.find_element(By.CSS_SELECTOR,'.event-header-date').text
            date_diff, match_time = get_date_diff(match_date)
            print(match_time)
            match_particpants = driver.find_elements(By.CSS_SELECTOR,'.event-participant')
            match_particpants = [participant.text for participant in match_particpants]
            print(match_particpants)
            tournament = driver.find_element(By.CSS_SELECTOR,'.event-breadcrumb').text
            tournament = tournament.split('/')[-1]
            print(tournament)
            print(match_date,'hours difference = ', date_diff)
            if date_diff <= self.diff :
                time.sleep(1)
                bets = driver.find_elements(By.CSS_SELECTOR,'.event-odds')
                bets = [bet.text for bet in bets]
                bet1 = bets[0]
                betx = bets[1]
                bet2 = bets[2]
                odd_select = self.driver.find_element(By.XPATH, f"//*[text()='Over/Under | Full Time']/following::span[contains(text(),'Over (2.5)')]")
                time.sleep(1)
                odds_value = odd_select.find_element(By.XPATH,"..")
                odds_value = float(odds_value.text[-4:])
                beto25 = odds_value
                time.sleep(2)
                odd_select = self.driver.find_element(By.XPATH, f"//*[text()='Over/Under | Full Time']/following::span[contains(text(),'Under (2.5)')]")
                time.sleep(2)
                odds_value = odd_select.find_element(By.XPATH,"..")
                odds_value = float(odds_value.text[-4:])
                betu25 = odds_value
                Day = match_time.weekday()
                # print("match Date = ",match_time.format('%d-%m-%Y'))
                print("match_time = ",match_time)
                print("match_particpants = ",match_particpants)
                print("tournament = ",tournament)
                print("date_diff = ",date_diff)
                print("bet1 = ",bet1)
                print("betx = ",betx)
                print("bet2 = ",bet2)
                print("beto25 = ",beto25)
                print("betu25 = ",betu25)

                match_data = {
                    'Div': [div],  # Replace with your actual scraped data
                    'DayOfWeek': [Day],
                    'B365H': [bet1],  # Example odds for Home win
                    'B365D': [betx],  # Example odds for Draw
                    'B365A': [bet2],  # Example odds for Away win
                    'B365>2.5': [beto25],  # Example odds for over 2.5 goals
                    'B365<2.5': [betu25],  # Example odds for under 2.5 goals
                }
                data = pd.DataFrame(match_data)
                features = ['Div','B365H', 'B365D', 'B365A', 'B365>2.5', 'B365<2.5']
                X_new = data[features]

                # Make predictions
                probabilities = model.predict_proba(X_new)
                print(probabilities)
                prediction = model.predict(X_new)
                print(prediction)

                if prediction == 'A':
                    away_prob = probabilities[:, 0]
                    print(f"Away win - {away_prob}")
                    if away_prob >= 0.5:
                        self.bet_place(3)
                        print("adding 1 to events_counter = ",self.events_counter)
                        self.events_counter += 1
                    else:
                        print("skipped away win")               
                if prediction == 'D':
                    draw_prob = probabilities[:, 1]
                    print(f"Draw - {draw_prob}")
                    if draw_prob >= 0.5:
                        self.bet_place(2)
                        self.events_counter += 1
                        print("adding 1 to events_counter = ",self.events_counter)
                    else:
                        print("skipped draw")
                if prediction == 'H':
                    home_prob = probabilities[:, 2]
                    print(f"Home win - {home_prob}")
                    if home_prob >= 0.5:
                        self.bet_place(1)
                        self.events_counter += 1
                        print("adding 1 to events_counter = ",self.events_counter)
                    else:
                        print("skipped home win")                    
                if self.events_counter >= self.events_threshold:
                    betcode = self.create_code()
                    self.place_bet(betcode=betcode)
                    self.events_counter = 0
                else:
                    print("events remaining = ",self.events_threshold-self.events_counter)
            else:
                print("Date difference greater than 48 hours")
            print("\n\n\n")
        except Exception as e:
            print("Something went wrong, Skipping this match", e)


    def get_over_model_prediction(self, event_link,div=0):
        #load the model
        model = joblib.load('goals_prediction_model_accuracy.joblib')
        le = LabelEncoder()
        #navigate to page
        
        driver = self.driver
        wait = WebDriverWait(driver, 20)
        driver = self.driver
        wait = WebDriverWait(driver, 20)
        driver.get(event_link)
        time.sleep(2)
        print("match url = ", event_link)
        try:                                
            match_date = driver.find_element(By.CSS_SELECTOR,'.event-header-date').text
            date_diff, match_time = get_date_diff(match_date)
            print(match_time)
            match_particpants = driver.find_elements(By.CSS_SELECTOR,'.event-participant')
            match_particpants = [participant.text for participant in match_particpants]
            print(match_particpants)
            tournament = driver.find_element(By.CSS_SELECTOR,'.event-breadcrumb').text
            tournament = tournament.split('/')[-1]
            print(tournament)
            print(match_date,'hours difference = ', date_diff)
            if date_diff <= self.diff :
                time.sleep(1)
                bets = driver.find_elements(By.CSS_SELECTOR,'.event-odds')
                bets = [bet.text for bet in bets]
                bet1 = bets[0]
                betx = bets[1]
                bet2 = bets[2]
                odd_select = self.driver.find_element(By.XPATH, f"//*[text()='Over/Under | Full Time']/following::span[contains(text(),'Over (2.5)')]")
                time.sleep(1)
                odds_value = odd_select.find_element(By.XPATH,"..")
                odds_value = float(odds_value.text[-4:])
                beto25 = odds_value
                time.sleep(2)
                odd_select = self.driver.find_element(By.XPATH, f"//*[text()='Over/Under | Full Time']/following::span[contains(text(),'Under (2.5)')]")
                time.sleep(2)
                odds_value = odd_select.find_element(By.XPATH,"..")
                odds_value = float(odds_value.text[-4:])
                betu25 = odds_value
                Day = match_time.weekday()
                print("Day of the week value = ",Day)
                # print("match Date = ",match_time.format('%d-%m-%Y'))
                print("match_time = ",match_time)
                print("match_particpants = ",match_particpants)
                print("tournament = ",tournament)
                print("date_diff = ",date_diff)
                print("bet1 = ",bet1)
                print("betx = ",betx)
                print("bet2 = ",bet2)
                print("beto25 = ",beto25)
                print("betu25 = ",betu25)

                match_data = {
                    'Div': [div],  # Replace with your actual scraped data
                    'DayOfWeek': [Day],
                    'home_odds': [bet1],  # Example odds for Home win
                    'draw_odds': [betx],  # Example odds for Draw
                    'away_odds': [bet2],  # Example odds for Away win
                    'over25_odds': [beto25],  # Example odds for over 2.5 goals
                    'under25_odds': [betu25],  # Example odds for under 2.5 goals
                }

                data = pd.DataFrame(match_data)
                features = ['Div','home_odds', 'draw_odds', 'away_odds', 'over25_odds', 'under25_odds']
                X_new = data[features]
                # Make predictions
                probabilities = model.predict_proba(X_new)
                print(probabilities)
                prediction = model.predict(X_new)
                print(prediction)

                if prediction == True:
                    over_prob = probabilities[:, 1]
                    if over_prob >= 0.5:
                        self.bet_place(4)
                        print("adding 1 to events_counter = ",self.events_counter)
                        self.events_counter += 1
                    else:
                        print("Skipped Over 2.5 goals")  
                if prediction == False:
                    under_prob = probabilities[:, 0]
                    if under_prob >= 0.5:
                        self.bet_place(5)
                        print("adding 1 to events_counter = ",self.events_counter)
                        self.events_counter += 1
                    else:
                        print("skipped Under 2.5 goals win")    
                if self.events_counter >= self.events_threshold:
                    betcode = self.create_code()
                    self.place_bet(betcode=betcode)
                    self.events_counter = 0
                else:
                    print("events remaining = ",self.events_threshold-self.events_counter)
            else:
                print("Date difference greater than 48 hours")
            print("\n\n\n")
        except Exception as e:
            print("Something went wrong, Skipping this match", e)