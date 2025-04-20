from django.core.management.base import BaseCommand
from core.models import Market, Selections, Bookmakers, BetLink
from django.db import transaction

class Command(BaseCommand):
    help = 'Set up initial data for Saamba betting automation app'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Force setup even if data already exists')

    @transaction.atomic
    def handle(self, *args, **options):
        self.setup_markets_and_selections(force=options['force'])
        self.setup_bookmakers(force=options['force'])
        self.setup_betlinks(force=options['force'])
        # Add other setup functions here as needed
        
        self.stdout.write(self.style.SUCCESS('Saamba setup completed successfully!'))

    def setup_markets_and_selections(self, force=False):
        """Set up all betting markets and their selections."""
        # If force is False and we already have markets, skip this step
        if not force and Market.objects.exists():
            self.stdout.write('Markets already exist. Skipping market setup. Use --force to override.')
            return
            
        self.stdout.write('Setting up betting markets and selections...')
        
        # Predefined markets with their selections
        markets = {
            '1X2 | Full Time': [
                {'code': '1', 'name': 'Home', 'description': 'Home team wins'},
                {'code': 'X', 'name': 'Draw', 'description': 'Match ends in a draw'},
                {'code': '2', 'name': 'Away', 'description': 'Away team wins'},
            ],
            'Double Chance | Full Time': [
                {'code': '1X', 'name': 'Home or Draw', 'description': 'Home team wins or match ends in a draw'},
                {'code': 'X2', 'name': 'Draw or Away', 'description': 'Match ends in a draw or away team wins'},
                {'code': '12', 'name': 'Home or Away', 'description': 'Either team wins (no draw)'},
            ],
            'Both Teams To Score | Full Time': [
                {'code': 'Yes', 'name': 'Yes', 'description': 'Both teams score at least one goal'},
                {'code': 'No', 'name': 'No', 'description': 'At least one team fails to score'},
            ],
            'Over/Under | Full Time': [
                {'code': 'Over 0.5', 'name': 'Over 0.5', 'description': 'More than 0.5 goals scored'},
                {'code': 'Under 0.5', 'name': 'Under 0.5', 'description': 'Less than 0.5 goals scored'},
                {'code': 'Over 1.5', 'name': 'Over 1.5', 'description': 'More than 1.5 goals scored'},
                {'code': 'Under 1.5', 'name': 'Under 1.5', 'description': 'Less than 1.5 goals scored'},
                {'code': 'Over 2.5', 'name': 'Over 2.5', 'description': 'More than 2.5 goals scored'},
                {'code': 'Under 2.5', 'name': 'Under 2.5', 'description': 'Less than 2.5 goals scored'},
                {'code': 'Over 3.5', 'name': 'Over 3.5', 'description': 'More than 3.5 goals scored'},
                {'code': 'Under 3.5', 'name': 'Under 3.5', 'description': 'Less than 3.5 goals scored'},
                {'code': 'Over 4.5', 'name': 'Over 4.5', 'description': 'More than 4.5 goals scored'},
                {'code': 'Under 4.5', 'name': 'Under 4.5', 'description': 'Less than 4.5 goals scored'},
                {'code': 'Over 5.5', 'name': 'Over 5.5', 'description': 'More than 5.5 goals scored'},
                {'code': 'Under 5.5', 'name': 'Under 5.5', 'description': 'Less than 5.5 goals scored'},
                {'code': 'Over 6.5', 'name': 'Over 6.5', 'description': 'More than 6.5 goals scored'},
                {'code': 'Under 6.5', 'name': 'Under 6.5', 'description': 'Less than 6.5 goals scored'},
            ],
            'Over/Under | Home Team | Full Time':[
                {'code': 'T1Over 0.5', 'name': 'Over 0.5', 'description': 'More than 0.5 goals scored'},
                {'code': 'T1Under 0.5', 'name': 'Under 0.5', 'description': 'Less than 0.5 goals scored'},
                {'code': 'T1Over 1.5', 'name': 'Over 1.5', 'description': 'More than 1.5 goals scored'},
                {'code': 'T1Under 1.5', 'name': 'Under 1.5', 'description': 'Less than 1.5 goals scored'},
                {'code': 'T1Over 2.5', 'name': 'Over 2.5', 'description': 'More than 2.5 goals scored'},
                {'code': 'T1Under 2.5', 'name': 'Under 2.5', 'description': 'Less than 2.5 goals scored'},
                {'code': 'T1Over 3.5', 'name': 'Over 3.5', 'description': 'More than 3.5 goals scored'},

            ],
            'Over/Under | Away Team | Full Time':[
                {'code': 'T2Over 0.5', 'name': 'Over 0.5', 'description': 'More than 0.5 goals scored'},
                {'code': 'T2Under 0.5', 'name': 'Under 0.5', 'description': 'Less than 0.5 goals scored'},
                {'code': 'T2Over 1.5', 'name': 'Over 1.5', 'description': 'More than 1.5 goals scored'},
                {'code': 'T2Under 1.5', 'name': 'Under 1.5', 'description': 'Less than 1.5 goals scored'},
                {'code': 'T2Over 2.5', 'name': 'Over 2.5', 'description': 'More than 2.5 goals scored'},
                {'code': 'T2Under 2.5', 'name': 'Under 2.5', 'description': 'Less than 2.5 goals scored'},
                {'code': 'T2Over 3.5', 'name': 'Over 3.5', 'description': 'More than 3.5 goals scored'},

            ],
            '1X2 First Half': [
                {'code': 'FH1', 'name': 'Home First Half', 'description': 'Home team wins the first half'},
                {'code': 'FHX', 'name': 'Draw First Half', 'description': 'First half ends in a draw'},
                {'code': 'FH2', 'name': 'Away First Half', 'description': 'Away team wins the first half'},
            ],
            '1X2 Second Half': [
                {'code': 'SH1', 'name': 'Home Second Half', 'description': 'Home team wins the second half'},
                {'code': 'SHX', 'name': 'Draw Second Half', 'description': 'Second half ends in a draw'},
                {'code': 'SH2', 'name': 'Away Second Half', 'description': 'Away team wins the second half'},
            ],
            'Over/Under First Half': [
                {'code': 'Over 0.5 H1', 'name': 'Over 0.5 First Half', 'description': 'More than 0.5 goals scored in first half'},
                {'code': 'Under 0.5 H1', 'name': 'Under 0.5 First Half', 'description': 'Less than 0.5 goals scored in first half'},
                {'code': 'Over 1.5 H1', 'name': 'Over 1.5 First Half', 'description': 'More than 1.5 goals scored in first half'},
                {'code': 'Under 1.5 H1', 'name': 'Under 1.5 First Half', 'description': 'Less than 1.5 goals scored in first half'},
                {'code': 'Over 2.5 H1', 'name': 'Over 2.5 First Half', 'description': 'More than 2.5 goals scored in first half'},
                {'code': 'Under 2.5 H1', 'name': 'Under 2.5 First Half', 'description': 'Less than 2.5 goals scored in first half'},
            ],
        }

        # Create all markets and their selections
        for market_name, selections_list in markets.items():
            market, created = Market.objects.get_or_create(market_name=market_name)
            action = 'Created' if created else 'Using existing'
            self.stdout.write(f'{action} market "{market_name}"')

            for selection in selections_list:
                sel, sel_created = Selections.objects.get_or_create(
                    market=market,
                    selection_code=selection['code'],
                    defaults={
                        'selection': selection['name'], 
                        'description': selection['description']
                    }
                )
                if sel_created:
                    self.stdout.write(f'  Created selection "{selection["name"]}" (code: {selection["code"]})')
                else:
                    # Update existing record if force is True
                    if force:
                        sel.selection = selection['name']
                        sel.description = selection['description']
                        sel.save(update_fields=['selection', 'description'])
                        self.stdout.write(f'  Updated selection "{selection["name"]}" (code: {selection["code"]}")')
                    else:
                        self.stdout.write(f'  Selection exists: "{selection["name"]}" (code: {selection["code"]}")')

    def setup_bookmakers(self, force=False):
        """Set up initial bookmakers."""
        if not force and Bookmakers.objects.exists():
            self.stdout.write('Bookmakers already exist. Skipping bookmaker setup. Use --force to override.')
            return
            
        self.stdout.write('Setting up bookmakers...')
        
        # List of bookmakers to create
        bookmakers = [
            {'name': 'Betpawa', 'url': 'https://www.betpawa.ug/'},
            {'name': 'Betway', 'url': 'https://www.betway.co.ug/'},
            {'name': 'SportPesa', 'url': 'https://ke.sportpesa.com/'},
            # Add more bookmakers as needed
        ]
        
        for bookmaker in bookmakers:
            bm, created = Bookmakers.objects.get_or_create(
                name=bookmaker['name'],
                defaults={'url': bookmaker.get('url', '')}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created bookmaker "{bookmaker["name"]}"'))
            else:
                self.stdout.write(f'Bookmaker exists: "{bookmaker["name"]}"')
                
    def setup_betlinks(self, force=False):
        """Set up initial bet links for various leagues."""
        if not force and BetLink.objects.exists():
            self.stdout.write('BetLinks already exist. Skipping BetLink setup. Use --force to override.')
            return
            
        self.stdout.write('Setting up bet links...')
        
        # Ensure we have at least one bookmaker
        if not Bookmakers.objects.exists():
            self.setup_bookmakers(force=True)
            
        default_bookmaker = Bookmakers.objects.first()
        
        # List of betlinks to create - Popular leagues with their links
        betlinks = [
            {
                'league_code': 'EPL',
                'link_url': 'https://www.betpawa.ug/events/group/11965?marketId=1X2&competitions=11965&categoryId=2',
                'league': 'Premier League',
                'country': 'England',
                'Level': 'Tier 1',
                'order': 1.0,
                'bookmaker': default_bookmaker
            },
            {
                'league_code': 'LALIGA',
                'link_url': 'https://www.betpawa.ug/events/group/12019?marketId=1X2&competitions=12019&categoryId=2',
                'league': 'La Liga',
                'country': 'Spain',
                'Level': 'Tier 1',
                'order': 2.0,
                'bookmaker': default_bookmaker
            },
            {
                'league_code': 'SERIEA',
                'link_url': 'https://www.betpawa.ug/events/group/12063?marketId=1X2&competitions=12063&categoryId=2',
                'league': 'Serie A',
                'country': 'Italy',
                'Level': 'Tier 1',
                'order': 3.0,
                'bookmaker': default_bookmaker
            },
            {
                'league_code': 'BUNDESLIGA',
                'link_url': 'https://www.betpawa.ug/events/group/11984?marketId=1X2&competitions=11984&categoryId=2',
                'league': 'Bundesliga',
                'country': 'Germany',
                'Level': 'Tier 1',
                'order': 4.0,
                'bookmaker': default_bookmaker
            },
            {
                'league_code': 'LIGUE1',
                'link_url': 'https://www.betpawa.ug/events/group/12015?marketId=1X2&competitions=12015&categoryId=2',
                'league': 'Ligue 1',
                'country': 'France',
                'Level': 'Tier 1',
                'order': 5.0,
                'bookmaker': default_bookmaker
            }
        ]
        
        for betlink_data in betlinks:
            betlink, created = BetLink.objects.get_or_create(
                league_code=betlink_data['league_code'],
                defaults={
                    'link_url': betlink_data['link_url'],
                    'league': betlink_data['league'],
                    'country': betlink_data['country'],
                    'Level': betlink_data['Level'],
                    'order': betlink_data['order'],
                    'bookmaker': betlink_data['bookmaker']
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created BetLink for "{betlink_data["league"]}" in {betlink_data["country"]}'))
            else:
                self.stdout.write(f'BetLink exists: "{betlink_data["league"]}" in {betlink_data["country"]}')
