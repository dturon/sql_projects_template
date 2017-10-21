
CREATE OR REPLACE FUNCTION my_project.my_table_insert()
RETURNS TRIGGER AS
$$
    BEGIN

        IF NEW.desctription IS NULL THEN
            NEW.desctription = 'No description';
        END IF;

    END;

$$ LANGUAGE plpgsql;
