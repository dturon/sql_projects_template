
DROP TRIGGER IF EXISTS my_trigger ON my_project.my_table;

CREATE TRIGGER my_trigger 
BEFORE INSERT
ON my_project.my_table
FOR EACH ROW
EXECUTE PROCEDURE my_project.my_table_insert(); 
