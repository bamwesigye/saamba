import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report


file_path = '/home/frank/code/saamba/core/stat.py'
df = pd.read_csv(file_path)
df.head()

# Data Preprocessing
# Convert categorical columns to numerical
df['Date'] = pd.to_datetime(df['Date'], format="%d/%m/%Y")
df['week_day'] = df['Date'].dt.weekday
# Function to replace ':' with '.' and convert to float
def convert_time_to_float(time_str):
    # Split the time string by ':'
    parts = time_str.split(':')
    # Convert hours and minutes to float
    hours = int(parts[0])
    minutes = int(parts[1]) / 60
    # Return the sum of hours and converted minutes as float
    return hours + minutes

# Apply the conversion function to the 'time' column
df['time_in_hours'] = df['Time'].apply(convert_time_to_float)


df['FTR'] = df['FTR'].map({'H': 1, 'D': 0, 'A': -1})
df['HTR'] = df['HTR'].map({'H': 1, 'D': 0, 'A': -1})

df.head(20)


#Encode home team and away team
from sklearn.preprocessing import LabelEncoder
encoder = LabelEncoder()
df['HomeTeam'] = encoder.fit_transform(df['HomeTeam'])
df['AwayTeam'] = encoder.fit_transform(df['AwayTeam'])
df['Referee'] = encoder.fit_transform(df['Referee'])

df.head(20)

# Select features and target variable
# features = ['HomeTeam',	'AwayTeam', 'home_odds','Referee',	'draw_odds', 'away_odds', 'over25_odds', 'under25_odds','week_day', 'time_in_hours']
# features = ['HomeTeam',	'AwayTeam', 'home_odds','Referee',	'draw_odds', 'away_odds', 'over25_odds', 'under25_odds','week_day', ]
features = ['home_odds','draw_odds','away_odds', 'over25_odds', 'under25_odds','week_day']


target = 'FTR'

X = df[features]
y = df[target]

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Initialize and train the model
# model_A = RandomForestClassifier(n_estimators=100, random_state=0)
model_1 = RandomForestClassifier(n_estimators=50, random_state=0)
model_2 = RandomForestClassifier(n_estimators=100, random_state=0)
model_3 = RandomForestClassifier(n_estimators=100,  random_state=42)
model_4 = RandomForestClassifier(n_estimators=200, min_samples_split=20, random_state=0)
model_5 = RandomForestClassifier(n_estimators=100, max_depth=7, random_state=0)

models = [model_1, model_2, model_3, model_4, model_5]
X_test.head()

def mean_absolute_error(y_true, y_pred):
    return np.mean(np.abs(y_true - y_pred))

def score_model(model, X_train=X_train, X_test=X_test, y_train=y_train, y_test=y_test):
    
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    accuracy = accuracy_score(y_test, preds)
    conf_matrix = confusion_matrix(y_test, preds)
    class_report = classification_report(y_test, preds)

    # Output the evaluation metrics
    print(f'Accuracy: {accuracy}')
    # print('Confusion Matrix:')
    # print(conf_matrix)
    # print('Classification Report:')
    # print(class_report)
    X_test.reset_index()
    
    return accuracy



X_test.reset_index(drop=True)
X_test.head()