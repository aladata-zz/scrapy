DROP INDEX idx_vendors_company_name;
DROP INDEX idx_contracts_contract_number;
DROP INDEX idx_payments_contract_id;
DROP INDEX idx_contracts_vendor_id;
DROP INDEX idx_tmp_vendors_company_name;


DROP TABLE payments;
DROP TABLE contracts;
DROP TABLE vendors;
DROP TABLE tmp_vendors;
DROP TABLE tmp_payments;



-- Table: vendors

-- DROP TABLE vendors;

CREATE TABLE vendors
(
  vendor_id uuid NOT NULL DEFAULT uuid_generate_v4(),
  company_name character varying(250) NOT NULL,
  dba_name character varying(250),
  owner_first character varying(50),
  owner_last character varying(50),
  physical_address character varying(250),
  city character varying(250),
  state character varying(250),
  zip character varying(250),
  mailing_address character varying(250),
  mailing_address_city character varying(250),
  mailing_address_state character varying(250),
  mailing_address_zip character varying(250),
  phone character varying(250),
  fax character varying(250),
  email character varying(250) NOT NULL,
  agency character varying(250),
  certification_type character varying(250),
  capability character varying(250),
  work_districts_regions character varying(250),
  industry character varying(250),
  business_size character varying(250),
  general_location character varying(250),
  location character varying(250),
  CONSTRAINT vendors_pkey PRIMARY KEY (vendor_id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE vendors
  OWNER TO uplank;


-- Table: contracts

-- DROP TABLE contracts;

CREATE TABLE contracts
(
  contract_id uuid NOT NULL DEFAULT uuid_generate_v4(),
  vendor_id uuid NOT NULL,
  department character varying(250),
  contract_number character varying(50) NOT NULL,
  amount character varying(50),
  spending_to_date character varying(50),
  contract_start_date character varying(50),
  contract_end_date character varying(50),
  contract_description character varying(500),
  contract_type character varying(250),
  contract_approved_date character varying(50),
  CONSTRAINT contracts_pkey PRIMARY KEY (contract_id),
  CONSTRAINT contracts_vendor_id_fkey FOREIGN KEY (vendor_id)
      REFERENCES vendors (vendor_id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
  OIDS=FALSE
);
ALTER TABLE contracts
  OWNER TO uplank;


-- Table: payments

-- DROP TABLE payments;

CREATE TABLE payments
(
  contract_id uuid NOT NULL,
  payment_date date NOT NULL,
  business_unit character varying(250),
  document_id character varying(50),
  amount money NOT NULL,
  CONSTRAINT payments_contract_id_fkey FOREIGN KEY (contract_id)
      REFERENCES contracts (contract_id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
  OIDS=FALSE
);
ALTER TABLE payments
  OWNER TO uplank;


-- Table: tmp_vendors

CREATE TABLE tmp_vendors
(
  company_name character varying(250),
  dba_name character varying(250),
  owner_first character varying(50),
  owner_last character varying(50),
  physical_address character varying(250),
  city character varying(250),
  state character varying(250),
  zip character varying(250),
  mailing_address character varying(250),
  mailing_address_city character varying(250),
  mailing_address_state character varying(250),
  mailing_address_zip character varying(250),
  phone character varying(250),
  fax character varying(250),
  email character varying(250),
  agency character varying(250),
  certification_type character varying(250),
  capability character varying(1000),
  work_districts_regions character varying(250),
  industry character varying(250),
  business_size character varying(250),
  general_location character varying(250),
  location character varying(250)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE tmp_vendors
  OWNER TO uplank;


-- Table: tmp_payments

CREATE TABLE tmp_payments
(
  vendor character varying(250),
  payment_date date,
  business_unit character varying(250),
  document_id character varying(50),
  amount character varying(20),
  contract_number character varying(50)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE tmp_payments
  OWNER TO uplank;



CREATE UNIQUE INDEX idx_contracts_contract_number
  ON contracts
  USING btree
  (contract_number COLLATE pg_catalog."default");


CREATE UNIQUE INDEX idx_vendors_company_name
  ON vendors
  USING btree
  (company_name COLLATE pg_catalog."default");

CREATE INDEX idx_contracts_vendor_id
  ON contracts
  (vendor_id); 


CREATE INDEX idx_payments_contract_id
  ON payments
  (contract_id);

CREATE INDEX idx_tmp_vendors_company_name
  ON tmp_vendors
  USING hash
  (company_name COLLATE pg_catalog."default");

