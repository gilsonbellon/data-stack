import os 
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

dag_path = os.path.join(os.path.dirname(__file__))
data_src_dir = f'/{dag_path}/../data_src'

def upload_files_to_s3(**kwargs):
    s3_hook = S3Hook(aws_conn_id="upload_minio")

    originations_local_dir = f'{data_src_dir}/originations'
    print(f"orig local dir: {originations_local_dir}")

    payments_local_dir = f'{data_src_dir}/payments'
    print(f"pay local dir: {payments_local_dir}")

    for root, dirs, files in os.walk(originations_local_dir):
        for filename in files:
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, originations_local_dir)
            s3_key = os.path.join(relative_path).replace("\\", "/")

            s3_hook.load_file(
                filename=local_path,
                key=s3_key,
                bucket_name='originations',
                replace=True
            )

            # print(f"uploading ... {s3_key}")

    for root, dirs, files in os.walk(payments_local_dir):
        for filename in files:
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, payments_local_dir)
            s3_key = os.path.join(relative_path).replace("\\", "/")

            s3_hook.load_file(
                filename=local_path,
                key=s3_key,
                bucket_name='payments',
                replace=True
            )

            # print(f"uploading ... {s3_key}")
            

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 10, 10),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    's3_file_uploader',
    default_args=default_args,
    description='upload files from local dir to minio s3',
    schedule_interval='@once',
)

upload_task = PythonOperator(
    task_id='upload_files_to_s3',
    python_callable=upload_files_to_s3,
    provide_context=True,
    dag=dag
)
