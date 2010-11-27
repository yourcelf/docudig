#rm db.sqlite3

DBNAME=docudig
DBUSER=django_dev

sudo su postgres -c "dropdb $DBNAME"
sudo su postgres -c "createdb -O $DBUSER $DBNAME"

python manage.py syncdb --noinput
python manage.py import_documents data/combined.csv
python manage.py build_solr_schema > schema.xml
echo "New Solr schema created: schema.xml.  Please copy or link this schema into Solr's 'conf' directory, then restart Solr."
echo "press Enter when ready."
read foo
python manage.py rebuild_index --noinput
