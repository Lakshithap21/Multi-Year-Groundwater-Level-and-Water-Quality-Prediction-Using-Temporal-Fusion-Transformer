from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import joblib
import json
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import google.generativeai as genai
app = Flask(__name__)

EMAIL_LOGS_FILE = 'email_logs.json'

def append_email_log(log_entry):
    logs = []
    if os.path.exists(EMAIL_LOGS_FILE):
        try:
            with open(EMAIL_LOGS_FILE, 'r') as f:
                logs = json.load(f)
        except Exception:
            pass
    logs.insert(0, log_entry)
    logs = logs[:50]
    try:
        with open(EMAIL_LOGS_FILE, 'w') as f:
            json.dump(logs, f, indent=4)
    except Exception:
        pass

def send_forecast_email_async(state, district, forecast_data, recipient="lucky.vel21@gmail.com"):
    sender_email = "lucky.vel21@gmail.com"
    app_password = "symm ctac ufkx ayzg"
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        'timestamp': timestamp,
        'recipient': recipient,
        'state': state,
        'district': district,
        'status': 'Pending',
        'error': None
    }
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = f"Groundwater Forecast Alert: {district}, {state}"
        
        # Simple HTML report
        forecast_list = forecast_data.get('forecast', [])
        forecast_details = ""
        for f in forecast_list:
            forecast_details += f"<li><b>{f.get('year')}</b>: Water Level {f.get('wl')} mbgl | pH {f.get('ph')} | Nitrate {f.get('no3')} mg/L</li>"
            
        html_body = f"""
        <html>
            <body style="font-family: sans-serif; color: #333;">
                <h2 style="color: #2563eb;">Groundwater Forecast Report</h2>
                <p>Location: <b>{district}, {state}</b></p>
                <p>Generated At: {timestamp}</p>
                <hr style="border: 1px solid #eee;">
                <h3>Forecast Data</h3>
                <ul>
                    {forecast_details}
                </ul>
                <hr style="border: 1px solid #eee;">
                <p style="font-size: 13px; color: #666;">Please check the web dashboard for full visual charts and dynamic alerts.</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()
        
        log_entry['status'] = 'Success'
    except Exception as e:
        log_entry['status'] = 'Failed'
        log_entry['error'] = str(e)
        
    append_email_log(log_entry)


# Global variables
wl_complete = None
wq_complete = None
wl_model = None
wq_model = None
wl_config = None
wq_config = None
device = None

class ImprovedTFT(nn.Module):
    def __init__(self, input_size, hidden_size=128, num_layers=3, num_heads=8, dropout=0.3, output_size=1):
        super().__init__()
        
        self.input_bn = nn.BatchNorm1d(input_size)
        self.input_projection = nn.Linear(input_size, hidden_size)
        
        self.lstm = nn.LSTM(hidden_size, hidden_size, num_layers, 
                           batch_first=True, dropout=dropout)
        
        self.attn = nn.MultiheadAttention(hidden_size, num_heads, 
                                         dropout=dropout, batch_first=True)
        
        self.attn_norm = nn.LayerNorm(hidden_size)
        
        self.ffn = nn.Sequential(
            nn.Linear(hidden_size, hidden_size * 4),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size * 4, hidden_size),
            nn.Dropout(dropout)
        )
        self.ffn_norm = nn.LayerNorm(hidden_size)
        
        self.output_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, output_size)
        )
        
    def forward(self, x):
        x_norm = self.input_bn(x)
        x_proj = torch.relu(self.input_projection(x_norm))
        x_seq = x_proj.unsqueeze(1)
        
        lstm_out, _ = self.lstm(x_seq)
        
        attn_out, _ = self.attn(lstm_out, lstm_out, lstm_out)
        attn_out = self.attn_norm(lstm_out + attn_out)
        
        ffn_out = self.ffn(attn_out)
        output = self.ffn_norm(attn_out + ffn_out)
        
        output = output.squeeze(1)
        pred = self.output_head(output)
        
        return pred

def load_data_and_models():
    """Load all data and models once at startup"""
    global wl_complete, wq_complete, wl_model, wq_model, wl_config, wq_config, device
    
    print("="*80)
    print("LOADING DATA AND MODELS...")
    print("="*80)
    
    # Load complete data (2019-2030)
    print("\n1. Loading complete datasets...")
    wl_complete = pd.read_csv('water_level_predictions_2019_2030.csv')
    wq_complete = pd.read_csv('water_quality_predictions_2019_2030.csv')
    
    print(f"✓ Water Level data: {len(wl_complete)} records ({wl_complete['Year'].min()}-{wl_complete['Year'].max()})")
    print(f"✓ Water Quality data: {len(wq_complete)} records ({wq_complete['Year'].min()}-{wq_complete['Year'].max()})")
    
    # Get common locations
    wl_locations = set(zip(wl_complete['STATE'], wl_complete['DISTRICT']))
    wq_locations = set(zip(wq_complete['STATE'], wq_complete['DISTRICT']))
    common_locations = wl_locations & wq_locations
    
    print(f"✓ Common locations: {len(common_locations)}")
    
    # Filter to common locations only
    wl_complete = wl_complete[wl_complete.apply(lambda x: (x['STATE'], x['DISTRICT']) in common_locations, axis=1)]
    wq_complete = wq_complete[wq_complete.apply(lambda x: (x['STATE'], x['DISTRICT']) in common_locations, axis=1)]
    
    # Load models
    print("\n2. Loading models...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"✓ Device: {device}")
    
    # Load Water Level model
    wl_config = joblib.load('tft_water_level_config.pkl')
    wl_model = ImprovedTFT(
        input_size=wl_config['model_config']['input_size'],
        hidden_size=wl_config['model_config']['hidden_size'],
        num_layers=wl_config['model_config']['num_layers'],
        num_heads=wl_config['model_config']['num_heads'],
        dropout=wl_config['model_config']['dropout'],
        output_size=1
    ).to(device)
    wl_model.load_state_dict(torch.load('tft_water_level.pth', map_location=device))
    wl_model.eval()
    print("✓ Water Level model loaded")
    
    # Load Water Quality model
    wq_config = joblib.load('tft_water_quality_config.pkl')
    wq_model = ImprovedTFT(
        input_size=wq_config['model_config']['input_size'],
        hidden_size=wq_config['model_config']['hidden_size'],
        num_layers=wq_config['model_config']['num_layers'],
        num_heads=wq_config['model_config']['num_heads'],
        dropout=wq_config['model_config']['dropout'],
        output_size=2  # pH and NO3
    ).to(device)
    wq_model.load_state_dict(torch.load('tft_water_quality.pth', map_location=device))
    wq_model.eval()
    print("✓ Water Quality model loaded")
    
    print("\n" + "="*80)
    print("STARTUP COMPLETE!")
    print("="*80)

def check_alerts(data):
    """Check for concerning trends and values"""
    alerts = []
    
    if len(data) < 2:
        return alerts
    
    # Get latest values
    latest = data[-1]
    
    # Critical thresholds
    WL_CRITICAL = 20  # Very deep water table
    WL_WARNING = 15   # Deep water table
    pH_LOW = 6.5
    pH_HIGH = 8.5
    NO3_WARNING = 45  # WHO guideline
    NO3_CRITICAL = 50  # Severe contamination
    
    # Check Water Level
    if latest['wl'] > WL_CRITICAL:
        alerts.append({
            'type': 'critical',
            'category': 'Water Level',
            'message': f'Critical water level: {latest["wl"]} mbgl (very deep water table). Immediate action required!'
        })
    elif latest['wl'] > WL_WARNING:
        alerts.append({
            'type': 'warning',
            'category': 'Water Level',
            'message': f'Warning: Water level at {latest["wl"]} mbgl (deep water table). Monitor closely.'
        })
    
    # Check water level trend (if increasing = declining water table)
    if len(data) >= 3:
        wl_values = [d['wl'] for d in data]
        increasing_count = sum(1 for i in range(1, len(wl_values)) if wl_values[i] > wl_values[i-1])
        
        if increasing_count >= 2:
            alerts.append({
                'type': 'warning',
                'category': 'Water Level Trend',
                'message': f'Declining water table trend detected over {increasing_count} years. Water level increasing from {wl_values[0]} to {wl_values[-1]} mbgl.'
            })
    
    # Check pH
    if latest['ph'] < pH_LOW:
        alerts.append({
            'type': 'warning',
            'category': 'pH Level',
            'message': f'pH below safe limit: {latest["ph"]} (safe range: 6.5-8.5). Water is too acidic.'
        })
    elif latest['ph'] > pH_HIGH:
        alerts.append({
            'type': 'warning',
            'category': 'pH Level',
            'message': f'pH above safe limit: {latest["ph"]} (safe range: 6.5-8.5). Water is too alkaline.'
        })
    
    # Check NO3
    if latest['no3'] > NO3_CRITICAL:
        alerts.append({
            'type': 'critical',
            'category': 'Nitrate (NO3)',
            'message': f'Critical nitrate contamination: {latest["no3"]} mg/L (WHO limit: 45 mg/L). Unsafe for consumption!'
        })
    elif latest['no3'] > NO3_WARNING:
        alerts.append({
            'type': 'warning',
            'category': 'Nitrate (NO3)',
            'message': f'Elevated nitrate level: {latest["no3"]} mg/L (WHO limit: 45 mg/L). Approaching unsafe levels.'
        })
    
    # Check NO3 trend
    if len(data) >= 3:
        no3_values = [d['no3'] for d in data]
        increasing_count = sum(1 for i in range(1, len(no3_values)) if no3_values[i] > no3_values[i-1])
        
        if increasing_count >= 2 and latest['no3'] > NO3_WARNING:
            alerts.append({
                'type': 'warning',
                'category': 'Nitrate Trend',
                'message': f'Rising nitrate trend detected over {increasing_count} years. Level increased from {no3_values[0]} to {no3_values[-1]} mg/L.'
            })
    
    # Overall water quality alert
    if len(alerts) >= 3:
        alerts.append({
            'type': 'critical',
            'category': 'Overall Water Quality',
            'message': 'Multiple water quality parameters showing concerning values. Comprehensive water treatment recommended!'
        })
    
    return alerts

def get_location_data(state, district, end_year):
    """Get data for a location up to specified year"""
    wl_data = wl_complete[
        (wl_complete['STATE'] == state) & 
        (wl_complete['DISTRICT'] == district) &
        (wl_complete['Year'] <= end_year)
    ].sort_values('Year')
    
    wq_data = wq_complete[
        (wq_complete['STATE'] == state) & 
        (wq_complete['DISTRICT'] == district) &
        (wq_complete['Year'] <= end_year)
    ].sort_values('Year')
    
    if len(wl_data) == 0 or len(wq_data) == 0:
        return None, "Location not found in database"
    
    # Combine data
    combined = []
    for year in range(wl_data['Year'].min(), end_year + 1):
        wl_year = wl_data[wl_data['Year'] == year]
        wq_year = wq_data[wq_data['Year'] == year]
        
        if len(wl_year) > 0 and len(wq_year) > 0:
            combined.append({
                'year': int(year),
                'wl': round(float(wl_year['WL(mbgl)'].values[0]), 2),
                'ph': round(float(wq_year['pH'].values[0]), 2),
                'no3': round(float(wq_year['NO3'].values[0]), 2),
                'is_predicted': year > 2023
            })
    
    return combined, None

def forecast_location(state, district, num_years):
    """Get forecast data for a location"""
    
    # Calculate target end year
    current_year = 2023
    end_year = min(current_year + num_years, 2030)
    
    # Get data from CSV (which already has predictions till 2030)
    data, error = get_location_data(state, district, end_year)
    
    if error:
        return None, error
    
    if len(data) == 0:
        return None, "No data available for this location"
    
    # Split into historical and forecast
    historical = [d for d in data if d['year'] <= 2023]
    forecast = [d for d in data if d['year'] > 2023]
    
    # Check for alerts based on forecast data
    alerts = check_alerts(forecast) if len(forecast) > 0 else []
    
    # Prepare historical data
    historical_data = {
        'years': [d['year'] for d in historical],
        'wl': [d['wl'] for d in historical],
        'ph': [d['ph'] for d in historical],
        'no3': [d['no3'] for d in historical]
    }
    
    # Prepare forecast data (remove is_predicted flag for response)
    forecast_data = [
        {
            'year': d['year'],
            'wl': d['wl'],
            'ph': d['ph'],
            'no3': d['no3']
        }
        for d in forecast
    ]
    
    return {
        'historical': historical_data,
        'forecast': forecast_data,
        'alerts': alerts
    }, None

# ============================================================================
# ROUTES
# ============================================================================
@app.route('/')
def index():
    """Home page with state selection"""
    states = sorted(wl_complete['STATE'].unique())
    return render_template('index.html', states=states)

@app.route('/get_districts/<state>')
def get_districts(state):
    """Get districts for a selected state"""
    # Get districts that exist in both datasets for this state
    wl_districts = set(wl_complete[wl_complete['STATE'] == state]['DISTRICT'].unique())
    wq_districts = set(wq_complete[wq_complete['STATE'] == state]['DISTRICT'].unique())
    common_districts = sorted(wl_districts & wq_districts)
    
    return jsonify(common_districts)

@app.route('/forecast', methods=['POST'])
def forecast():
    """Generate forecast for selected location"""
    data = request.json
    state = data.get('state')
    district = data.get('district')
    num_years = int(data.get('num_years', 1))
    
    # Validate inputs
    if not state or not district:
        return jsonify({'error': 'State and district are required'}), 400
    
    if num_years < 1 or num_years > 7:
        return jsonify({'error': 'Number of years must be between 1 and 7'}), 400
    
    # Get forecast
    result, error = forecast_location(state, district, num_years)
    
    if error:
        return jsonify({'error': error}), 400
        
    # Trigger email asynchronously on successful generation
    threading.Thread(target=send_forecast_email_async, args=(state, district, result)).start()
    
    return jsonify(result)

@app.route('/email_logs')
def get_email_logs():
    if os.path.exists(EMAIL_LOGS_FILE):
        try:
            with open(EMAIL_LOGS_FILE, 'r') as f:
                logs = json.load(f)
                return jsonify(logs)
        except Exception:
            return jsonify([])
    return jsonify([])

@app.route('/map_data')
def map_data():
    """Get forecast map data for a specific year"""
    year = request.args.get('year', 2024, type=int)
    
    try:
        # Filter data for the year
        wl_year = wl_complete[wl_complete['Year'] == year]
        wq_year = wq_complete[wq_complete['Year'] == year]
        
        # Merge them on STATE, DISTRICT
        merged = pd.merge(wl_year, wq_year, on=['STATE', 'DISTRICT', 'Year'], how='inner')
        
        locations = []
        for _, row in merged.iterrows():
            try:
                lat = row.get('LATITUDE')
                lon = row.get('LONGITUDE')
                if pd.isna(lat) or pd.isna(lon):
                    continue
                locations.append({
                    'state': row['STATE'],
                    'district': row['DISTRICT'],
                    'lat': float(lat),
                    'lon': float(lon),
                    'wl': round(float(row['WL(mbgl)']), 2),
                    'ph': round(float(row['pH']), 2),
                    'no3': round(float(row['NO3']), 2)
                })
            except Exception:
                continue
                
        return jsonify(locations)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats')
def stats():
    """Get overall statistics"""
    stats = {
        'total_states': int(wl_complete['STATE'].nunique()),
        'total_districts': int(wl_complete.groupby(['STATE', 'DISTRICT']).ngroups),
        'years_available': f"{int(wl_complete['Year'].min())}-{int(wl_complete['Year'].max())}",
        'historical_years': '2019-2023',
        'forecast_years': '2024-2030'
    }
    
    return jsonify(stats)

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chatbot interactions"""
    try:
        data = request.json
        user_message = data.get('message', '')
        context_data = data.get('context', {})
        
        api_key = "AIzaSyBSLaSKwO4KtcVzNfrl1CxKaJQijwDxTB0" or os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return jsonify({'error': 'GEMINI_API_KEY environment variable is not set.'}), 500
            
        genai.configure(api_key=api_key)
        
        # Prepare context summary
        context_summary = "User is looking at the GroundWater Forecasting System."
        if context_data:
            state = context_data.get('state', 'Unknown')
            district = context_data.get('district', 'Unknown')
            forecast = context_data.get('latestForecast', {})
            alerts = context_data.get('alerts', [])
            
            context_summary = f"User is viewing data for {district}, {state}. "
            if forecast:
                context_summary += f"The {forecast.get('year')} forecast predicts: Water Level {forecast.get('wl')}m, pH {forecast.get('ph')}, Nitrate {forecast.get('no3')} mg/L. "
            if alerts:
                alert_msgs = [a.get('message') for a in alerts]
                context_summary += f"Active alerts for this location: {'; '.join(alert_msgs)}."
                
        # Initialize model
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        # Prompt construction
        prompt = f"""You are an expert groundwater scientist and AI assistant for India's Groundwater Forecasting System.

        Current context:
        {context_summary}

        Rules:
        - Answer directly and confidently. Never ask the user clarifying questions.
        - If forecast data is available, always mention specific numbers (water level, pH, nitrate).
        - If the user asks about a topic outside groundwater (like a city in general), briefly answer from your general knowledge, then relate it back to groundwater if possible.
        - Keep answers under 100 words. Use plain text, no markdown bullet points.
        - If no location is selected yet, answer from general knowledge about Indian groundwater.

        User Question: {user_message}
        """
        
        response = model.generate_content(prompt)
        
        return jsonify({'response': response.text})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Load data and models at startup
    load_data_and_models()
    
    # Run app
    app.run(debug=True, host='0.0.0.0', port=5000)