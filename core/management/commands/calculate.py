from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time, json, requests, html
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



def get_date_diff(date_string='3:00 pm Sat 09/12'):
    # Get the current year
    current_year = datetime.now().strftime("%Y")
    # Concatenate the current year with the existing string
    date_string = date_string + " " + current_year
    date_format = "%I:%M %p %a %d/%m %Y"
    parsed_date_time = datetime.strptime(date_string, date_format)
    current_date_time = datetime.now()
    time_difference = abs(parsed_date_time - current_date_time)
    days = time_difference.days
    return days, parsed_date_time

def analyze_goals(goal_list, threshold = 2.5, ):
    hometeam1 = [goal_list[0],goal_list[3]]
    hometeam2 = [goal_list[1],goal_list[4]]
    hometeam3 = [goal_list[2],goal_list[5]]
    awayteam1 = [goal_list[6],goal_list[9]]
    awayteam2 = [goal_list[7],goal_list[10]]
    awayteam3 = [goal_list[8],goal_list[11]]
    scores_list = [hometeam1,hometeam2,hometeam3,awayteam1,awayteam2,awayteam3]
    overs = sum(1 for score in scores_list if sum(score) > threshold)
    print(overs)
    unders = sum(1 for score in scores_list if sum(score) < threshold)
    print(unders)
    result = overs - unders    
    return result, scores_list



if __name__ == "__main__":
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    links = ['https://www.betpawa.ug/event/16744583','https://www.betpawa.ug/event/15360033','https://www.betpawa.ug/event/16183424','https://www.betpawa.ug/event/15417183']
    for link in links:
        wait = WebDriverWait(driver, 20)
        driver.get(link)
        time.sleep(5)
        try:
            match_date = driver.find_element(By.CSS_SELECTOR,'.event-header-date').text
        except:
            print('skiping live match')
        date_diff = get_date_diff(match_date)
        print(match_date,'hours difference = ', date_diff)
        if date_diff < 3 :
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".event-statistics-text")))
            time.sleep(5)
            match_date = driver.find_element(By.CSS_SELECTOR,'.event-header-date').text
            time.sleep(2)    
            driver.find_element(By.CSS_SELECTOR,".event-statistics-text").click() # change to wait until
            time.sleep(5)
            try:
                wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-test-tab="lastmatches"]')))
            except:
                time.sleep(20)
                driver.find_element(By.CSS_SELECTOR,".event-statistics-text").click()
            try:
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
                result, scores_list = analyze_goals(goal_list=goals_list, threshold=2.5)
                print("Goals_list:", goals_list)
                print("result:", result, 'Scores_list = ', scores_list)
                print("Average Goals:", average)
                print(driver.current_url)
                time.sleep(2)
            except Exception as e:
                print("Skipping Live match", e)
        else:
            print('match is further than 3 days')
