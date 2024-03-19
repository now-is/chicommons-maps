# directory/fixtures
## seed_data.yaml
Seed_data.yaml contains an initial set of data to be imported in to the database for development and testing. 
To import seed_data.yaml (and potential delete any existing data): 
`python manage.py insert_seed_data`
To generate a new version of seed_data.yaml:
`python manage.py dumpdata -o ./directory/fixtures/seed_data_new.yaml --format yaml --exclude=auth --exclude=contenttypes --exclude=sessions`