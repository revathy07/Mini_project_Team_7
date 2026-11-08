-- 01_oltp_ddl.sql (OLTP Backend)

DROP DATABASE IF EXISTS employee_oltp;
CREATE DATABASE employee_oltp;
USE employee_oltp;

CREATE TABLE Departments (
  department_id    INT AUTO_INCREMENT PRIMARY KEY,
  department_code  VARCHAR(20) UNIQUE NOT NULL,
  department_name  VARCHAR(100) NOT NULL,
  location         VARCHAR(100),
  budget           DECIMAL(14,2),
  manager_id       INT NULL
);

CREATE TABLE Employees (
  employee_id      INT AUTO_INCREMENT PRIMARY KEY,
  employee_code    VARCHAR(20) UNIQUE NOT NULL,
  first_name       VARCHAR(50) NOT NULL,
  last_name        VARCHAR(50) NOT NULL,
  email            VARCHAR(100) UNIQUE NOT NULL,
  hire_date        DATE NOT NULL,
  department_id    INT,
  job_role         VARCHAR(50) NOT NULL,
  job_level        INT,
  monthly_income   DECIMAL(12,2) NOT NULL,
  manager_id       INT NULL,
  attrition        BOOLEAN DEFAULT FALSE,
  status           VARCHAR(20) DEFAULT 'Active',
  updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (department_id) REFERENCES Departments(department_id),
  FOREIGN KEY (manager_id)    REFERENCES Employees(employee_id)
);

-- Add the circular FK for Departments manager_id AFTER Employees table exists
ALTER TABLE Departments 
ADD FOREIGN KEY (manager_id) REFERENCES Employees(employee_id);

CREATE TABLE Projects (
  project_id          INT AUTO_INCREMENT PRIMARY KEY,
  project_code        VARCHAR(20) UNIQUE NOT NULL,
  project_name        VARCHAR(150) NOT NULL,
  department_id       INT,
  project_manager_id  INT,
  start_date          DATE NOT NULL,
  end_date            DATE,
  status              VARCHAR(20) DEFAULT 'Active',
  FOREIGN KEY (department_id)      REFERENCES Departments(department_id),
  FOREIGN KEY (project_manager_id) REFERENCES Employees(employee_id)
);

CREATE TABLE Project_Assignments (
  assignment_id         INT AUTO_INCREMENT PRIMARY KEY,
  employee_id           INT NOT NULL,
  project_id            INT NOT NULL,
  role_in_project       VARCHAR(50),
  allocation_percentage INT,
  start_date            DATE NOT NULL,
  end_date              DATE,
  status                VARCHAR(20) DEFAULT 'Active',
  UNIQUE KEY uk_assign (employee_id, project_id, start_date),
  FOREIGN KEY (employee_id) REFERENCES Employees(employee_id),
  FOREIGN KEY (project_id)  REFERENCES Projects(project_id)
);

CREATE TABLE Performance_Reviews (
  review_id            INT AUTO_INCREMENT PRIMARY KEY,
  employee_id          INT NOT NULL,
  reviewer_id          INT,
  review_date          DATE NOT NULL,
  review_period        VARCHAR(20) NOT NULL,
  performance_rating   INT,
  job_satisfaction     INT,
  work_life_balance    INT,
  percent_salary_hike  DECIMAL(5,2),
  comments             TEXT,
  UNIQUE KEY uk_review (employee_id, review_period),
  FOREIGN KEY (employee_id) REFERENCES Employees(employee_id),
  FOREIGN KEY (reviewer_id) REFERENCES Employees(employee_id)
);

CREATE TABLE Employee_Change_Log (
  change_id    INT AUTO_INCREMENT PRIMARY KEY,
  employee_id  INT NOT NULL,
  change_date  DATE NOT NULL,
  change_type  VARCHAR(30),
  field_name   VARCHAR(50),
  old_value    VARCHAR(100),
  new_value    VARCHAR(100),
  FOREIGN KEY (employee_id) REFERENCES Employees(employee_id)
);