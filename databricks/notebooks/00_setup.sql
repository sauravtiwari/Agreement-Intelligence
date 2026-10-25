-- Databricks notebook source
-- Phase 0: medallion layout in Unity Catalog.
-- Run in a Free Edition workspace (SQL warehouse or serverless notebook).

CREATE CATALOG IF NOT EXISTS contracts COMMENT 'Agreement Intelligence learning catalog (public CUAD data only)';

-- COMMAND ----------

CREATE SCHEMA IF NOT EXISTS contracts.bronze COMMENT 'Raw PDF binaries ingested by Auto Loader';
CREATE SCHEMA IF NOT EXISTS contracts.silver COMMENT 'Parsed documents: pages, tables, layout boxes';
CREATE SCHEMA IF NOT EXISTS contracts.gold   COMMENT 'Agreements, parties, clauses, chunks';

-- COMMAND ----------

-- Upload CUAD PDFs here: Catalog Explorer > contracts > bronze > raw_pdfs > Upload,
-- or with the CLI: databricks fs cp -r data/cuad/pdfs dbfs:/Volumes/contracts/bronze/raw_pdfs/cuad
CREATE VOLUME IF NOT EXISTS contracts.bronze.raw_pdfs COMMENT 'Landing zone for source PDFs';

-- COMMAND ----------

SHOW SCHEMAS IN contracts;
