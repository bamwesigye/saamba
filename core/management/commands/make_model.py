from django.core.management.base import BaseCommand
from django.conf import settings
import pandas as pd
import numpy as np
import os
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
from sklearn import neighbors, preprocessing
from xgboost import XGBClassifier
from sklearn.neighbors import KNeighborsClassifier



import joblib
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

class Command(BaseCommand):
    help = 'Train betting model for FTR prediction and to calculate ROI'

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
        model, X_test, y_test = self.train_and_save_model(X, y, 'ftr_prediction_model',df=df)
        predictions = model.predict(X_test)
        # Convert X_test, y_pred, and y_test into a single DataFrame
        y_pred_series = pd.Series(predictions, name='y_pred')  # Predicted labels
        y_test_series = pd.Series(y_test.values, name='y_test')  # True labels
        result_df = pd.concat([X_test.reset_index(drop=True), y_test_series, y_pred_series], axis=1)
        # Export to Excel
        result_df.to_excel('predictions.xlsx', index=False)
        # Print result_df file path0.
        

    def load_data(self, folder_path):
        columns_to_extract = ['Div','Date', 'HomeTeam', 'AwayTeam', 'FTR', 'B365H', 'B365D', 'B365A','B365>2.5', 'B365<2.5']
        dfs = []
        encodings = ['utf-8', 'ISO-8859-1', 'Windows-1252']
        
        for filename in os.listdir(folder_path):
            if filename.endswith('.csv'):
                file_path = os.path.join(folder_path, filename)
                
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, usecols=columns_to_extract, encoding=encoding)
                        df =df.replace([np.inf, -np.inf], np.nan).dropna()
                        dfs.append(df)
                        # self.stdout.write(self.style.SUCCESS(f"Successfully read {filename} with {encoding} encoding"))
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
        le = LabelEncoder()
        # df['HomeTeam'] = le.fit_transform(df['HomeTeam'])
        # df['AwayTeam'] = le.fit_transform(df['AwayTeam'])
        df['Div'] = le.fit_transform(df['Div'])
        # Get the mapping of original values to encoded values
        mapping = dict(zip(le.classes_, le.transform(le.classes_)))

        df = df.rename(columns={
            'B365>2.5': 'over25_odds', 
            'B365<2.5': 'under25_odds', 
            'B365H': 'home_odds', 
            'B365A': 'away_odds',
            'B365D': 'draw_odds'
            })
        
        print(mapping)        
        features = ['HomeTeam', 'AwayTeam', 'DayOfWeek', 'Month', 'B365H', 'B365D', 'B365A', 'B365>2.5', 'B365<2.5']
        features = ['Div','DayOfWeek','Month', 'home_odds', 'draw_odds', 'away_odds', 'over25_odds', 'under25_odds']
        X = df[features]
        y = df['FTR']
        return X, y, df

    def train_and_save_model(self, X, y, model_name, df):
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
       # Define models to evaluate
        models = {
            # 'SVC': SVC(C=1.0, kernel='rbf', gamma='scale', probability=True),
            'KNN': KNeighborsClassifier(n_neighbors=7, weights='distance', p=2),
            'KNN10': KNeighborsClassifier(n_neighbors=10, weights='distance'),
            'KNN300': KNeighborsClassifier(n_neighbors=300, weights='distance'),
            'KNN500': KNeighborsClassifier(n_neighbors=500, weights='distance'),
            'RandomForest': RandomForestClassifier(n_estimators=300, max_depth=15, max_features='sqrt'),
            'RandomForest10': RandomForestClassifier(n_estimators=10, random_state=42),
            'RandomForest100': RandomForestClassifier(n_estimators=100, random_state=42),
            'RandomForest500': RandomForestClassifier(n_estimators=500, random_state=42),
            'AdaBoost': AdaBoostClassifier(n_estimators=100, learning_rate=0.5),
            'XGBoost': XGBClassifier(n_estimators=200, learning_rate=0.1, max_depth=5, colsample_bytree=0.8),
            'GradientBoosting': GradientBoostingClassifier(n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42),
            'DecisionTree': DecisionTreeClassifier(max_depth=10, max_features='sqrt'),
            # 'SVM': SVC(C=1.0, kernel='rbf', gamma='scale', probability=True),
            'NaiveBayes' : GaussianNB(),
            'LogisticRegression': LogisticRegression(solver='liblinear', C=1.0),
            'GaussianNB': GaussianNB()
        }
        best_score_accuracy = -1000000
        best_model_accuracy = None
        best_model_name_accuracy = None
        best_score_roi = -1000000
        best_model_roi = None
        best_model_name_roi = None
        # Evaluate each model
        for name_model, model in models.items():
            print("\n")
            print("Model:", name_model)
            # Train the model
            model.fit(X_train, y_train)
            
            accuracy = model.score(X_test, y_test)
            print("Accuracy:", accuracy)
            # Evaluate the model
            cross_val_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
            print("Cross-Validation Scores:", cross_val_scores)
            print("Mean Accuracy:", cross_val_scores.mean())
            print("Standard Deviation:", cross_val_scores.std())
            predictions = model.predict(X_test)

            odds = df.loc[y_test.index, ['home_odds','draw_odds','away_odds','over25_odds', 'under25_odds']].to_dict('records')

            roi, win_rate, profit, total_bets = self.calculate_roi(predictions, y_test, odds)

            self.stdout.write(self.style.SUCCESS(f"ROI: {roi:.4f}%"))
            self.stdout.write(self.style.SUCCESS(f"Win Rate: {win_rate:.4f}"))
            self.stdout.write(self.style.SUCCESS(f"Profit/loss: £{profit:.4f}"))
            self.stdout.write(self.style.SUCCESS(f"Total Stake: £{total_bets}"))
             
            if accuracy > best_score_accuracy:
                best_score_accuracy = accuracy
                best_model_accuracy = model
                best_model_name_accuracy = name_model

            if roi > best_score_roi:
                best_score_roi = roi
                best_model_roi = model
                best_model_name_roi = name_model
        
        model_path_accuracy = os.path.join(settings.BASE_DIR, f'{model_name}_accuracy.joblib')
        joblib.dump(best_model_accuracy, model_path_accuracy)
        self.stdout.write(self.style.SUCCESS(f'Model saved to {model_path_accuracy}'))
        print(f"\n\n\n\n Best Model: {best_model_name_accuracy} with Accuracy: {best_score_accuracy:.4f}")

        model_path_roi = os.path.join(settings.BASE_DIR, f'{model_name}_roi.joblib')
        joblib.dump(best_model_roi, model_path_roi)
        self.stdout.write(self.style.SUCCESS(f'Model saved to {model_path_roi}'))
        print(f"\n\n\n\n Best Model: {best_model_name_roi} with roi: {best_score_accuracy:.4f}")
        return model, X_test, y_test

    def calculate_roi(self, predictions, actual, odds):
        total_bets = len(predictions)
        wins = 0
        returns = 0

        for pred, act, match_odds in zip(predictions, actual, odds):
            if pred == act:
                wins += 1
                if pred == 'H' and not np.isnan(match_odds['home_odds']):
                    returns += match_odds['home_odds']
                elif pred == 'A' and not np.isnan(match_odds['away_odds']):
                    returns += match_odds['away_odds']
                elif pred == 'D' and not np.isnan(match_odds['draw_odds']):
                    returns += match_odds['draw_odds']
            else:
                returns -= 1
        profit = returns - total_bets
        roi = (profit / total_bets) * 100
        win_rate = wins / total_bets if total_bets > 0 else 0

        return roi, win_rate, profit, total_bets