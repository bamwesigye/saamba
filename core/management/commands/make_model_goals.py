from django.core.management.base import BaseCommand
from django.conf import settings
import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
import joblib

class Command(BaseCommand):
    help = 'Train betting model for FTR prediction and calculate ROI'

    def add_arguments(self, parser):
        parser.add_argument('--data_folder', type=str, default=os.path.join(settings.BASE_DIR, 'data'), help='Path to the folder containing CSV files')
        parser.add_argument('--unit-stake', type=float, default=10, help='Unit stake for each bet')
        parser.add_argument('--bank', type=float, default=1000, help='Starting bank amount')

    def handle(self, *args, **options):
        data_folder = options['data_folder']
        unit_stake = options['unit_stake']
        bank = options['bank']

        self.stdout.write(self.style.SUCCESS(f'Starting model training with data from {data_folder}'))

        df = self.load_data(data_folder)
        X, y, df = self.preprocess_data(df)
        
        model, X_test, y_test = self.train_and_save_model(X, y, 'goals_prediction_model')

        predictions = model.predict(X_test)

        # Print classification report
        self.stdout.write(self.style.SUCCESS("Classification Report:"))
        self.stdout.write(classification_report(y_test, predictions))

        odds = df.loc[y_test.index, ['B365H', 'B365D', 'B365A', 'B365>2.5', 'B365<2.5']].to_dict('records')

        roi, win_rate, profit, total_stake = self.calculate_roi(predictions, y_test, odds, unit_stake, bank)

        self.stdout.write(self.style.SUCCESS(f"ROI: {roi:.2f}%"))
        self.stdout.write(self.style.SUCCESS(f"Win Rate: {win_rate:.2f}"))
        self.stdout.write(self.style.SUCCESS(f"Profit: £{profit:.2f}"))
        self.stdout.write(self.style.SUCCESS(f"Total Stake: £{total_stake:.2f}"))

    def load_data(self, folder_path):
        columns_to_extract = ['Div','Date', 'HomeTeam', 'AwayTeam', 'FTR','FTHG','FTAG','HTHG','HTAG', 'B365H', 'B365D', 'B365A','B365>2.5', 'B365<2.5']
        dfs = []
        encodings = ['utf-8', 'ISO-8859-1', 'Windows-1252']
        
        for filename in os.listdir(folder_path):
            if filename.endswith('.csv'):
                file_path = os.path.join(folder_path, filename)
                
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, usecols=columns_to_extract, encoding=encoding)
                        dfs.append(df)
                        self.stdout.write(self.style.SUCCESS(f"Successfully read {filename} with {encoding} encoding"))
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error reading {filename}: {str(e)}"))
                        break
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to read {filename} with any of the attempted encodings"))
        
        if not dfs:
            raise ValueError("No data could be loaded from the CSV files")
        
        return pd.concat(dfs, ignore_index=True)

    def preprocess_data(self, df):
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
        df['DayOfWeek'] = df['Date'].dt.dayofweek
        df['Month'] = df['Date'].dt.month
        df['over25'] = df['FTHG'] + df['FTAG'] > 2.5
        
        le = LabelEncoder()
        df['HomeTeam'] = le.fit_transform(df['HomeTeam'])
        df['AwayTeam'] = le.fit_transform(df['AwayTeam'])
        df['Div'] = le.fit_transform(df['Div'])
        # Get the mapping of original values to encoded values
        mapping = dict(zip(le.classes_, le.transform(le.classes_)))

        print(mapping)
        
        features = ['Div','HomeTeam', 'AwayTeam', 'DayOfWeek', 'Month', 'B365H', 'B365D', 'B365A', 'B365>2.5', 'B365<2.5']
        features = ['Div','B365H', 'B365D', 'B365A', 'B365>2.5', 'B365<2.5']
        X = df[features]
        y = df['over25']

        print(df.tail(20))
        
        return X, y, df

    def train_and_save_model(self, X, y, model_name):
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)
        
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X_train, y_train)
        
        model_path = os.path.join(settings.BASE_DIR, f'{model_name}.joblib')
        joblib.dump(model, model_path)
        self.stdout.write(self.style.SUCCESS(f'Model saved to {model_path}'))
        
        return model, X_test, y_test

    def calculate_roi(self, predictions, actual, odds, unit_stake, bank):
        total_bets = len(predictions)
        wins = 0
        returns = 0

        for pred, act, match_odds in zip(predictions, actual, odds):
            if pred == act:
                wins += 1
                if pred == True  and not np.isnan(match_odds['B365>2.5']):
                    returns += unit_stake * match_odds['B365>2.5']
                elif pred == False and not np.isnan(match_odds['B365<2.5']):
                    returns += unit_stake * match_odds['B365<2.5']
        
        total_stake = total_bets * unit_stake
        profit = returns - total_stake
        
        if bank == 0:
            self.stdout.write(self.style.WARNING("Warning: Bank is zero. Unable to calculate ROI."))
            roi = 0
        else:
            roi = (profit / bank) * 100

        win_rate = wins / total_bets if total_bets > 0 else 0

        return roi, win_rate, profit, total_stake