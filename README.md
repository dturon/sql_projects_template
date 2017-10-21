# sql projects template
template for automated version / test upgrades 

## prerequirements
* colordiff
* pg_extractor

```bash
dnf install colordiff
```

```bash
cd somewere
git clone https://github.com/omniti-labs/pg_extractor
cd pg_extractor
mv pg_extractor.py pg_extractor
ln -s /usr/bin/pg_extractor pg_extractor

ln -s /usr/bin/sql_manager sql_manager.py 
```

## usage
* update files, create new files
* commit changes
* create tag 
* make

## commands
* ```make dirs```  # create sql directories
* ```make``` # create $PROJECT_NAME--$VERSION.sql file (first time need run 2x, sort install.sql file)
* ```make test``` # test load $PROJECT_NAME--$VERSION.sql into database
* ```make upgrade``` create upgrade file $PROJECT_NAME--$OLD_VERSION--$VERSION.sql 
* ```make test_upgrade``` # load $PROJECT_NAME--$VERSION.sql, $PROJECT_NAME--$OLD_VERSION.sql + upgrade $PROJECT_NAME--$OLD_VERSION--$VERSION.sql, extract DBs using pg_extractor and show diff (when everything is ok show empty diff)

## details
Make use local git, so you can make/update/delete tags before you push tags to upstream branch 


```make```
make will create new sql install file $PROJECT_NAME--$VERSION.sql if no new files added/deleted, if not show diff install.sql file instead. You need remove/add lines in correct order if there is some dependencies and run make again.
* make new RPM, copy files from install dir, current $PROJECT_NAME--$VERSION.sql file and all upgrade files from sql/upgdares/*

## links
dirs created with [pg_extractor](https://github.com/omniti-labs/pg_extractor)
usage
`python3.4 pg_extractor.py --getall --gettriggers -U postgres -d dbname`