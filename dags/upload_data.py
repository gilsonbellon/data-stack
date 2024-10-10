import os 
from datetime import datetime, timedelta
from airflow import DAG
from airflow.decorators import task
from airflow.operators.empty import EmptyOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook


dag_path = os.path.join(os.path.dirname(__file__))
dag_name = os.path.join(os.path.basename(__file__)).replace('.py', '')
# originations_directory = f'/{dag_path}/../originations'
originations_directory = f'/{dag_path}/../test'
payments_directory = f'/{dag_path}/../payments'

default_args = {
    'owner': 'gilson',
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    dag_id=dag_name,
    schedule_interval='@once',
    default_args=default_args,
    start_date=datetime(2022, 9, 10),
    catchup=True,
    max_active_runs=1
) as dag:
    
    # start = EmptyOperator(task_id='start')
    # end = EmptyOperator(task_id='end')
    
    @task(task_id="upload_data")
    def upload_data(**context):
        
        s3_hook = S3Hook(aws_conn_id="upload_minio")

        s3_hook.load_file(filename =f'{originations_directory}/{context["ds"]}.csv',
                          bucket_name='originations',
                          key=f'{context["ds"]}.csv',
                          replace=True)
        
        # s3_hook.load_file(filename =f'{originations_directory}/{context[0]}.json',
        #                   bucket_name='originations',
        #                   key=f'{context[0]}.json',
        #                   replace=True)
        
        # s3_hook.load_file(filename =f'{payments_directory}/{context["uuid"]}.json',
        #                   bucket_name='payments',
        #                   key=f'{context["uuid"]}.json',
        #                   replace=True)
        

    upload_data() 