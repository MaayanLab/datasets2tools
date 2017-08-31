DROP DATABASE IF EXISTS `datasets2tools`;
CREATE DATABASE `datasets2tools` DEFAULT CHARACTER SET utf8;
USE `datasets2tools`;

### Dataset

CREATE TABLE repository (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`repository_name` VARCHAR(50) UNIQUE,
	`repository_homepage_url` VARCHAR(255),
	`repository_icon_url` VARCHAR(255)
);

CREATE TABLE dataset_type (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`dataset_type_name` VARCHAR(50),
	`dataset_type_icon_url` VARCHAR(255)
);

CREATE TABLE dataset (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`repository_fk` INT,
	`dataset_accession` VARCHAR(30) UNIQUE,
	`dataset_title` VARCHAR(255),
	`dataset_description` TEXT,
	`dataset_type_fk` INT,
	FOREIGN KEY (repository_fk) REFERENCES repository(id),
	FOREIGN KEY (dataset_type_fk) REFERENCES dataset_type(id)
);

CREATE TABLE related_dataset (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`source_dataset_fk` INT,
	`target_dataset_fk` INT,
	`similarity` DOUBLE,
	FOREIGN KEY (source_dataset_fk) REFERENCES dataset(id),
	FOREIGN KEY (target_dataset_fk) REFERENCES dataset(id)
);

### Tool

CREATE TABLE tool (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`tool_name` VARCHAR(100) UNIQUE,
	`tool_description` TEXT,
	`tool_homepage_url` VARCHAR(255),
	`tool_icon_url` VARCHAR(255)
);

CREATE TABLE related_tool (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`source_tool_fk` INT,
	`target_tool_fk` INT,
	`similarity` DOUBLE,
	FOREIGN KEY (source_tool_fk) REFERENCES tool(id),
	FOREIGN KEY (target_tool_fk) REFERENCES tool(id)
);

### Article

CREATE TABLE journal (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`journal_name` VARCHAR(50) UNIQUE,
	`journal_description` TEXT,
	`journal_homepage_url` VARCHAR(255)
);

CREATE TABLE article (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`journal_fk` INT,
	`abstract` TEXT,
	`authors` TEXT,
	`date` DATE,
	`doi` VARCHAR(255) UNIQUE,
	FOREIGN KEY (journal_fk) REFERENCES journal(id),
	FOREGIN KEY (tool_fk) REFERENCES tool(id)
);

### Canned analysis

CREATE TABLE canned_analysis (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`canned_analysis_title` VARCHAR(255),
	`canned_analysis_description` TEXT,
	`canned_analysis_url` VARCHAR(255) UNIQUE,
	`canned_analysis_preview_url` VARCHAR(255)
);

CREATE TABLE related_canned_analysis (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`source_canned_analysis_fk` INT,
	`target_canned_analysis_fk` INT,
	`similarity` DOUBLE,
	FOREIGN KEY (source_canned_analysis_fk) REFERENCES canned_analysis(id),
	FOREIGN KEY (target_canned_analysis_fk) REFERENCES canned_analysis(id)
);

CREATE TABLE analysis_to_dataset (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`canned_analysis_fk` INT,
	`dataset_fk` INT,
	FOREIGN KEY (canned_analysis_fk) REFERENCES canned_analysis(id),
	FOREIGN KEY (dataset_fk) REFERENCES dataset(id)
);

CREATE TABLE analysis_to_tool (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`canned_analysis_fk` INT,
	`tool_fk` INT,
	FOREIGN KEY (canned_analysis_fk) REFERENCES canned_analysis(id),
	FOREIGN KEY (tool_fk) REFERENCES tool(id)
);

CREATE TABLE term (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`term_name` VARCHAR(50) UNIQUE,
	`term_description` TEXT
);

CREATE TABLE canned_analysis_metadata (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`canned_analysis_fk` INT,
	`term_fk` INT,
	`value` VARCHAR(255),
	FOREIGN KEY (canned_analysis_fk) REFERENCES canned_analysis(id),
	FOREIGN KEY (term_fk) REFERENCES term(id)
);

### Keywords

CREATE TABLE keywords (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`dataset_fk` INT DEFAULT NULL,
	`tool_fk` INT DEFAULT NULL,
	`canned_analysis_fk` INT DEFAULT NULL,
	`keyword` VARCHAR(255),
	FOREIGN KEY (dataset_fk) REFERENCES dataset(id),
	FOREIGN KEY (tool_fk) REFERENCES tool(id),
	FOREIGN KEY (canned_analysis_fk) REFERENCES canned_analysis(id)
);

### User

CREATE TABLE user (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`username` VARCHAR(50) UNIQUE,
	`email` VARCHAR(50) UNIQUE,
	`password` VARCHAR(80)
);

