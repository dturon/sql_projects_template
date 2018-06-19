EXTENSION = my_project
EXTVERSION = $(shell git tag | sort -V | tail -n 1)
EXTVERSION_OLD = $(shell git tag | sort -V | tail -n 2 | head -n 1)
DB_HOST = localhost
ROOT_DIR = ..

.PHONY: all clean cleandb upgrade test_upgrade dirs test

all: clean $(EXTENSION)--$(EXTVERSION).sql

$(EXTENSION)--$(EXTVERSION).sql:
	sql_manager -p $(EXTENSION) -d $(ROOT_DIR) -a build

test: $(EXTENSION)--$(EXTVERSION).sql
	sql_manager -p $(EXTENSION) -d $(ROOT_DIR) -a test --host $(DB_HOST)

upgrade: 
	sql_manager -p $(EXTENSION) -d $(ROOT_DIR) -a upgrade

test_upgrade: $(EXTENSION)--$(EXTVERSION_OLD).sql $(EXTENSION)--$(EXTVERSION).sql upgrades/$(EXTENSION)--$(EXTVERSION_OLD)--$(EXTVERSION).sql
	sql_manager -p $(EXTENSION) -d $(ROOT_DIR) -a test_upgrade --host $(DB_HOST)

clean:
	sql_manager -p $(EXTENSION) -d $(ROOT_DIR) -a clean

cleandb:
	sql_manager -p $(EXTENSION) -d $(ROOT_DIR) -a cleandb --host $(DB_HOST)
	
dirs:
	sql_manager -p $(EXTENSION) -d $(ROOT_DIR) -a make_dirs	


