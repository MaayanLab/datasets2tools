############################################################
############################################################
############### Datasets2Tools Schema Definition ###########
############################################################
############################################################

#######################################################
########## 1. Create Tables ###########################
#######################################################

##############################
##### 1.1 Create Database
##############################

# 1. Create and Use
DROP DATABASE IF EXISTS `datasets2tools`;
CREATE DATABASE `datasets2tools` DEFAULT CHARACTER SET utf8;
USE `datasets2tools`;

#######################################################
########## 2. Create Tables ###########################
#######################################################

##############################
##### 2.1 Repository
##############################

CREATE TABLE `repository` (
	# Fields
	`id` INT AUTO_INCREMENT PRIMARY KEY#,
	-- `name` VARCHAR(100) NOT NULL UNIQUE,
	-- `homepage_url` VARCHAR(100) DEFAULT '',
	-- `icon_url` VARCHAR(100) DEFAULT '',
	-- `description` TEXT,
	-- `screenshot_url` VARCHAR(150) DEFAULT '',
	-- `date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

##############################
##### 2.2 Dataset
##############################

CREATE TABLE `dataset` (
	# Fields
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`repository_fk` INT DEFAULT NULL#,
	-- `accession` VARCHAR(30) NOT NULL UNIQUE,
	-- `landing_url` VARCHAR(100) DEFAULT '',
	-- `title` TEXT,
	-- `description` TEXT,
	-- `date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

	# Foreign keys
	FOREIGN KEY (repository_fk)
		REFERENCES repository(id)
		ON DELETE RESTRICT
);

##############################
##### 2.3 Tool
##############################

CREATE TABLE `tool` (
	# Fields
	`id` INT AUTO_INCREMENT PRIMARY KEY#,
	-- `name` VARCHAR(30) NOT NULL UNIQUE,
	-- `icon_url` VARCHAR(100) DEFAULT '',
	-- `homepage_url` VARCHAR(150) DEFAULT '',
	-- `description` TEXT,
	-- `screenshot_url` VARCHAR(150) DEFAULT '',
	-- `date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

##############################
##### 2.4 Canned Analysis
##############################

CREATE TABLE `canned_analysis` (
	# Fields
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	-- `canned_analysis_accession` CHAR(10) GENERATED ALWAYS AS(CONCAT('CA', LPAD(id, 8, 0))),
	-- `canned_analysis_title` VARCHAR(300) NOT NULL,
	-- `canned_analysis_description` TEXT NOT NULL,
	-- `canned_analysis_url` VARCHAR(255) NOT NULL UNIQUE,
	-- `canned_analysis_preview_url` VARCHAR(150) NOT NULL,
	-- `dataset_fk` INT NOT NULL,
	-- `tool_fk` INT NOT NULL,
	-- `date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

##############################
##### 2.5 Terms
##############################

CREATE TABLE `term` (
	# Fields
	`id` INT AUTO_INCREMENT PRIMARY KEY#,
	-- `term_name` VARCHAR(50) NOT NULL,
	-- `term_description` VARCHAR(200) DEFAULT ''
);

##############################
##### 2.8 Canned Analysis Metadata
##############################

CREATE TABLE `canned_analysis_metadata` (
	# Fields
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`canned_analysis_fk` INT NOT NULL,
	`term_fk` INT NOT NULL,
	-- `value` TEXT NOT NULL,

	# Foreign keys
	FOREIGN KEY (canned_analysis_fk)
		REFERENCES canned_analysis(id)
		ON DELETE RESTRICT,

	FOREIGN KEY (term_fk)
		REFERENCES term(id)
		ON DELETE RESTRICT
);
