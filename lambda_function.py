import json
import urllib3
import os

def lambda_handler(event, context):
    try:        
        city = event['city']
        url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid=ccaf7a577ae596e079e9a0ed04af6b10&units=metric'
        
    
        http = urllib3.PoolManager()
        response = http.request('GET', url)
        data = json.loads(response.data.decode('utf-8'))        
        
        if 'main' not in data or 'temp' not in data['main']:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Temperature data not found'})
            }

        current_temp = data['main']['temp']
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'city': city,
                'current_temperature': current_temp
            }),
            'headers': {'Content-Type': 'application/json'}
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
