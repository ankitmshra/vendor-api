#!/bin/sh

echo 'Waiting for postgres...'

while ! nc -z $DB_HOSTNAME $DB_PORT; do
    sleep 0.1
done

echo 'Running migrations...'
python manage.py makemigrations
python manage.py migrate

echo 'Collecting static files...'
python manage.py collectstatic --no-input

# Run app.py when the container launches
exec "$@"