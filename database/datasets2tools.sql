DROP DATABASE IF EXISTS `datasets2tools`;
CREATE DATABASE `datasets2tools` DEFAULT CHARACTER SET utf8;
USE `datasets2tools`;

# Dataset

CREATE TABLE repository (
	`id` INT AUTO_INCREMENT PRIMARY KEY
);

CREATE TABLE dataset (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`repository_fk` INT,
	FOREIGN KEY (repository_fk) REFERENCES repository(id)
);

CREATE TABLE similar_dataset (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`dataset_1_fk` INT,
	`dataset_2_fk` INT,
	FOREIGN KEY (dataset_1_fk) REFERENCES dataset(id),
	FOREIGN KEY (dataset_2_fk) REFERENCES dataset(id)
);

CREATE TABLE data_type (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`dataset_fk` INT,
	FOREIGN KEY (dataset_fk) REFERENCES dataset(id)
);

# Tool

CREATE TABLE tool (
	`id` INT AUTO_INCREMENT PRIMARY KEY
);

CREATE TABLE similar_tool (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`tool_1_fk` INT,
	`tool_2_fk` INT,
	FOREIGN KEY (tool_1_fk) REFERENCES tool(id),
	FOREIGN KEY (tool_2_fk) REFERENCES tool(id)
);

CREATE TABLE script (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`tool_fk` INT,
	FOREIGN KEY (tool_fk) REFERENCES tool(id)
);

CREATE TABLE script_to_datatype (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`script_fk` INT,
	`data_type_fk` INT,
	FOREIGN KEY (script_fk) REFERENCES script(id),
	FOREIGN KEY (data_type_fk) REFERENCES data_type(id)
);

# Article

CREATE TABLE journal (
	`id` INT AUTO_INCREMENT PRIMARY KEY
);

CREATE TABLE article (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`journal_fk` INT,
	FOREIGN KEY (journal_fk) REFERENCES journal(id)
);

CREATE TABLE article_to_tool (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`article_fk` INT,
	`tool_fk` INT,
	FOREIGN KEY (article_fk) REFERENCES article(id),
	FOREIGN KEY (tool_fk) REFERENCES tool(id)
);


# Canned analysis

CREATE TABLE canned_analysis (
	`id` INT AUTO_INCREMENT PRIMARY KEY
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
	`id` INT AUTO_INCREMENT PRIMARY KEY
);

CREATE TABLE canned_analysis_metadata (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`canned_analysis_fk` INT,
	`term_fk` INT,
	FOREIGN KEY (canned_analysis_fk) REFERENCES canned_analysis(id),
	FOREIGN KEY (term_fk) REFERENCES term(id)
);

CREATE TABLE user (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`username` VARCHAR(50) UNIQUE,
	`email` VARCHAR(50) UNIQUE,
	`password` VARCHAR(80)
);

