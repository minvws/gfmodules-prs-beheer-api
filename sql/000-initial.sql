
--- Create web user localisation
CREATE ROLE prs_beheer_api;
ALTER ROLE prs_beheer_api WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION NOBYPASSRLS ;

--- Create DBA role
CREATE ROLE prs_beheer_api_dba;
ALTER ROLE prs_beheer_api_dba WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION NOBYPASSRLS ;

CREATE TABLE deploy_releases
(
        version varchar(255),
        deployed_at timestamp default now()
);

ALTER TABLE deploy_releases OWNER TO prs_beheer_api_dba;

GRANT SELECT ON deploy_releases TO prs_beheer_api;

