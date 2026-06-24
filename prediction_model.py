import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import pickle
import os
import re

class MobilePricePredictor:
    def __init__(self):
        self.model = None
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.mae = 0
        self.r2 = 0
        self.rmse = 0
        self.is_trained = False
        
    def clean_data(self, df):
        df_clean = df.copy()
        
        price_columns = ['Launched Price (Pakistan)', 'Launched Price (India)', 
                       'Launched Price (China)', 'Launched Price (USA)', 
                       'Launched Price (Dubai)']
        
        for col in price_columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str)
                df_clean[col] = df_clean[col].str.replace('PKR ', '', regex=False)
                df_clean[col] = df_clean[col].str.replace('INR ', '', regex=False)
                df_clean[col] = df_clean[col].str.replace('CNY ', '', regex=False)
                df_clean[col] = df_clean[col].str.replace('USD ', '', regex=False)
                df_clean[col] = df_clean[col].str.replace('AED ', '', regex=False)
                df_clean[col] = df_clean[col].str.replace(',', '', regex=False)
                df_clean[col] = df_clean[col].str.replace('"', '', regex=False)
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        if 'Battery Capacity' in df_clean.columns:
            def extract_battery(x):
                if pd.isna(x):
                    return np.nan
                x = str(x)
                x = x.replace('mAh', '').replace(',', '').strip()
                try:
                    return float(x)
                except:
                    return np.nan
            
            df_clean['Battery_Num'] = df_clean['Battery Capacity'].apply(extract_battery)
        
        if 'Screen Size' in df_clean.columns:
            def extract_screen_size(x):
                if pd.isna(x):
                    return np.nan
                x = str(x)
                x = x.replace(' inches', '')
                if '(' in x:
                    main_part = x.split('(')[0].strip()
                    try:
                        return float(main_part)
                    except:
                        return np.nan
                try:
                    return float(x)
                except:
                    return np.nan
            
            df_clean['Screen_Size_Num'] = df_clean['Screen Size'].apply(extract_screen_size)
        
        if 'RAM' in df_clean.columns:
            def extract_ram(x):
                if pd.isna(x):
                    return np.nan
                x = str(x)
                if 'GB' in x:
                    x = x.replace('GB', '').strip()
                try:
                    return float(x)
                except:
                    return np.nan
            
            df_clean['RAM_Num'] = df_clean['RAM'].apply(extract_ram)
        
        if 'Model Name' in df_clean.columns:
            def extract_storage(x):
                if pd.isna(x):
                    return np.nan
                x = str(x).upper()
                
                patterns = [
                    r'(\d+)(GB|TB)',
                    r'(\d+)\s*(GB|TB)',
                    r'/(\d+)(GB|TB)'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, x)
                    if match:
                        num = float(match.group(1))
                        unit = match.group(2)
                        if unit == 'TB':
                            return num * 1024
                        return num
                return np.nan
            
            df_clean['Storage_Num'] = df_clean['Model Name'].apply(extract_storage)
        
        if 'Front Camera' in df_clean.columns:
            def extract_front_camera(x):
                if pd.isna(x):
                    return np.nan
                x = str(x)
                match = re.search(r'(\d+)MP', x)
                if match:
                    return float(match.group(1))
                
                match = re.search(r'(\d+\.?\d*)\s*MP', x)
                if match:
                    return float(match.group(1))
                
                return np.nan
            
            df_clean['Front_Camera_Num'] = df_clean['Front Camera'].apply(extract_front_camera)
        
        if 'Back Camera' in df_clean.columns:
            def extract_back_camera(x):
                if pd.isna(x):
                    return np.nan
                x = str(x)
                match = re.search(r'(\d+)MP', x)
                if match:
                    return float(match.group(1))
                
                matches = re.findall(r'(\d+\.?\d*)\s*MP', x)
                if matches:
                    return float(matches[0])
                
                return np.nan
            
            df_clean['Back_Camera_Num'] = df_clean['Back Camera'].apply(extract_back_camera)
        
        if 'Mobile Weight' in df_clean.columns:
            def extract_weight(x):
                if pd.isna(x):
                    return np.nan
                x = str(x)
                x = x.replace('g', '').strip()
                try:
                    return float(x)
                except:
                    return np.nan
            
            df_clean['Weight_Num'] = df_clean['Mobile Weight'].apply(extract_weight)
        
        if 'Processor' in df_clean.columns:
            df_clean['Processor_Type'] = df_clean['Processor'].astype(str)
        
        return df_clean
    
    def load_data(self):
        csv_filename = 'Mobiles_Dataset__2025_.csv'
        encodings = ['latin-1', 'cp1252', 'iso-8859-1', 'utf-8', 'utf-16']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(csv_filename, encoding=encoding, on_bad_lines='skip')
                break
            except:
                continue
        else:
            try:
                df = pd.read_csv(csv_filename, encoding='latin-1', engine='python', on_bad_lines='skip')
            except:
                df = pd.read_csv(csv_filename, encoding='latin-1', sep=',', on_bad_lines='skip')
        
        return self.clean_data(df)
    
    def train_model(self):
        try:
            df = self.load_data()
            
            if 'Launched Price (Pakistan)' not in df.columns:
                return False, "Price column not found", None
            
            features = [
                'Company Name', 'RAM_Num', 'Launched Year', 
                'Battery_Num', 'Screen_Size_Num', 'Storage_Num',
                'Front_Camera_Num', 'Back_Camera_Num', 'Weight_Num',
                'Processor_Type'
            ]
            
            for feature in features:
                if feature not in df.columns:
                    df[feature] = 0 if 'Num' in feature else 'Unknown'
            
            df = df.dropna(subset=['Launched Price (Pakistan)'] + features)
            
            if len(df) < 100:
                return False, "Not enough data for training", None
            
            X = df[features].copy()
            y = df['Launched Price (Pakistan)']
            
            self.label_encoders = {}
            categorical_cols = ['Company Name', 'Processor_Type']
            
            for col in categorical_cols:
                if col in X.columns:
                    le = LabelEncoder()
                    X[col] = le.fit_transform(X[col].astype(str))
                    self.label_encoders[col] = le
            
            numerical_cols = ['RAM_Num', 'Launched Year', 'Battery_Num', 
                            'Screen_Size_Num', 'Storage_Num', 'Front_Camera_Num',
                            'Back_Camera_Num', 'Weight_Num']
            
            for col in numerical_cols:
                if col in X.columns:
                    X[col] = X[col].fillna(X[col].median())
            
            X[numerical_cols] = self.scaler.fit_transform(X[numerical_cols])
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            self.model = RandomForestRegressor(
                n_estimators=200, 
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            
            self.model.fit(X_train, y_train)
            
            y_pred = self.model.predict(X_test)
            self.mae = mean_absolute_error(y_test, y_pred)
            self.r2 = r2_score(y_test, y_pred)
            self.rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            
            self.is_trained = True
            
            self.save_model()
            
            feature_importance = pd.DataFrame({
                'feature': features,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            return True, "Model trained successfully", feature_importance
            
        except Exception as e:
            return False, f"Error in training: {str(e)}", None
    
    def predict_price(self, company, model_name, launch_year, ram, storage, 
                     battery, screen_size, front_camera, back_camera, 
                     processor, weight=None):
        if not self.is_trained:
            return None, "Model not trained"
        
        try:
            storage_num = self.extract_storage_from_model(model_name, storage)
            
            input_data = pd.DataFrame({
                'Company Name': [company],
                'RAM_Num': [ram],
                'Launched Year': [launch_year],
                'Battery_Num': [battery],
                'Screen_Size_Num': [screen_size],
                'Storage_Num': [storage_num],
                'Front_Camera_Num': [front_camera],
                'Back_Camera_Num': [back_camera],
                'Weight_Num': [weight if weight else 180],
                'Processor_Type': [processor]
            })
            
            categorical_cols = ['Company Name', 'Processor_Type']
            
            for col in categorical_cols:
                if col in self.label_encoders:
                    try:
                        input_data[col] = self.label_encoders[col].transform(input_data[col].astype(str))
                    except:
                        input_data[col] = 0
            
            numerical_cols = ['RAM_Num', 'Launched Year', 'Battery_Num', 
                            'Screen_Size_Num', 'Storage_Num', 'Front_Camera_Num',
                            'Back_Camera_Num', 'Weight_Num']
            
            for col in numerical_cols:
                if col in input_data.columns:
                    input_data[col] = input_data[col].fillna(input_data[col].median())
            
            input_data[numerical_cols] = self.scaler.transform(input_data[numerical_cols])
            
            prediction = self.model.predict(input_data)[0]
            
            confidence = 0.85
            
            lower_bound = prediction * (1 - 0.15)
            upper_bound = prediction * (1 + 0.15)
            
            return {
                'predicted_price': max(0, prediction),
                'confidence': confidence,
                'price_range': (max(0, lower_bound), upper_bound),
                'storage_used': storage_num
            }, "Success"
            
        except Exception as e:
            return None, f"Prediction error: {str(e)}"
    
    def extract_storage_from_model(self, model_name, storage_input):
        try:
            if storage_input:
                if 'TB' in str(storage_input).upper():
                    return float(str(storage_input).upper().replace('TB', '').strip()) * 1024
                elif 'GB' in str(storage_input).upper():
                    return float(str(storage_input).upper().replace('GB', '').strip())
                else:
                    return float(storage_input)
            
            if not model_name:
                return 128
            
            model_str = str(model_name).upper()
            
            patterns = [
                r'(\d+)(GB|TB)',
                r'(\d+)\s*(GB|TB)',
                r'/(\d+)(GB|TB)',
                r'(\d+)GB',
                r'(\d+)TB'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, model_str)
                if match:
                    num = float(match.group(1))
                    unit = match.group(2) if len(match.groups()) > 1 else 'GB'
                    if unit == 'TB':
                        return num * 1024
                    return num
            
            return 128
            
        except:
            return 128
    
    def save_model(self):
        try:
            with open('mobile_price_model.pkl', 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'label_encoders': self.label_encoders,
                    'scaler': self.scaler,
                    'mae': self.mae,
                    'r2': self.r2,
                    'rmse': self.rmse
                }, f)
        except:
            pass
    
    def load_saved_model(self):
        try:
            if os.path.exists('mobile_price_model.pkl'):
                with open('mobile_price_model.pkl', 'rb') as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.label_encoders = data['label_encoders']
                    self.scaler = data['scaler']
                    self.mae = data['mae']
                    self.r2 = data['r2']
                    self.rmse = data['rmse']
                    self.is_trained = True
                    return True
            return False
        except:
            return False
    
    def get_model_info(self):
        if self.is_trained:
            return {
                'mae': self.mae,
                'r2': self.r2,
                'rmse': self.rmse,
                'is_trained': True
            }
        return {
            'mae': 0,
            'r2': 0,
            'rmse': 0,
            'is_trained': False
        }