from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import BetLink, Event, Selections, EventSelection, Market, Bookmakers, EventOdds
import logging
import time
from datetime import datetime
from django.utils import timezone
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import re

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process betlinks to create events and their selections'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=None, 
                            help='Limit the number of betlinks to process')
        parser.add_argument('--delay', type=float, default=1.0,
                            help='Delay between requests (in seconds) to avoid rate limiting')
        parser.add_argument('--headless', action='store_true',
                            help='Run Chrome in headless mode')
        parser.add_argument('--diff', type=int, default=21,
                            help='Maximum date difference in days for events to process')

    def handle(self, *args, **options):
        limit = options['limit']
        delay = options['delay']
        headless = options['headless']
        diff = options['diff']

        # Initialize the Chrome driver
        self.setup_driver(headless)
        
        try:
            # Get betlinks to process - all betlinks since they're dynamic
            betlinks = self._get_betlinks(limit)
            
            if not betlinks:
                self.stdout.write(self.style.WARNING('No betlinks found to process'))
                return

            self.stdout.write(f'Processing {len(betlinks)} betlinks...')
            
            # Process each betlink
            processed_count = 0
            error_count = 0
            skipped_count = 0
            event_count = 0
            
            for betlink in betlinks:
                try:
                    processed, stats = self._process_betlink(betlink, diff, delay)
                    if processed:
                        processed_count += 1
                        event_count += stats['processed']
                        skipped_count += stats['skipped']
                        self.stdout.write(self.style.SUCCESS(
                            f'Processed betlink: {betlink.league} - {stats["processed"]} events processed, {stats["skipped"]} skipped'
                        ))
                    else:
                        self.stdout.write(f'Skipped betlink: {betlink.league} - No events found')
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing betlink {betlink.league_code}: {str(e)}")
                    self.stdout.write(self.style.ERROR(f'Error processing betlink {betlink.league}: {str(e)}'))
            
            self.stdout.write(self.style.SUCCESS(
                f'Summary: {processed_count} betlinks processed, {event_count} events created/updated, '
                f'{skipped_count} events skipped, {error_count} errors'
            ))
        finally:
            # Ensure the browser is closed when done
            self.close_driver()

    def setup_driver(self, headless=False):
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
        
        self.driver = webdriver.Chrome(service=ChromeService(driver_path), options=chrome_options)
        self.driver.maximize_window()
        
    def close_driver(self):
        """Close the Chrome webdriver"""
        if hasattr(self, 'driver'):
            self.driver.quit()

    def _get_betlinks(self, limit):
        """Get betlinks to process"""
        queryset = BetLink.objects.all().order_by('order')
        
        if limit:
            queryset = queryset[:limit]
            
        return queryset

    # @transaction.atomic
    def _process_betlink(self, betlink, diff, delay):
        """Process a single betlink to create events and selections"""
        self.stdout.write(f'Processing betlink: {betlink.league} ({betlink.link_url})')
        
        # Get event links from the betlink page
        event_links = self._get_event_urls(betlink.link_url)
        
        if not event_links:
            self.stdout.write(self.style.WARNING(f'No event links found for {betlink.league}'))
            return False, {'processed': 0, 'skipped': 0}
            
        self.stdout.write(f'Found {len(event_links)} events for {betlink.league}')
        
        # Stats for this betlink
        stats = {
            'processed': 0,  # Events created or updated
            'skipped': 0     # Events skipped (too far in the future, etc.)
        }
        
        # Process each event link
        for event_link in event_links:
            try:
                result = self._process_event(event_link, betlink.league, diff)
                if result == 'processed':
                    stats['processed'] += 1
                elif result == 'skipped':
                    stats['skipped'] += 1
                
                # Add delay between requests to avoid rate limiting
                if delay > 0:
                    time.sleep(delay)
            except Exception as e:
                logger.error(f"Error processing event {event_link}: {str(e)}")
                self.stdout.write(self.style.ERROR(f"Error processing event {event_link}: {str(e)}"))
                
        return True, stats
    
    def _get_event_urls(self, url):
        """Extract event URLs from a betlink page using Selenium
        
        Based on the get_event_urls method from betpawa.py
        """
        driver = self.driver
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
            self.stdout.write(self.style.ERROR(f"Error getting event URLs: {str(e)}"))
            return []
    
    def _process_event(self, event_link, tournament, max_days_diff):
        """Process a single event to create an Event object and its selections
        
        Based on the get_statistics method from betpawa.py
        """
        driver = self.driver
        wait = WebDriverWait(driver, 20)
        
        try:
            driver.get(event_link)
            time.sleep(5)
            
            # Extract event information
            try:
                match_date = driver.find_element(By.CSS_SELECTOR, '.event-header-date').text
                print("match_date",match_date)
                match_details = driver.find_element(By.CSS_SELECTOR, '.event-header-details').text
                print("match_details",match_details)
                home_team = driver.find_elements(By.CSS_SELECTOR, '.event-participant')[0].text
                print("home_team",home_team)
                away_team = driver.find_elements(By.CSS_SELECTOR, '.event-participant')[1].text
                print("away_team",away_team)
                
                self.stdout.write(f"Event: {home_team} vs {away_team} | Date: {match_date} | Details: {match_details}")
                
                # Parse date difference and convert to datetime
                event_datetime = self._parse_event_datetime(match_date)
                
                # Only process events within the specified date range
                date_diff = self._get_date_diff(event_datetime)
                
                if date_diff <= max_days_diff:
                    # Create/update the event in the database
                    event = self._create_event(
                        event_link=event_link,
                        event_time=event_datetime,
                        home_team=home_team,
                        away_team=away_team,
                        tournament=tournament
                    )
                    
                    # Add selections to the event
                    self._add_selections_to_event(event)
                    
                    # Extract and save odds for the event
                    self._extract_and_save_odds(event, driver)
                    
                    return 'processed'
                else:
                    self.stdout.write(f"Skipping event - too far in the future ({date_diff} days)")
                    return 'skipped'
            
            except Exception as e:
                logger.error(f"Error extracting event data from {event_link}: {str(e)}")
                self.stdout.write(self.style.ERROR(f"Error extracting event data: {str(e)}"))
                return 'skipped'
                
        except Exception as e:
            logger.error(f"Error processing event {event_link}: {str(e)}")
            self.stdout.write(self.style.ERROR(f"Error processing event: {str(e)}"))
            return 'skipped'
    
    def _parse_event_datetime(self, date_string):
        """Parse event date/time string to datetime object
        
        Sample formats:
        "5:00 pm Sat 19/04"
        "10:30 pm Thu 24/04"
        """
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
            self.stdout.write(self.style.WARNING(f"Could not parse date: '{date_string}', using current time"))
            return timezone.now()
            
        except Exception as e:
            logger.error(f"Error parsing date '{date_string}': {str(e)}")
            self.stdout.write(self.style.WARNING(f"Date parsing error: {str(e)}, using current time"))
            return timezone.now()
    
    def _get_date_diff(self, event_datetime):
        """Get the difference in days between now and the event datetime"""
        if not event_datetime:
            return 0
            
        now = timezone.now()
        diff = event_datetime - now
        
        # Return the difference in days, rounded up if there's a partial day
        return max(0, diff.days + (1 if diff.seconds > 0 else 0))
    
    def _create_event(self, event_link, event_time, home_team, away_team, tournament):
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
                self.stdout.write(self.style.SUCCESS(f"Created new event: {event_link} - {home_team} vs {away_team}"))
            else:
                # Update the existing event - times or participants might change
                event.event_time = event_time
                event.home_team = home_team
                event.away_team = away_team
                event.tournament = tournament
                event.save()
                self.stdout.write(f"Updated existing event: {event_link} - {home_team} vs {away_team}")
            
            return event
            
        except Exception as e:
            logger.error(f"Error creating/updating event: {str(e)}")
            raise
    
    def _add_selections_to_event(self, event):
        """Add default selections to an event based on predefined markets"""
   
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
            self.stdout.write(f"  Added {selections_added} selections to event")
        else:
            self.stdout.write(f"  All selections already exist for event")
        
    def _extract_and_save_odds(self, event, driver):
        """Extract odds from the event page and save them with default bookmaker (ID 1)"""
        try:
            # Get the default bookmaker (ID 1)
            default_bookmaker = Bookmakers.objects.get(id=1)
            self.stdout.write(f"Using default bookmaker: {default_bookmaker.name}")
            
            odds_saved = 0
            
            event_selections1x2 = EventSelection.objects.filter(event=event, selection__market__market_name="1X2 | Full Time")
            print("event_selections1x2", event_selections1x2)
            #get the irst events-sub-container
            events_sub_containers = driver.find_elements(By.XPATH, "//div[@class='events-sub-container']")
            print("events_sub_containers", events_sub_containers[0].text)  
            #convert the text into an array using linebreak as a delimiter
            odds_text = events_sub_containers[0].text
            odds_array = odds_text.split('\n')
            print("odds_array", odds_array)
            #extract parts of the array that can be are odds i.e the have a decimal point in them
            odds = [float(x) for x in odds_array if '.' in x]
            print("final odds", odds)       
            #save the odds to the database
            for i, event_selection in enumerate(event_selections1x2):
                EventOdds.objects.create(
                    event_selection=event_selection,
                    bookmaker=default_bookmaker,
                    odd=odds[i]
                )
                odds_saved += 1
            return odds_saved
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Error extracting odds: {str(e)}\n{error_traceback}")
            self.stdout.write(self.style.ERROR(f"Error extracting and saving odds: {str(e)}\n{error_traceback}"))
            return 0
