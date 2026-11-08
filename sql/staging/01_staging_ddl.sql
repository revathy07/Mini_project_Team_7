-- 01_staging_ddl.sql: raw landing zone, one table per CSV, no FKs
DROP DATABASE IF EXISTS employee_staging;
CREATE DATABASE employee_staging CHARACTER SET utf8mb4;
USE employee_staging;

CREATE TABLE stg_departments (
  department_id    INT PRIMARY KEY,
  department_name  VARCHAR(100),
  location         VARCHAR(100),
  annual_budget    DECIMAL(14,2),
  cost_center      VARCHAR(20)
);

CREATE TABLE stg_employees (
  employee_id                 INT PRIMARY KEY,
  source_employee_number      INT,
  first_name                  VARCHAR(60),
  last_name                   VARCHAR(60),
  email                       VARCHAR(150),
  gender                      VARCHAR(10),
  age                         INT,
  marital_status              VARCHAR(20),
  education                   INT,
  education_field             VARCHAR(50),
  department_id               INT,
  job_role                    VARCHAR(50),
  job_level                   INT,
  monthly_income              DECIMAL(12,2),
  percent_salary_hike         INT,
  hire_date                   DATE,
  termination_date            DATE NULL,
  attrition                   TINYINT(1),
  manager_id                  INT NULL,
  business_travel             VARCHAR(30),
  overtime                    TINYINT(1),
  distance_from_home          INT,
  job_satisfaction            INT,
  environment_satisfaction    INT,
  work_life_balance           INT,
  job_involvement             INT,
  performance_rating          INT,
  stock_option_level          INT,
  training_times_last_year    INT,
  num_companies_worked        INT,
  total_working_years         INT,
  years_at_company            INT,
  years_in_current_role       INT,
  years_since_last_promotion  INT,
  years_with_curr_manager     INT
);

CREATE TABLE stg_projects (
  project_id        INT PRIMARY KEY,
  project_name      VARCHAR(150),
  department_id     INT,
  start_date        DATE,
  planned_end_date  DATE,
  end_date          DATE NULL,
  budget            DECIMAL(12,2),
  status            VARCHAR(20),
  priority          VARCHAR(10)
);

CREATE TABLE stg_project_assignments (
  assignment_id   INT PRIMARY KEY,
  employee_id     INT,
  project_id      INT,
  role            VARCHAR(30),
  allocation_pct  INT,
  assigned_date   DATE,
  released_date   DATE NULL
);

CREATE TABLE stg_performance_reviews (
  review_id              INT PRIMARY KEY,
  employee_id            INT,
  reviewer_id            INT NULL,
  review_date            DATE,
  review_cycle           VARCHAR(20),
  performance_score      DECIMAL(3,2),
  performance_rating     INT,
  goal_achievement_pct   DECIMAL(5,1),
  peer_feedback_score    DECIMAL(3,2),
  promotion_recommended  TINYINT(1)
);

CREATE TABLE stg_employee_changes (
  change_id             INT PRIMARY KEY,
  employee_id           INT,
  version_no            INT,
  change_type           VARCHAR(30),
  department_id         INT,
  job_role              VARCHAR(50),
  job_level             INT,
  monthly_income        DECIMAL(12,2),
  effective_start_date  DATE,
  effective_end_date    DATE NULL,
  is_current            TINYINT(1),
  KEY idx_chg_emp (employee_id, version_no)
);