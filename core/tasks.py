
from celery import shared_task
import logging
import time
from datetime import datetime
import re
import os
import pytz

from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.models import BetLink, Event, Selections, EventSelection, Market, Bookmakers, EventOdds

logger = logging.getLogger(__name__)

@shared_task
def process_betlinks(limit=None, delay=1.0, headless=True, diff=21):
    """
    Process betlinks to create events and capture their odds
    
    Args:
        limit (int, optional): Limit the number of betlinks to process
        delay (float, optional): Delay between requests in seconds
        headless (bool, optional): Whether to run Chrome in headless mode
        diff (int, optional): Maximum date difference in days for events to process
    
    Returns:
        dict: Summary of processing results
    """
    logger.info(f'Starting betlinks processing task. Limit: {limit}, Delay: {delay}, Headless: {headless}, Max diff: {diff}')
    
    # Initialize the Chrome driver
    driver = setup_driver(headless)
    
    try:
        # Get betlinks to process
        betlinks = get_betlinks(limit)
        
        if not betlinks:
            logger.warning('No betlinks found to process')
            return {"status": "warning", "message": "No betlinks found to process"}

        logger.info(f'Processing {len(betlinks)} betlinks...')
        
        # Process each betlink
        processed_count = 0
        error_count = 0
        skipped_count = 0
        event_count = 0
        
        for betlink in betlinks:
            try:
                processed, stats = process_betlink(driver, betlink, diff, delay)
                if processed:
                    processed_count += 1
                    event_count += stats['processed']
                    skipped_count += stats['skipped']
                    logger.info(
                        f'Processed betlink: {betlink.league} - {stats["processed"]} events processed, {stats["skipped"]} skipped'
                    )
                else:
                    logger.info(f'Skipped betlink: {betlink.league} - No events found')
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing betlink {betlink.league_code}: {str(e)}")
        
        summary = {
            'status': 'success',
            'processed_count': processed_count,
            'event_count': event_count,
            'skipped_count': skipped_count,
            'error_count': error_count
        }
        
        logger.info(
            f'Summary: {processed_count} betlinks processed, {event_count} events created/updated, '
            f'{skipped_count} events skipped, {error_count} errors'
        )
        
        return summary
    
    except Exception as e:
        logger.error(f"Critical error in process_betlinks task: {str(e)}")
        return {"status": "error", "message": str(e)}
    
    finally:
        # Ensure the browser is closed when done
        if driver:
            driver.quit()

def setup_driver(headless=False):
    """Set up the Chrome webdriver"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    
    # Additional options to make Selenium more robust
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Handle pathing issues with chromedriver
    driver_path = ChromeDriverManager().install()
    if driver_path:
        driver_name = driver_path.split('/')[-1]
        if driver_name != "chromedriver":
            driver_path = "/".join(driver_path.split('/')[:-1]+["chromedriver"])
            os.chmod(driver_path, 0o755)
    
    driver = webdriver.Chrome(service=ChromeService(driver_path), options=chrome_options)
    driver.maximize_window()
    return driver

def get_betlinks(limit):
    """Get betlinks to process"""
    queryset = BetLink.objects.all().order_by('order')
    
    if limit:
        queryset = queryset[:limit]
        
    return queryset

def process_betlink(driver, betlink, diff, delay):
    """Process a single betlink to create events and selections"""
    logger.info(f'Processing betlink: {betlink.league} ({betlink.link_url})')
    
    # Get event links from the betlink page
    event_links = get_event_urls(driver, betlink.link_url)
    
    if not event_links:
        logger.warning(f'No event links found for {betlink.league}')
        return False, {'processed': 0, 'skipped': 0}
        
    logger.info(f'Found {len(event_links)} events for {betlink.league}')
    
    # Stats for this betlink
    stats = {
        'processed': 0,  # Events created or updated
        'skipped': 0     # Events skipped (too far in the future, etc.)
    }
    
    # Process each event link
    for event_link in event_links:
        try:
            result = process_event(driver, event_link, betlink.league, diff)
            if result == 'processed':
                stats['processed'] += 1
            elif result == 'skipped':
                stats['skipped'] += 1
            
            # Add delay between requests to avoid rate limiting
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            logger.error(f"Error processing event {event_link}: {str(e)}")
            
    return True, stats

def get_event_urls(driver, url):
    """Extract event URLs from a betlink page using Selenium"""
    wait = WebDriverWait(driver, 20)
    
    try:
        driver.get(url)
        time.sleep(2)
        
        # Wait for the events to load
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "event-match")))
        
        # Extract event links
        event_links = []
        events = driver.find_elements(By.CLASS_NAME, "event-match")
        
        for event in events:
            event_link = event.get_attribute("href")
            if event_link:
                event_links.append(event_link)
                
        return event_links
        
    except Exception as e:
        logger.error(f"Error getting event URLs from {url}: {str(e)}")
        return []

def process_event(driver, event_link, tournament, max_days_diff):
    """Process a single event to create an Event object and its selections"""
    wait = WebDriverWait(driver, 20)
    
    try:
        driver.get(event_link)
        time.sleep(5)
        
        # Extract event information
        try:
            match_date = driver.find_element(By.CSS_SELECTOR, '.event-header-date').text
            print("match_date", match_date)
            match_details = driver.find_element(By.CSS_SELECTOR, '.event-header-details').text
            print("match_details", match_details)
            home_team = driver.find_elements(By.CSS_SELECTOR, '.event-participant')[0].text
            print("home_team", home_team)
            away_team = driver.find_elements(By.CSS_SELECTOR, '.event-participant')[1].text
            print("away_team", away_team)
            
            logger.info(f"Event: {home_team} vs {away_team} | Date: {match_date} | Details: {match_details}")
            
            # Parse date difference and convert to datetime
            event_datetime = parse_event_datetime(match_date)
            
            # Only process events within the specified date range
            date_diff = get_date_diff(event_datetime)
            
            if date_diff <= max_days_diff:
                # Create/update the event in the database
                event = create_event(
                    event_link=event_link,
                    event_time=event_datetime,
                    home_team=home_team,
                    away_team=away_team,
                    tournament=tournament
                )
                
                # Add selections to the event
                add_selections_to_event(event)
                
                # Extract and save odds for the event
                extract_and_save_odds(event, driver)
                
                return 'processed'
            else:
                logger.info(f"Skipping event - too far in the future ({date_diff} days)")
                return 'skipped'
        
        except Exception as e:
            logger.error(f"Error extracting event data from {event_link}: {str(e)}")
            return 'skipped'
            
    except Exception as e:
        logger.error(f"Error processing event {event_link}: {str(e)}")
        return 'skipped'

def parse_event_datetime(date_string):
    """Parse event date/time string to datetime object"""
    try:
        # Extract time, day, and date parts
        match = re.search(r'(\d+:\d+ [ap]m) ([A-Za-z]+) (\d+/\d+)', date_string)
        if match:
            time_str, weekday, date_str = match.groups()
            
            # Extract day and month
            day_month = date_str.split('/')
            if len(day_month) == 2:
                day, month = int(day_month[0]), int(day_month[1])
                
                # Get current year
                current_year = timezone.now().year
                
                # Parse the time (e.g., "5:00 pm")
                time_match = re.search(r'(\d+):(\d+) ([ap]m)', time_str)
                if time_match:
                    hour, minute, am_pm = time_match.groups()
                    hour = int(hour)
                    minute = int(minute)
                    
                    # Adjust hour for PM
                    if am_pm.lower() == 'pm' and hour < 12:
                        hour += 12
                    elif am_pm.lower() == 'am' and hour == 12:
                        hour = 0
                    
                    # Create datetime with Kampala timezone
                    kampala_tz = pytz.timezone('Africa/Kampala')
                    event_datetime = timezone.datetime(current_year, month, day, hour, minute, 0)
                    
                    # If the date is in the past (e.g., for December when it's January),
                    # assume it's for the next year
                    if event_datetime.date() < timezone.now().date():
                        event_datetime = timezone.datetime(current_year + 1, month, day, hour, minute, 0)
                    
                    # Make it timezone-aware
                    event_datetime = kampala_tz.localize(event_datetime)
                    
                    return event_datetime
        
        # Fallback to current time if parsing fails
        logger.warning(f"Could not parse date: '{date_string}', using current time")
        return timezone.now()
        
    except Exception as e:
        logger.error(f"Error parsing date '{date_string}': {str(e)}")
        logger.warning(f"Date parsing error: {str(e)}, using current time")
        return timezone.now()

def get_date_diff(event_datetime):
    """Get the difference in days between now and the event datetime"""
    if not event_datetime:
        return 0
        
    now = timezone.now()
    diff = event_datetime - now
    
    # Return the difference in days, rounded up if there's a partial day
    return max(0, diff.days + (1 if diff.seconds > 0 else 0))

def create_event(event_link, event_time, home_team, away_team, tournament):
    """Create or update an Event in the database"""
    try:
        # Check if event already exists
        event, created = Event.objects.get_or_create(
            event_link=event_link,
            defaults={
                'event_time': event_time,
                'home_team': home_team,
                'away_team': away_team,
                'tournament': tournament
            }
        )
        
        if created:
            logger.info(f"Created new event: {event_link} - {home_team} vs {away_team}")
        else:
            # Update the existing event - times or participants might change
            event.event_time = event_time
            event.home_team = home_team
            event.away_team = away_team
            event.tournament = tournament
            event.save()
            logger.info(f"Updated existing event: {event_link} - {home_team} vs {away_team}")
        
        return event
        
    except Exception as e:
        logger.error(f"Error creating/updating event: {str(e)}")
        raise

def add_selections_to_event(event):
    """Add selections to an event based on predefined markets"""
    selections = Selections.objects.all()
    selections_added = 0

    # Add each selection to the event
    for selection in selections:
        # Create event selection if it doesn't exist
        event_selection, created = EventSelection.objects.get_or_create(
            event=event,
            selection=selection
        )
        
        if created:
            selections_added += 1
                
    if selections_added > 0:
        logger.info(f"  Added {selections_added} selections to event")
    else:
        logger.info(f"  All selections already exist for event")

def extract_and_save_odds(event, driver):
    """Extract odds from the event page and save them with default bookmaker (ID 1)"""
    try:
        # Get the default bookmaker (ID 1)
        default_bookmaker = Bookmakers.objects.get(id=1)
        logger.info(f"Using default bookmaker: {default_bookmaker.name}")
        
        odds_saved = 0
        
        event_selections1x2 = EventSelection.objects.filter(event=event)
        logger.info(f"event_selections1x2 {event_selections1x2}")
        
        # Get the events-sub-container
        events_sub_containers = driver.find_elements(By.XPATH, "//div[@class='events-sub-container']")
        logger.info(f"events_sub_containers {events_sub_containers[0].text}")
        
        # Convert the text into an array using linebreak as a delimiter
        odds_text = events_sub_containers[0].text
        odds_array = odds_text.split('\n')
        logger.info(f"odds_array {odds_array}")
        
        # Extract parts of the array that are odds (have a decimal point)
        odds = [float(x) for x in odds_array if '.' in x]
        logger.info(f"final odds {odds}")
        
        # Save the odds to the database if we have at least 3 selections and 3 odds
        if len(event_selections1x2) >= 3 and len(odds) >= 3:
            EventOdds.objects.create(
                event_selection=event_selections1x2[0],
                bookmaker=default_bookmaker,
                odd=odds[0]
            )
            odds_saved += 1
            
            EventOdds.objects.create(
                event_selection=event_selections1x2[1],
                bookmaker=default_bookmaker,
                odd=odds[1]
            )
            odds_saved += 1
            
            EventOdds.objects.create(
                event_selection=event_selections1x2[2],
                bookmaker=default_bookmaker,
                odd=odds[2]
            )
            odds_saved += 1
            
        return odds_saved
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Error extracting odds: {str(e)}\n{error_traceback}")
        return 0