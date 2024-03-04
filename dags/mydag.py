from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from bs4 import BeautifulSoup
import requests
import pandas as pd
import os

default_args = {
    'owner': 'nduti',
    'depends_on_past': False,
    'start_date': datetime(2023, 11, 11),
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

dag = DAG(
    'scrape_n_save_to_csv',
    default_args=default_args,
    description='Scraping_with_airflow',
    schedule_interval=timedelta(days=1),
)

def scrape_quotes():
    url = 'http://quotes.toscrape.com'
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        quotes = [quote.text.strip() for quote in soup.select('span.text')]
        return quotes
    else:
        print(f"Failed to fetch quotes. Status code: {response.status_code}")
        return []
    
def save_to_csv(quotes, **kwargs):
    if not quotes:
        print("No quotes to save.")
        return
    
    # Get the directory of the current DAG file
    current_dag_directory = os.path.dirname(os.path.abspath(__file__))
    
    # Specify the directory where you want to save the CSV file
    output_directory = os.path.join(current_dag_directory, 'output')
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)
    
    # Create a Pandas DataFrame
    df = pd.DataFrame({'Quote': quotes})
    
    # Save to CSV file in the specified output directory
    csv_path = os.path.join(output_directory, 'quotes.csv')
    df.to_csv(csv_path, index=False)
    
    print(f"Quotes saved to {csv_path}.")

 
task_scrape_quotes = PythonOperator(
    task_id='scrape_quotes',
    python_callable=scrape_quotes,
    dag=dag,
)

task_save_to_csv = PythonOperator(
    task_id='save_to_csv',
    python_callable=save_to_csv,
    op_args=[task_scrape_quotes.output],  # Pass the output of the first task as an argument
    provide_context=True,  # This allows passing parameters between tasks
    dag=dag,
)

# Set up task dependencies
# Correctly sets the downstream dependency
task_scrape_quotes >> task_save_to_csv  
