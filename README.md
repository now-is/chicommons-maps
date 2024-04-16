# maps

## Getting Started

There are three options for running the web app:
 1. Development Mode (via Docker)
 2. Production Mode (via Docker)
 3. Local (without Docker)

### Option 1: Development Mode (via Docker)
Development mode is a simplified installation to expedite development. System installation and management will be managed by Docker.

#### Docker
* Docker Compose File: [`docker-compose.yml`](./docker-compose.yml)
* Containers managed: 
    * `web`: The Django Backend app running its debug server.
    * `client`: The node Frontend app running its debug server.

#### Database
* Engine: `sqlite`
* Location: `./maps/data/db.sqlite3`

Development mode uses a locally stored SQLite database. When the database is created, it will be loaded with testing data and a Django/Python app superuser will be created. For more details, see [entrypoint_dev.sh](./web/entrypoint_dev.sh). 

If you need to reset the database, delete the SQLite database in `./data/` and restart Docker -- a new, clean database will be created for you.

#### Web Server
* Front end: `http://localhost:3000`
* Back end: `http://localhost:8000/api/v1`

Both the front end and backend are running their respective debug servers and are running on separate ports.

#### Email Server

Development mode is configured to **not** send emails. Any emails sent from development will be printed to the console.

#### Installation
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Clone the Maps Repository
    ```
    git clone https://github.com/chicommons/maps.git
    ```
3. Start the application via Docker Compose.
    ```
    cd maps
    docker-compose up
    ```

#### Helpful Commands
* To start the app: `docker-compose up`
* To shutdown the app: `docker-compose down`
* To reset the Docker container to a "stock" install : `docker-compose up --build`

### Option 2: Production Mode (via Docker)
Production mode is a complex installation used for production environments. 

#### Docker
* Docker Compose File: [`docker-compose.prod.yml`](./docker-compose.prod.yml)
* Containers managed: 
    * `web`: The Django Backend app
    * `client`: The node Frontend app. The frontend only runs during startup. It is compiled through a Docker container that will shut down when completed.
    * `postgres`: The Postgres database.
    * `nginx`: The NGINX Web server. Serves both the frontend and backend. Communication with the backend is managed by UWSGI via socket.

#### Database
* Engine: `PostgreSQL`
* Location: `./postgres/`

Production mode uses a Postgres Database running in a separate docker container. The docker installation will make no changes to the postgres database and assumes that all 
migrations and data imports are being performed directly by the administrator. 

To connect to the production database, connect to the database directly via the 5105 port locally (see docker-compose.prod.yml).
To run Django migrations or other admin tasks, log into the back end's terminal `docker exec -it web-prod /bin/bash`.

#### Web Server
* Front end: `http://<server_ip>`
* Back end: `http://<server_ip>/api/v1`

The front end and back end are served by a common NGINX web server. They can be accessed via the same port. 

#### Email Server

Production mode is configured to send emails via SMTP. See [Environment Variables](#environment-variables) for details on configuration. 

#### Installation
1. Install Docker
1. Clone the Maps Repository
    ```
    git clone https://github.com/chicommons/maps.git
    ```

1. Create a `.env` file to store secrets needed by production. 

    The file is stored by default in `./config/.env/`. The location can be changed by modifying the env_file field in the `docker-compose.prod.yml` file. A template for the `.env` can be found at [./config/.env-template](./config/.env-template). See [Environment Variables](#environment-variables) for more details.

1. Start the application via Docker Compose.
    ```
    cd maps
    docker-compose -f docker-compose.prod.yml up
    ```

1. Install data in database (optional)

    If working in a new database, run migrations and load data. See [./web/entrypoint_dev.sh](./web/entrypoint_dev.sh) for an example of how the Development environment handles this. 

#### Helpful Commands
* To start the app: `docker-compose -f docker-compose.prod.yml up`
* To shutdown the app: `docker-compose -f docker-compose.prod.yml down`
* Log into Backend container's terminal: `docker exec -it web-prod /bin/bash`

### Option 3: Local (without Docker)
Local mode is the most complex method for installation. The process installs a production-like environment outside of Docker. It is not recommended for everyday development. It is only useful to run local debugging tools. 

#### Installation 
1. Install Prerequisites
    - Postgres 10.5
    - Node 19 or above
    - Python 3.9 (and not higher)
    - Conda (optional)

1. Configure Postgres

    After installing PostGres, we may need to make some configurations.  Specifically, we need to enable login to happen without having a user with the same name defined on your system.  To do this, look for the "pg_hba.conf" file (on Mac, this is usually found at /usr/local/var/postgresql@10.0/pg_hba.conf).  Near the bottom of the file, you will want to add these lines and restart Postgres.
    ```
    # Login for chicommons application
    local   all             chicommons                              md5
    ```

1. Setup Postgres accounts and create empty database. (optional)

    If this is a new Postgres installation, create Postgres accounts and configure the database.

    Open the Postgres Client `psql` and run the following commands to setup the Postgres database. Be sure to replace the following values in your commands. See [Environment Variables](#environment-variables) for more details.
     - $POSTGRES_DB: the name of your Postgres Database
     - $POSTGRES_USER: the superuser of your Postgres Database. 
     - $POSTGRES_PASSWORD: the password of the superuser

    ```
    SELECT 'CREATE DATABASE $POSTGRES_DB' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$POSTGRES_DB');

    SELECT 'DROP OWNED BY $POSTGRES_USER;' WHERE EXISTS (SELECT rolname FROM pg_roles WHERE rolname = '$POSTGRES_USER');

    DROP ROLE IF EXISTS $POSTGRES_USER;

    create user $POSTGRES_USER with encrypted password '$POSTGRES_PASSWORD';

    grant all privileges on database $POSTGRES_DB to $POSTGRES_USER;
    ```

1. Create a CONDA Python Environment (optional)

    The app requires python 3.9 and can behave unexpectedly on different versions. It is recommend to us Conda to manage your python and package installations, and environment variables. Python Virtual Environments ([`venv`](https://docs.python.org/3/library/venv.html)) also work, however you'll need to manually manage the Python version requirements.
    ```
    # Create a CONDA environment: 
    conda create --name <env-name> python=3.9

    # Activate the CONDA environment 
    conda activate <env-name>
    ```

1. Configure Environment Variables

    See [Environment Variables](#environment-variables) for more details on the needed environment configuration variables. 

    **Option A: Using CONDA Environment Variables:**
    ```
    # Replace 'key=value' with a line from your .env config file.
    conda env config vars set my_var=value
    # Repeat for each line in your .env config file.

    # Restart your CONDA environment for the changes to take effect. 
    conda deactivate
    conda activate <env-name>
    ```

    **Option B. Using Terminal Environment Variables:**

    On Mac or Linux, open your ~/.profile file and add these lines to the end of your file. Adjust if you have different settings.
    ```
    # Replace 'key=value' with a line from your .env config file.
    export key=value
    # Repeat for each line in your .env config file.
    ```

    Run this command to set the environment variables in your current shell.
    ```
    source ~/.profile
    ```

1. Install the Django/Python app

    ```
    cd web

    # Install required python packages
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    ```

1. Install data in database (optional)

    If working in a new database, run migrations and load data. See [./web/entrypoint_dev.sh](./web/entrypoint_dev.sh) for an example of how the Development environment handles this. 

1. Run the Django/Python app
    ```
    python manage.py runserver
    ```

    This starts the Django/Python app on port 8000 (http://localhost:8000).  

1. Run the React/Node app
    ```
    cd client
    npm install --force -g yarn
    npm run start
    ```

    This will start the React application on port 3000.  If you also have the Django/Python app running locally, you should be able to visit http://localhost:3000 and see the start page.

### Environment Variables
The application requires a set of environment variables to run. A list of required environment variables can be found in the [`.config/env-template`](./config/.env-template) file. Refer to your respective installation guide on how to set the environment variables. 
- `POSTGRES_HOST`
  - The hostname of the Postgres database.
  - **Default:** `postgres` (if using `Production Mode`)
- `POSTGRES_DB`
  - The name of the Postgres database.
  - **Default:** `directory_data`
- `POSTGRES_USER`
  - The username to access the Postgres database.
  - **Default:** `chicommons`
- `POSTGRES_PASSWORD`
  - The password for POSTGRES_USER to access the Postgres database.
  - **Default:** `password` (... and you really should change it)
- `POSTGRES_PORT`
  - The port number of the Postgres database.
  - **Default:** 5432
- `DJANGO_SETTINGS_MODULE`
  - The port number of the Postgres database.
  - **Default:** 
    * `directory.settings.prod` for `Production Mode` or `Local` installations
    * `directory.settings.dev` for `Development Mode` installations.
- `EMAIL_HOST`
  - The host to use for sending emails. See [EMAIL_HOST](https://docs.djangoproject.com/en/5.0/ref/settings/#email-host) for more details.
- `EMAIL_PORT`
  - Port to use for SMTP server defined in `EMAIL_HOST`. See [EMAIL_PORT](https://docs.djangoproject.com/en/5.0/ref/settings/#email-port) for more details.
  - **Default:**  25
- `EMAIL_HOST_USER`
  - Username to use for the SMTP server defined in `EMAIL_HOST`. If empty, Django won’t attempt authentication. See [EMAIL_HOST_USER](https://docs.djangoproject.com/en/5.0/ref/settings/#email-host-user) for more details.
  - **Default:** ""
- `EMAIL_HOST_PASSWORD`
  - Password to use for the SMTP server defined in `EMAIL_HOST`. This setting is used in conjunction with `EMAIL_HOST_USER` when authenticating to the SMTP server. If either of these settings is empty, Django won’t attempt authentication. See [EMAIL_HOST_PASSWORD](https://docs.djangoproject.com/en/5.0/ref/settings/#email-host-password.) for more details.
  - **Default:** ""
- `SECRET_KEY`
  - A secret key for a particular Django installation. This is used to provide cryptographic signing, and should be set to a unique, unpredictable value. See [SECRET_KEY](https://docs.djangoproject.com/en/5.0/ref/settings/#secret-key) for more details.
  - **Default:** ""