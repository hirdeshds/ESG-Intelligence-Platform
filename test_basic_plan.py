"""
Test script for BASIC PLAN API endpoint
Demonstrates how to use the /basic/predict endpoint
"""

import requests
import pandas as pd
import io

# API URL (adjust if running on different host/port)
API_URL = "http://localhost:8000/basic/predict"

def test_basic_plan_endpoint():
    """
    Test the BASIC PLAN endpoint with sample data
    """
    
    # Create sample ESG data with environmental metrics
    sample_data = {
        'Firm_ID': ['MFG0103'],
        'Year': [2023],
        'Industry_Type': ['Pharmaceuticals'],
        'E_Score': [71.37],
        'S_Score': [62.37],
        'G_Score': [60.5],
        'ROA': [10.44],
        'ROE': [13.28],
        'Net_Profit_Margin': [5.47],
        'Revenue': [207.77],
        'Operating_Cost': [207.77],
        'Board_Independence': [81.08],
        'Innovation_Spending': [3.97],
        'carbon_emissions': [150.5],  # Optional detailed metrics
        'energy_consumption': [300.2],
        'renewable_energy_percent': [35.0],
        'water_usage': [450.0],
        'waste_generated': [120.0]
    }
    
    df = pd.DataFrame(sample_data)
    
    # Convert to CSV format
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()
    
    # Prepare file for upload
    files = {
        'file': ('test_data.csv', io.BytesIO(csv_data.encode()), 'text/csv')
    }
    
    print("Testing BASIC PLAN API Endpoint")
    print("=" * 60)
    print(f"Sending request to: {API_URL}")
    print(f"Sample data columns: {list(df.columns)}")
    print()
    
    try:
        response = requests.post(API_URL, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS - API Response:")
            print("-" * 60)
            
            for key, value in result.items():
                if key == 'summary':
                    print(f"\n📊 Summary:")
                    print(f"   {value}")
                else:
                    print(f"  {key:.<40} {value}")
            
            print("-" * 60)
            return result
        else:
            print(f"❌ Error: Status Code {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to API")
        print("Make sure the API is running: uvicorn api.main:app --reload")
        return None
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None


def test_with_minimal_data():
    """
    Test with minimal data (only core ESG scores)
    """
    sample_data = {
        'Firm_ID': ['MFG0436'],
        'Year': [2021],
        'E_Score': [85.2],
        'S_Score': [77.27],
        'G_Score': [71.71],
        'ROA': [7.41],
        'ROE': [10.94],
        'Net_Profit_Margin': [5.93],
        'Innovation_Spending': [5.51]
    }
    
    df = pd.DataFrame(sample_data)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()
    
    files = {
        'file': ('minimal_data.csv', io.BytesIO(csv_data.encode()), 'text/csv')
    }
    
    print("\n\nTesting BASIC PLAN with Minimal Data")
    print("=" * 60)
    
    try:
        response = requests.post(API_URL, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS - API Response:")
            print("-" * 60)
            
            for key, value in result.items():
                if key != 'summary':
                    print(f"  {key:.<40} {value}")
            
            print("-" * 60)
            return result
        else:
            print(f"❌ Error: Status Code {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")


def test_premium_plan_endpoint():
    """
    Test script for PREMIUM PLAN API endpoint
    """
    API_URL_PREMIUM = "http://localhost:8000/premium/predict"
    sample_data = {
        'Firm_ID': ['PREM001'],
        'Year': [2023],
        'carbon_emissions': [900],
        'Revenue': [12000],
        'csr_spending': [800],
        'ROA': [6],
        'Board_Independence': [0.6],
        'renewable_energy_percent': [45]
    }
    df = pd.DataFrame(sample_data)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()
    files = {'file': ('premium.csv', io.BytesIO(csv_data.encode()), 'text/csv')}

    print("\n\nTesting PREMIUM PLAN API Endpoint")
    print("=" * 60)
    try:
        response = requests.post(API_URL_PREMIUM, files=files)
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS - PREM API Response:")
            print(result)
            return result
        else:
            print(f"❌ Error: Status Code {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None


if __name__ == "__main__":
    print("\n" + "="*60)
    print("BASIC PLAN API - Test Suite")
    print("="*60 + "\n")
    
    # Test 1: Full detailed data
    result1 = test_basic_plan_endpoint()
    
    # Test 2: Minimal data
    result2 = test_with_minimal_data()
    
    # Test 3: Premium plan
    result3 = test_premium_plan_endpoint()
    
    print("\n" + "="*60)
    print("Tests Complete!")
    print("="*60)
