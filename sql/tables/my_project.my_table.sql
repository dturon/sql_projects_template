
CREATE TABLE my_project.my_table(
    id serial PRIMARY KEY,
    status my_project.my_enum,
    description text
);

ALTER TABLE my_project.my_table OWNER TO dturon;

CREATE INDEX ON my_project.my_table(description);
