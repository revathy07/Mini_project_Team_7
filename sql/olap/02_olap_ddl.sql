-- 02_olap_ddl.sql (OLAP Data Warehouse)

DROP DATABASE IF EXISTS employee_dw;
CREATE DATABASE employee_dw;
USE employee_dw;

CREATE TABLE Dim_Department (
  department_sk   INT AUTO_INCREMENT PRIMARY KEY,
  department_code VARCHAR(20) NOT NULL UNIQUE,
  department_name VARCHAR(100) NOT NULL,
  location        VARCHAR(100),
  budget          DECIMAL(14,2)
);

CREATE TABLE Dim_Employee (
  employee_sk     INT AUTO_INCREMENT PRIMARY KEY,
  employee_code   VARCHAR(20) NOT NULL,
  full_name       VARCHAR(100) NOT NULL,
  email           VARCHAR(100),
  department_name VARCHAR(100),
  job_role        VARCHAR(50),
  job_level       INT,
  monthly_income  DECIMAL(12,2),
  hire_date       DATE,
  attrition_flag  BOOLEAN DEFAULT FALSE,
  start_date      DATE NOT NULL,
  end_date        DATE NOT NULL DEFAULT '9999-12-31',
  is_current      BOOLEAN NOT NULL DEFAULT TRUE,
  
  -- Index for SCD2 logic
  INDEX idx_employee_current (employee_code, is_current),
  
  -- NEW INDEX: Speeds up the Fact table date-range joins
  INDEX idx_emp_scd_dates (employee_code, start_date, end_date) 
);

CREATE TABLE Dim_Project (
  project_sk        INT AUTO_INCREMENT PRIMARY KEY,
  project_code      VARCHAR(20) NOT NULL UNIQUE,
  project_name      VARCHAR(150) NOT NULL,
  department_name   VARCHAR(100),
  status            VARCHAR(20),
  priority          VARCHAR(10),
  start_date        DATE,
  planned_end_date  DATE,
  end_date          DATE,
  budget            DECIMAL(12,2)
);

CREATE TABLE Dim_Date (
  date_key    INT PRIMARY KEY,
  full_date   DATE NOT NULL UNIQUE,
  day_of_week VARCHAR(10),
  month_name  VARCHAR(10),
  quarter     INT,
  year        INT
);

CREATE TABLE Fact_PerformanceReviews (
  review_sk              INT AUTO_INCREMENT PRIMARY KEY,
  employee_sk            INT NOT NULL,
  department_sk          INT NOT NULL,
  date_key               INT NOT NULL,
  reviewer_employee_sk   INT,
  review_period          VARCHAR(20),
  performance_score      DECIMAL(3,2),
  performance_rating     INT,
  goal_achievement_pct   DECIMAL(5,1),
  peer_feedback_score    DECIMAL(3,2),
  promotion_recommended  BOOLEAN,
  INDEX idx_fact_emp (employee_sk),
  INDEX idx_fact_date (date_key),
  FOREIGN KEY (employee_sk)          REFERENCES Dim_Employee(employee_sk),
  FOREIGN KEY (department_sk)        REFERENCES Dim_Department(department_sk),
  FOREIGN KEY (date_key)             REFERENCES Dim_Date(date_key),
  FOREIGN KEY (reviewer_employee_sk) REFERENCES Dim_Employee(employee_sk)
);

CREATE TABLE Fact_ProjectAllocations (
  allocation_sk         INT AUTO_INCREMENT PRIMARY KEY,
  employee_sk           INT NOT NULL,
  project_sk            INT NOT NULL,
  date_key              INT NOT NULL,
  role_in_project       VARCHAR(50),
  allocation_percentage INT,
  FOREIGN KEY (employee_sk) REFERENCES Dim_Employee(employee_sk),
  FOREIGN KEY (project_sk)  REFERENCES Dim_Project(project_sk),
  FOREIGN KEY (date_key)    REFERENCES Dim_Date(date_key)
);