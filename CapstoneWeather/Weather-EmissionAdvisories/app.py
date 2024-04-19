from flask import Flask, render_template, request
from forms import ICAOForm  # Import the form definition
import requests
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Set a secret key for security purposes

# API Key and URL setup

api_key = 'a741a79a6d7246f8a3e0364dc8'
taf_base_url = 'https://api.checkwx.com/taf/'
sigmet_base_url = 'https://api.checkwx.com/sigmet/'

def fetch_data(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data: {response.status_code} {response.text}")
        return None

def fetch_taf_data(icao):
    url = f"{taf_base_url}{icao}/decoded"
    headers = {'X-API-Key': api_key}
    return fetch_data(url, headers)

def fetch_sigmet_data(icao):
    url = f"{sigmet_base_url}{icao}/decoded"
    headers = {'X-API-Key': api_key}
    return fetch_data(url, headers)

def analyze_taf_fuel_impact(taf_data):
    impacts = []
    if taf_data and 'data' in taf_data:
        for report in taf_data['data']:
            icao = report.get('icao', 'Unknown')
            for forecast in report.get('forecast', []):
                period = f"From {forecast['timestamp']['from']} to {forecast['timestamp']['to']}"
                conditions_described = ', '.join(c['text'] for c in forecast.get('conditions', []))
                wind_speed = forecast.get('wind', {}).get('speed_kts', 0)
                impact_desc = f"{conditions_described}. High winds might increase fuel if wind speed > 20 kts ({wind_speed} kts)."

                # Include visibility and significant weather conditions like snow, ice, or fog
                if 'visibility' in forecast and forecast['visibility']['miles_float'] < 1:
                    impact_desc += " Low visibility could lead to delays and increased fuel usage."
                if any('snow' in c['text'].lower() or 'ice' in c['text'].lower() or 'fog' in c['text'].lower() for c in forecast.get('conditions', [])):
                    impact_desc += " Conditions like snow, ice, or fog may require de-icing and can cause delays, increasing fuel usage."

                # Check for rain and its operational implications
                if any('rain' in c['text'].lower() for c in forecast.get('conditions', [])):
                    impact_desc += " Rain may lead to increased braking distances and reduced runway friction, potentially affecting fuel usage due to longer taxi and rollout times."

                # Check for thunderstorms and turbulence for additional flight considerations
                if any('thunderstorm' in c['text'].lower() for c in forecast.get('conditions', [])):
                    impact_desc += " Thunderstorms may necessitate significant rerouting."
                if any('turbulence' in c['text'].lower() for c in forecast.get('conditions', [])):
                    impact_desc += " Turbulence could lead to operational adjustments and potential fuel inefficiencies."

                # Append the formatted string to impacts list
                impacts.append({
                    'icao': icao,
                    'period': period,
                    'description': impact_desc
                })
    return impacts

def analyze_sigmet_fuel_impact(sigmet_data):
    impacts = []
    if sigmet_data and 'data' in sigmet_data:
        for entry in sigmet_data['data']:
            icao = entry.get('icao', 'Unknown')
            hazard_type = entry.get('hazard', {}).get('type', {}).get('text', 'Unknown')
            description = f"Hazard type: {hazard_type}. "
            if 'Thunderstorm' in hazard_type:
                description += "Potential rerouting increases fuel."
            elif 'Volcanic ash' in hazard_type:
                description += "Avoidance increases fuel usage."
            # ... more conditions if necessary

            impacts.append({
                'icao': icao,
                'description': description
            })
        if not impacts:
            impacts.append({
            'icao': 'N/A',
            'period': 'N/A',
            'description': 'No significant SIGMET advisories affecting fuel emissions.'
        })
    return impacts

# Usage
icao_code = 'KATL'
taf_data = fetch_taf_data(icao_code)
sigmet_data = fetch_sigmet_data(icao_code)
taf_impacts = analyze_taf_fuel_impact(taf_data)
sigmet_impacts = analyze_sigmet_fuel_impact(sigmet_data)

# Displaying impacts
print('TAF Fuel Impacts:')
for impact in taf_impacts:
    print(f"{impact['icao']} | {impact['period']} | {impact['description']}")

print('SIGMET Fuel Impacts:')
for impact in sigmet_impacts:
    print(f"{impact['icao']} | {impact['description']}")

@app.route('/', methods=['GET', 'POST'])
def home():
    form = ICAOForm()  # Create an instance of the form
    if form.validate_on_submit():  # Check if the form is submitted and valid
        icao_code = form.icao_code.data
        taf_data = fetch_taf_data(icao_code)
        sigmet_data = fetch_sigmet_data(icao_code)
        taf_impacts = analyze_taf_fuel_impact(taf_data)
        sigmet_impacts = analyze_sigmet_fuel_impact(sigmet_data)
        return render_template('results.html', icao_code=icao_code, taf_impacts=taf_impacts, sigmet_impacts=sigmet_impacts, form=form)
    return render_template('index.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)
