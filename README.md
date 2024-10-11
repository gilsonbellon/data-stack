## Building a Stack Data Pipeline

### API's

- **Airbyte:** data extraction - http://localhost:8000/
- **Dbt:** data transformation
- **Airflow:** task orchestration - http://localhost:8085/
- **Clickhouse:** data storage
- **Openmetadata:** data catalog - http://localhost:8585/
- **Minio:** object storage - http://localhost:9090/
- Metabase: data visualization - http://localhost:3000/

## Requirements

- Docker Desktop
- Docker compose
- Windows 10 or higher, Mac or Linux - This project has been tested on Mac M1, should works fine for Windows or Linux as well
- Python 3.6 or higher
- Recommended 12GB RAM or higher only for docker containers.
- Java

---

## Credentials

### Airflow

- **username:** `airflow`
- **password:** `airflow`

### Minio

Minio acces and secret keys along with url_endpoint are used to log in and for connections.

- **minio_access_key:** `minio`
- **minio_secret_key:** `minio1234`
- **url_endpoint:** http://host.docker.internal:9000
- **port:** 9000

### Clickhouse DWH

* **username:** `default`
* **password:** topsecret
* **host:** `localhost`
* **port:** 8123

*If you connect to your database through Mysql or DBeaver, you need to use the external host and port.*

### Airbyte

Enter a valid email when trying to log in.

- For other configurations:
- **internal_host:** `host.docker.internal`
- **internal_host_and_port:** `http://host.docker.internal:8000`
- **user:** `airbyte`
- **password:** `airbyte`

### Openmetadata

- **username:** `admin`
- **password:** `admin`

### Metabase

* Enter some email
* **usermame**: metabase1234
* **passwor**d: metabase1234

---

## Setup Instructions

1. Open your terminal.
2. Navigate to the root of the `data-stack` repository
3. Run `docker compose up `to initialize the containers. If you want to run it in the background, add `-d` argument.
4. Perform Airflow configurations (*Section below*)
5. Run the Airflow DAG called `upload_data_to_s3` for uploading csv files into minio s3 bucket.
6. Perform Airbyte configurations (*Section below*)
7. Run the Airflow DAG called `dbt_model` to create the tables in the bronze, silver, and gold schemas.
8. Perform Openmetadata configurations. (*Section below*)
9. Play around all the technologies.

---

## Clickhouse Configurations

Open Clichouse on DBeaver or any similar software, setting as above.

CREATE USER 'airbyte_user'@'%' IDENTIFIED BY 'airbyte1234';

GRANT CREATE ON * TO airbyte_user;

GRANT CREATE ON default.* TO airbyte_user;
GRANT DROP ON * TO airbyte_user;
GRANT TRUNCATE ON * TO airbyte_user;
GRANT INSERT ON * TO airbyte_user;
GRANT SELECT ON * TO airbyte_user;
GRANT CREATE DATABASE ON airbyte_internal.* TO airbyte_user;
GRANT CREATE TABLE ON airbyte_internal.* TO airbyte_user;
GRANT DROP ON airbyte_internal.* TO airbyte_user;
GRANT TRUNCATE ON airbyte_internal.* TO airbyte_user;
GRANT INSERT ON airbyte_internal.* TO airbyte_user;
GRANT SELECT ON airbyte_internal.* TO airbyte_user;


### After data syncronization from Airbyte:

use dwh;

CREATE TABLE IF NOT EXISTS payment_data
(
    paymentId String,
    installmentId String,
    paymentDate DateTime,
    paymentValue Decimal(10, 2)
) ENGINE = MergeTree()
ORDER BY (paymentId, installmentId);

INSERT INTO payment_data
SELECT
JSONExtractString(_airbyte_data, 'paymentId') AS paymentId,
JSONExtractString(_airbyte_data, 'installmentId') AS installmentId,
toDateTime(JSONExtractString(_airbyte_data, 'paymentDate')) AS paymentDate,
toDecimal64(JSONExtractString(_airbyte_data, 'paymentValue'), 2) AS paymentValue
FROM dwh_raw__stream_payments_stream;


```
CREATE TABLE Originations (
    originationId String,
    clientId String,
    registerDate Date
) ENGINE = MergeTree()
ORDER BY originationId;

INSERT INTO Originations
SELECT
JSONExtractString(_airbyte_data, 'originationId') AS originationId,
    JSONExtractString(_airbyte_data, 'clientId') AS clientId,
    toDateTime(JSONExtractString(_airbyte_data, 'registerDate')) AS registerDate
FROM dwh_raw__stream_originations_stream;



CREATE TABLE Installments (
    originationId String,
    installmentId String,
    dueDate Date,
    installmentValue Decimal(10, 2)
) ENGINE = MergeTree()
ORDER BY (originationId, installmentId);

INSERT INTO Installments
SELECT
JSONExtractString(_airbyte_data, 'originationId') AS originationId,
   arrayJoin(arrayMap(x -> JSONExtractString(x, 'installmentId'), JSONExtractArrayRaw(_airbyte_data, 'installments'))) AS installmentId,
   arrayJoin(arrayMap(x -> toDateTime(JSONExtractString(x, 'dueDate')), JSONExtractArrayRaw(_airbyte_data, 'installments'))) AS dueDate,
   arrayJoin(arrayMap(x -> toDecimal64(JSONExtractString(x, 'installmentValue'), 2), JSONExtractArrayRaw(_airbyte_data, 'installments'))) AS installmentValue
FROM dwh_raw__stream_originations_stream;
```



## Airflow Configurations

1. Open Airflow
2. Go to connections
3. Create the Minio S3 connection with the below configuration:
   *If you test this connection it will fail, just ignore it.*
   - **Connection Type:** `Amazon Web Services`
   - **Connection Id:** `aws_default`
   - **Extra:** `{"aws_access_key_id": "minio", "aws_secret_access_key": "minio1234", "endpoint_url": "http://host.docker.internal:9000"}`
4. Create the Postgres connection
   - **Connection Type:** `Postgres`
   - **Connection Id:** `postgres_default`
   - **Host:** `postgres_dwh`
   - **Schema:** `dwh`
   - **Login:** `dwh`
   - **Password:** `dwh`
   - **Port:** `5432`
5. Create the Airbyte connection (Optional, in case you want to use the stack for your own development)
   - **Connection Type:** `Airbyte`
   - **Connection Id:** `airbyte_default`
   - **Host:** `host.docker.internal`
   - **Username:** `airbyte`
   - **Password:** `password`
   - **Port:** `8000`

---

## Airbyte Configurations

1. Open Airbyte, enter an email and select `Get started`
2. Select sources (*left sidebar*) , in the search bar write `S3` and select it
3. Create the S3 connection for customer data
   - **Source_name:** `S3_originations`
   - **Output_stream_name:** `originations-stream`
   - **Bucket:** `originations`
   - **Aws_access_key_id:** `minio`
   - **Aws_secret_access_key:** `minio1234`
   - **Endpoint:** `http://host.docker.internal:9000`
   - ***Scroll until the end and select `set up source`***
4. Create the S3 connection for customer driver data
   - **Source_name:** `S3_payments`
   - **Output_stream_name:** `payments-stream`
   - **Bucket:** `payments`
   - **Aws_access_key_id:** `minio`
   - **Aws_secret_access_key:** `minio1234`
   - **Endpoint:** `http://host.docker.internal:9000`
   - ***Scroll until the end and select `set up source`***
5. Select Destinations (*left sidebar*), search for Clickhouse and select it.
7. Create the Postgres connection as destination
   - **Destination_name:** `Clickhouse_DWH`
   - **Host:** `localhost`
   - **Port:** `8432`
   - **Db_name:** `dwh`
   - **user:** `airbyte_user`
   - **password:** `airbyte1234`
   - ***Scroll until the end and select `set up destination`***
8. After setting up the connections, select Connections (*left side bar*) and click on `Sync now` for your 3 connections.
10. Wait until the syncronization finished.

---


### Pipeline Services - Airflow

1. Select `Services` in the left sidebar.
2. Select `Add New Service` in the right top corner.
3. Select `Pipeline Services` from the drop down list.
4. Select `Airflow` and then `Next`
5. Enter a name for your service connection and select `Next`
6. Enter the below configuration:
   - **Host_and_Port:** `http://localhost:8085/`
   - **Metadata_Database_Connection:** `PostgresConnection`
   - **Username:** `airflow`
   - **Password:** `airflow`
   - **Host_and_Port:** `host.docker.internal:5432`
   - **Database:** `airflow`
7. Test your connection and save.
8. Navigate to your airflow service connection and create a metadata ingestion.
9. Run the metadata ingestion.

### Pipeline Services - Airbyte

1. Select `Services` in the left sidebar.
2. Select `Add New Service` in the right top corner.
3. Select `Pipeline Services` from the drop down list.
4. Select `Airbyte` and then `Next`
5. Enter a name for your service connection and select `Next`
6. Enter the below configuration:
   - **Host_and_Port:** `http://host.docker.internal:8000`
   - **Metadata_Database_Connection:** `PostgresConnection`
   - **Username:** `airbyte`
   - **Password:** `airbyte`
7. Test your connection and save.
8. Navigate to your airflow service connection and create a metadata ingestion.
9. Run the metadata ingestion.

