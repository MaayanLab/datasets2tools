DROP DATABASE IF EXISTS `datasets2tools`;
CREATE DATABASE `datasets2tools` DEFAULT CHARACTER SET utf8;
USE `datasets2tools`;

### User

CREATE TABLE user (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`username` VARCHAR(50) UNIQUE NOT NULL,
	`email` VARCHAR(50) UNIQUE NOT NULL,
	`password` VARCHAR(80),
	`max_contributions` INT DEFAULT 1000
);

### Dataset

CREATE TABLE repository (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`repository_name` VARCHAR(50) UNIQUE NOT NULL,
	`repository_homepage_url` TEXT,
	`repository_icon_url` TEXT
);

CREATE TABLE dataset (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`repository_fk` INT DEFAULT 3,
	`dataset_accession` VARCHAR(30) UNIQUE NOT NULL,
	`internal_dataset_accession` CHAR(11) GENERATED ALWAYS AS(CONCAT('DDS', LPAD(id, 8, 0))),
	`dataset_title` TEXT,
	`dataset_description` TEXT,
	`dataset_landing_url` TEXT,
	`dataset_type` VARCHAR(50),
	FOREIGN KEY (repository_fk) REFERENCES repository(id)
);

CREATE TABLE related_dataset (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`source_dataset_fk` INT NOT NULL,
	`target_dataset_fk` INT NOT NULL,
	`similarity` DOUBLE,
	FOREIGN KEY (source_dataset_fk) REFERENCES dataset(id),
	FOREIGN KEY (target_dataset_fk) REFERENCES dataset(id),
	UNIQUE INDEX `unique_related_dataset` (source_dataset_fk, target_dataset_fk)
);

CREATE TABLE dataset_keyword (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`dataset_fk` INT DEFAULT NULL,
	`keyword` VARCHAR(255),
	FOREIGN KEY (dataset_fk) REFERENCES dataset(id),
	UNIQUE INDEX `unique_dataset_keyword` (dataset_fk, keyword)
);

### Tool

CREATE TABLE tool (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`tool_name` VARCHAR(100) UNIQUE NOT NULL,
	`tool_accession` CHAR(11) GENERATED ALWAYS AS(CONCAT('DCT', LPAD(id, 8, 0))),
	`tool_description` TEXT,
	`tool_homepage_url` TEXT NOT NULL,#VARCHAR(255) UNIQUE NOT NULL,
	`tool_icon_url` VARCHAR(255) DEFAULT 'static/icons/tool.png',
	`display` BOOL DEFAULT TRUE
);

CREATE TABLE related_tool (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`source_tool_fk` INT NOT NULL,
	`target_tool_fk` INT NOT NULL,
	`similarity` DOUBLE,
	FOREIGN KEY (source_tool_fk) REFERENCES tool(id),
	FOREIGN KEY (target_tool_fk) REFERENCES tool(id),
	UNIQUE INDEX `unique_related_tool` (source_tool_fk, target_tool_fk)
);

CREATE TABLE tool_keyword (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`tool_fk` INT DEFAULT NULL,
	`keyword` VARCHAR(255),
	FOREIGN KEY (tool_fk) REFERENCES tool(id),
	UNIQUE INDEX `unique_tool_keyword` (tool_fk, keyword)
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

CREATE TABLE article_metrics (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`article_fk` INT,
	`altmetric_badge_url` VARCHAR(255),
	`attention_percentile` INT,
	`attention_score` DOUBLE,
	`citations` INT,
	FOREIGN KEY (article_fk) REFERENCES article(id)
);

### Contribution

CREATE TABLE contribution (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`user_fk` INT DEFAULT NULL,
	`date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	`display` BOOL DEFAULT 0,
	FOREIGN KEY (user_fk) REFERENCES user(id)
);

### Canned analysis

CREATE TABLE canned_analysis (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`canned_analysis_accession` CHAR(11) GENERATED ALWAYS AS(CONCAT('DCA', LPAD(id, 8, 0))),
	`canned_analysis_title` VARCHAR(255),
	`canned_analysis_description` TEXT,
	`canned_analysis_url` VARCHAR(255) UNIQUE NOT NULL,
	`canned_analysis_preview_url` VARCHAR(255) DEFAULT 'static/icons/analysis_preview.png',
	`contribution_fk` INT NOT NULL,
	`date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (contribution_fk) REFERENCES contribution(id)
);

CREATE TABLE related_canned_analysis (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`source_canned_analysis_fk` INT NOT NULL,
	`target_canned_analysis_fk` INT NOT NULL,
	`similarity` DOUBLE,
	FOREIGN KEY (source_canned_analysis_fk) REFERENCES canned_analysis(id),
	FOREIGN KEY (target_canned_analysis_fk) REFERENCES canned_analysis(id),
	UNIQUE INDEX `unique_related_canned_analysis` (source_canned_analysis_fk, target_canned_analysis_fk)
);

CREATE TABLE canned_analysis_keyword (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`canned_analysis_fk` INT DEFAULT NULL,
	`keyword` VARCHAR(255),
	FOREIGN KEY (canned_analysis_fk) REFERENCES canned_analysis(id),
	UNIQUE INDEX `unique_canned_analysis_keyword` (canned_analysis_fk, keyword)
);

CREATE TABLE analysis_to_dataset (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`canned_analysis_fk` INT,
	`dataset_fk` INT,
	FOREIGN KEY (canned_analysis_fk) REFERENCES canned_analysis(id),
	FOREIGN KEY (dataset_fk) REFERENCES dataset(id),
	UNIQUE INDEX `unique_analysis_dataset` (canned_analysis_fk, dataset_fk)
);

CREATE TABLE analysis_to_tool (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`canned_analysis_fk` INT,
	`tool_fk` INT,
	FOREIGN KEY (canned_analysis_fk) REFERENCES canned_analysis(id),
	FOREIGN KEY (tool_fk) REFERENCES tool(id),
	UNIQUE INDEX `unique_analysis_tool` (canned_analysis_fk, tool_fk)
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
	`value` VARCHAR(255),
	FOREIGN KEY (canned_analysis_fk) REFERENCES canned_analysis(id),
	FOREIGN KEY (term_fk) REFERENCES term(id),
	UNIQUE INDEX `unique_canned_analysis_metadata` (canned_analysis_fk, term_fk, value)
);

### Evaluations

CREATE TABLE question (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`question_number` INT NOT NULL,
	`question` TEXT NOT NULL,
	`object_type` ENUM('dataset', 'tool', 'canned_analysis')
);

CREATE TABLE dataset_evaluation (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`user_fk` INT NOT NULL,
	`dataset_fk` INT DEFAULT NULL,
	`question_fk` INT NOT NULL,
	`answer` VARCHAR(10),
	`comment` TEXT,
	FOREIGN KEY (user_fk) REFERENCES user(id),
	FOREIGN KEY (dataset_fk) REFERENCES dataset(id),
	FOREIGN KEY (question_fk) REFERENCES question(id),
	UNIQUE INDEX `unique_dataset_evaluation` (user_fk, dataset_fk, question_fk)
);

CREATE TABLE tool_evaluation (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`user_fk` INT NOT NULL,
	`tool_fk` INT DEFAULT NULL,
	`question_fk` INT NOT NULL,
	`answer` VARCHAR(10),
	`comment` TEXT,
	FOREIGN KEY (user_fk) REFERENCES user(id),
	FOREIGN KEY (tool_fk) REFERENCES tool(id),
	FOREIGN KEY (question_fk) REFERENCES question(id),
	UNIQUE INDEX `unique_tool_evaluation` (user_fk, tool_fk, question_fk)
);

CREATE TABLE canned_analysis_evaluation (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`user_fk` INT NOT NULL,
	`canned_analysis_fk` INT DEFAULT NULL,
	`question_fk` INT NOT NULL,
	`answer` VARCHAR(10),
	`comment` TEXT,
	FOREIGN KEY (user_fk) REFERENCES user(id),
	FOREIGN KEY (canned_analysis_fk) REFERENCES canned_analysis(id),
	FOREIGN KEY (question_fk) REFERENCES question(id),
	UNIQUE INDEX `unique_canned_analysis_evaluation` (user_fk, canned_analysis_fk, question_fk)
);

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
	(1, "Standardized IDs are used to identify dataset.", "dataset"),
	(2, "The dataset can be located on the host platform via free-text search and menu-driven decision tree search.", "dataset"),
	(3, "The dataset is hosted in one or more well-used repositories, if relevant repositories exist.", "dataset"),
	(4, "(Meta)data are assigned a globally unique and eternally persistent identifier.", "dataset"),
	(5, "The dataset is retrievable by a standardized protocol.", "dataset"),
	(6, "The dataset is available in a human-readable format.", "dataset"),
	(7, "The dataset is available in a standard machine-accessible format (that is interoperable with popular analysis tools).", "dataset"),
	(8, "The meta(data) are sufficiently complete to permit effective reuse.", "dataset"),
	(9, "Metadata are linked to other relevant datasets, vocabularies and ontologies.", "dataset"),
	(1, "The structure of the repository permits efficient discovery of data and metadata by end users.", "canned_analysis"),
	(2, "The repository is available online.", "canned_analysis"),
	(3, "The repository uses a standardized protocol to permit access by users.", "canned_analysis"),
	(4, "The repository provides a tutorial that describes detailed usage guidelines.", "canned_analysis"),
	(5, "The repository provides a Frequently Asked Questions (FAQ) page and/or user forum as a resource for users.", "canned_analysis"),
	(6, "The repository provides contact information for staff to enable users with questions or suggestions to interact with repository experts.", "canned_analysis"),
	(7, "The repository is established on standard core infrastructure components including hardware, operating systems, and supporting software.", "canned_analysis"),
	(8, "Tools that can be used to analyze each dataset are listed on the corresponding dataset pages.", "canned_analysis"),
	(9, "The repository maintains licenses to manage data access and use.", "canned_analysis");

# Terms
INSERT INTO term (term_name) VALUES
	('organism'),
	('geneset'),
	('direction');

# Contribution
INSERT INTO contribution (id) VALUES
	(1);

# Canned Analysis
INSERT INTO canned_analysis (canned_analysis_title, canned_analysis_description, canned_analysis_url, contribution_fk) VALUES
	('', '', '', 1);
