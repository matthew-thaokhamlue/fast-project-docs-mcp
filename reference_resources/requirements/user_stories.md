# Example User Stories for Task Management Application

## Core User Stories

### User Authentication
- As a team member, I want to create an account with email and password, so that I can access the task management system
- As a user, I want to log in securely, so that my tasks and data are protected
- As a user, I want to reset my password if I forget it, so that I can regain access to my account

### Task Management
- As a team member, I want to create new tasks with titles and descriptions, so that I can track work items
- As a task owner, I want to set due dates and priorities, so that I can manage my workload effectively
- As a team member, I want to assign tasks to other team members, so that work can be distributed
- As a user, I want to mark tasks as complete, so that I can track progress

### Team Collaboration
- As a team lead, I want to create project workspaces, so that tasks can be organized by project
- As a team member, I want to comment on tasks, so that I can communicate with colleagues
- As a user, I want to receive notifications about task updates, so that I stay informed
- As a team member, I want to view team dashboards, so that I can see overall project progress

## Acceptance Criteria

### Task Creation
- WHEN a user creates a task THEN the system SHALL save the task with a unique ID
- WHEN a task is created THEN the system SHALL set the creator as the default assignee
- IF a due date is set THEN the system SHALL validate it is not in the past

### User Management
- WHEN a user registers THEN the system SHALL validate the email format
- WHEN a user logs in THEN the system SHALL verify credentials against the database
- IF login fails THEN the system SHALL show an appropriate error message

### Notifications
- WHEN a task is assigned THEN the system SHALL notify the assignee
- WHEN a task is completed THEN the system SHALL notify relevant team members
- IF notifications fail THEN the system SHALL log the error and continue operation
