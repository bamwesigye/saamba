from django.core.management.base import BaseCommand
from core.models import Market, Selections

class Command(BaseCommand):
    help = 'Populate standard betting markets and their selections'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Populate all predefined markets')
        parser.add_argument('--market', type=str, help='Specify a single market to populate')
        parser.add_argument('--list', action='store_true', help='List available predefined markets')

    def handle(self, *args, **options):
        # Predefined markets with their selections
        markets = {
            '1X2': [
                {'code': '1', 'name': 'Home', 'description': 'Home team wins'},
                {'code': 'X', 'name': 'Draw', 'description': 'Match ends in a draw'},
                {'code': '2', 'name': 'Away', 'description': 'Away team wins'},
            ],
            'Double Chance': [
                {'code': '1X', 'name': 'Home or Draw', 'description': 'Home team wins or match ends in a draw'},
                {'code': 'X2', 'name': 'Draw or Away', 'description': 'Match ends in a draw or away team wins'},
                {'code': '12', 'name': 'Home or Away', 'description': 'Either team wins (no draw)'},
            ],
            'Both Teams To Score': [
                {'code': 'Yes', 'name': 'Yes', 'description': 'Both teams score at least one goal'},
                {'code': 'No', 'name': 'No', 'description': 'At least one team fails to score'},
            ],
            'Over/Under': [
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
            'Half Time/Full Time': [
                {'code': '1/1', 'name': 'Home/Home', 'description': 'Home team leads at half time and wins at full time'},
                {'code': '1/X', 'name': 'Home/Draw', 'description': 'Home team leads at half time and match ends in a draw'},
                {'code': '1/2', 'name': 'Home/Away', 'description': 'Home team leads at half time and away team wins at full time'},
                {'code': 'X/1', 'name': 'Draw/Home', 'description': 'Match is tied at half time and home team wins at full time'},
                {'code': 'X/X', 'name': 'Draw/Draw', 'description': 'Match is tied at half time and at full time'},
                {'code': 'X/2', 'name': 'Draw/Away', 'description': 'Match is tied at half time and away team wins at full time'},
                {'code': '2/1', 'name': 'Away/Home', 'description': 'Away team leads at half time and home team wins at full time'},
                {'code': '2/X', 'name': 'Away/Draw', 'description': 'Away team leads at half time and match ends in a draw'},
                {'code': '2/2', 'name': 'Away/Away', 'description': 'Away team leads at half time and wins at full time'},
            ],
            '1X2 First Half': [
                {'code': '1H1', 'name': 'Home First Half', 'description': 'Home team wins the first half'},
                {'code': 'XH1', 'name': 'Draw First Half', 'description': 'First half ends in a draw'},
                {'code': '2H1', 'name': 'Away First Half', 'description': 'Away team wins the first half'},
            ],
            '1X2 Second Half': [
                {'code': '1H2', 'name': 'Home Second Half', 'description': 'Home team wins the second half'},
                {'code': 'XH2', 'name': 'Draw Second Half', 'description': 'Second half ends in a draw'},
                {'code': '2H2', 'name': 'Away Second Half', 'description': 'Away team wins the second half'},
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

        if options['list']:
            self.stdout.write("Available predefined markets:")
            for market_name in markets.keys():
                self.stdout.write(f"- {market_name}")
            return

        if options['market']:
            market_name = options['market']
            if market_name in markets:
                self._create_market_with_selections(market_name, markets[market_name])
            else:
                self.stdout.write(self.style.ERROR(f"Market '{market_name}' not found in predefined list"))
                self.stdout.write("Available markets:")
                for name in markets.keys():
                    self.stdout.write(f"- {name}")
        elif options['all']:
            for market_name, selections in markets.items():
                self._create_market_with_selections(market_name, selections)
        else:
            self.stdout.write("Please specify --all to populate all markets or --market 'Market Name' to populate a specific market")
            self.stdout.write("Use --list to see available markets")

    def _create_market_with_selections(self, market_name, selections_list):
        """Create a market and its selections."""
        market, created = Market.objects.get_or_create(market=market_name)
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created market "{market_name}"'))
        else:
            self.stdout.write(f'Using existing market "{market_name}"')

        for selection in selections_list:
            sel, sel_created = Selections.objects.get_or_create(
                market=market,
                selection_code=selection['code'],
                defaults={
                    'selection': selection['name'], 
                    'desription': selection['description']
                }
            )
            if sel_created:
                self.stdout.write(self.style.SUCCESS(f'  Created selection "{selection["name"]}" (code: {selection["code"]})'))
            else:
                # Update existing record
                sel.selection = selection['name']
                sel.desription = selection['description']
                sel.save(update_fields=['selection', 'desription'])
                self.stdout.write(f'  Updated selection "{selection["name"]}" (code: {selection["code"]}")')
