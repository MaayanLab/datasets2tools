DROP DATABASE IF EXISTS `datasets2tools`;
CREATE DATABASE `datasets2tools` DEFAULT CHARACTER SET utf8;
USE `datasets2tools`;

### Dataset

CREATE TABLE repository (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`repository_name` VARCHAR(50) UNIQUE NOT NULL,
	`repository_homepage_url` TEXT,
	`repository_icon_url` TEXT
);

CREATE TABLE dataset_type (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`dataset_type_name` VARCHAR(50),
	`dataset_type_icon_url` TEXT
);

CREATE TABLE dataset (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`repository_fk` INT DEFAULT 3,
	`dataset_type_fk` INT,
	`dataset_accession` VARCHAR(30) UNIQUE NOT NULL,
	`dataset_title` VARCHAR(255),
	`dataset_description` TEXT,
	`dataset_landing_url` TEXT,
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
	`tool_name` VARCHAR(100) UNIQUE NOT NULL,
	`tool_description` TEXT,
	`tool_homepage_url` TEXT,
	`tool_icon_url` TEXT
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
	`journal_name` VARCHAR(50) UNIQUE NOT NULL,
	`journal_description` TEXT,
	`journal_homepage_url` TEXT
);

CREATE TABLE article (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`journal_fk` INT,
	`tool_fk` INT,
	`article_title` TEXT,
	`abstract` TEXT,
	`authors` TEXT,
	`date` DATE,
	`doi` VARCHAR(255) UNIQUE NOT NULL,
	FOREIGN KEY (journal_fk) REFERENCES journal(id),
	FOREIGN KEY (tool_fk) REFERENCES tool(id)
);

### Canned analysis

CREATE TABLE canned_analysis (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`canned_analysis_accession` CHAR(11) GENERATED ALWAYS AS(CONCAT('DCA', LPAD(id, 8, 0))),
	`canned_analysis_title` VARCHAR(255),
	`canned_analysis_description` TEXT,
	`canned_analysis_url` VARCHAR(255) UNIQUE NOT NULL,
	`canned_analysis_preview_url` TEXT
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
	`term_name` VARCHAR(50) UNIQUE NOT NULL,
	`term_description` TEXT
);

CREATE TABLE canned_analysis_metadata (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`canned_analysis_fk` INT,
	`term_fk` INT,
	`value` TEXT,
	FOREIGN KEY (canned_analysis_fk) REFERENCES canned_analysis(id),
	FOREIGN KEY (term_fk) REFERENCES term(id)
);

### Keywords

CREATE TABLE keyword (
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
	`username` VARCHAR(50) UNIQUE NOT NULL,
	`email` VARCHAR(50) UNIQUE NOT NULL,
	`password` VARCHAR(80)
);

### Evaluations

CREATE TABLE question (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`question_number` INT NOT NULL,
	`question` TEXT NOT NULL,
	`object_type` ENUM('dataset', 'tool', 'canned_analysis')
);

CREATE TABLE evaluation (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`user_fk` INT NOT NULL,
	`question_fk` INT NOT NULL,
	`score` INT,
	`comment` TEXT,
	`dataset_fk` INT DEFAULT NULL,
	`tool_fk` INT DEFAULT NULL,
	`canned_analysis_fk` INT DEFAULT NULL,
	FOREIGN KEY (dataset_fk) REFERENCES dataset(id),
	FOREIGN KEY (tool_fk) REFERENCES tool(id),
	FOREIGN KEY (canned_analysis_fk) REFERENCES canned_analysis(id),
	FOREIGN KEY (question_fk) REFERENCES question(id),
	FOREIGN KEY (user_fk) REFERENCES user(id),
	UNIQUE KEY (user_fk, question_fk, dataset_fk, tool_fk, canned_analysis_fk)
);

-- CREATE TABLE question_answer (
-- 	`id` INT AUTO_INCREMENT PRIMARY KEY,
-- 	`question_fk` INT NOT NULL,
-- 	`evaluation_fk` INT NOT NULL,
-- 	`score` INT,
-- 	`comment` TEXT,
-- 	FOREIGN KEY (question_fk) REFERENCES question(id),
-- 	FOREIGN KEY (evaluation_fk) REFERENCES evaluation(id),
-- 	UNIQUE KEY (question_fk, evaluation_fk)
-- );


### Add Data

# Repositories
INSERT INTO repository (repository_name, repository_homepage_url, repository_icon_url) VALUES
	('Gene Expression Omnibus', 'https://www.ncbi.nlm.nih.gov/geo/', 'https://www.ncbi.nlm.nih.gov/geo/img/geo_main.gif'),
	('LINCS Data Portal', 'http://lincsportal.ccs.miami.edu/dcic-portal/', 'http://lincsportal.ccs.miami.edu/dcic-portal/images/ldp_logo.png'),
	('Unspecified', '#', '#');

# Journals
INSERT INTO journal (journal_name) VALUES
	('Bioinformatics'),
	('Database'),
	('Nucleic Acids Research'),
	('BMC Bioinformatics');

# Questions
INSERT INTO question (question_number, question, object_type) VALUES
	(1, "The tool is hosted in one or more well-used repositories, if relevant repositories exist.", "tool"),
	(2, "Source code is shared on a public repository.", "tool"),
	(3, "Code is written in an open-source, free programming language.", "tool"),
	(4, "The tool inputs standard data format(s) consistent with community practice.", "tool"),
	(5, "All previous versions of the tool are made available.", "tool"),
	(6, "Web-based version is available (in addition to desktop version).", "tool"),
	(7, "Source code is documented.", "tool"),
	(8, "Pipelines that use the tool have been standardized and provide detailed usage guidelines.", "tool"),
	(9, "A tutorial page is provided for the tool.", "tool"),
	(10, "Example datasets are provided.", "tool"),
	(11, "Licensing information is provided on the tool's landing page.", "tool"),
	(12, "Information is provided describing how to cite the tool.", "tool"),
	(13, "Version information is provided for the tool.", "tool"),
	(14, "A paper about the tool has been published.", "tool"),
	(15, "Video tutorials for the tool are available.", "tool"),
	(16, "Contact information is provided for the originator(s) of the tool.", "tool"),
	(1, "Standardized IDs are used to identify dataset.", "dataset"),
	(2, "The dataset can be located on the host platform via free-text search and menu-driven decision tree search.", "dataset"),
	(3, "The dataset is hosted in one or more well-used repositories, if relevant repositories exist.", "dataset"),
	(4, "(Meta)data are assigned a globally unique and eternally persistent identifier.", "dataset"),
	(5, "The dataset is retrievable by a standardized protocol.", "dataset"),
	(6, "The dataset is available in a human-readable format.", "dataset"),
	(7, "The dataset is available in a standard machine-accessible format (that is interoperable with popular analysis tools).", "dataset"),
	(8, "The meta(data) are sufficiently complete to permit effective reuse.", "dataset"),
	(9, "Metadata are linked to other relevant datasets, vocabularies and ontologies.", "dataset"),
	(10, "A tutorial page is provided for the dataset to describe the format of the dataset.", "dataset"),
	(11, "Information is provided describing how to cite the dataset.", "dataset"),
	(12, "A description of the methods used to acquire the data is provided.", "dataset"),
	(13, "Licensing information is provided on the dataset's landing page.", "dataset"),
	(14, "Version information is provided on the dataset's landing page.", "dataset"),
	(15, "Tools that can be used to analyze the dataset are listed on the dataset's landing page.", "dataset"),
	(16, "Contact information is provided for the originator(s) of the dataset.", "dataset"),
	(1, "The structure of the repository permits efficient discovery of data and metadata by end users.", "canned_analysis"),
	(2, "The repository is available online.", "canned_analysis"),
	(3, "The repository uses a standardized protocol to permit access by users.", "canned_analysis"),
	(4, "The repository provides a tutorial that describes detailed usage guidelines.", "canned_analysis"),
	(5, "The repository provides a Frequently Asked Questions (FAQ) page and/or user forum as a resource for users.", "canned_analysis"),
	(6, "The repository provides contact information for staff to enable users with questions or suggestions to interact with repository experts.", "canned_analysis"),
	(7, "The repository is established on standard core infrastructure components including hardware, operating systems, and supporting software.", "canned_analysis"),
	(8, "Tools that can be used to analyze each dataset are listed on the corresponding dataset pages.", "canned_analysis"),
	(9, "The repository maintains licenses to manage data access and use.", "canned_analysis"),
	(10, "The repository hosts data and metadata according to a set of defined criteria to ensure that the resources provided are consistent with the intent of the repository.", "canned_analysis"),
	(11, "The repository provides sufficient detail about its data and metadata so that users are able to evaluate the quality of these resources.", "canned_analysis"),
	(12, "Metadata are linked to other relevant datasets, vocabularies and ontologies.", "canned_analysis"),
	(13, "The repository provides documentation for each resource to permit its complete and accurate citation.", "canned_analysis"),
	(14, "Sufficient metadata are provided for each dataset to permit accurate and useful employment of the dataset.", "canned_analysis"),
	(15, "A description of the methods used to acquire the data is provided.", "canned_analysis"),
	(16, "Version information is provided for each resource, where available.", "canned_analysis");

