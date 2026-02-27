# Requirements Document

## Introduction

This document specifies requirements for improving the reliability of AI-based answer key extraction in an OMR (Optical Mark Recognition) evaluation system and setting up a GitHub repository for the project. The system currently uses Ollama with the moondream vision model to extract answer keys from question paper images, but experiences failures when the AI cannot extract answers. The system also needs to be uploaded to GitHub as a public repository.

## Glossary

- **Extraction_System**: The AI-based component that extracts answer keys from question paper images using Ollama moondream vision model
- **Answer_Key**: A mapping of question numbers to correct answer letters (A, B, C, D, or E)
- **Question_Paper_Image**: An image or PDF file containing questions and their correct answers
- **Extraction_Pass**: One attempt by the AI model to extract answer keys using a specific prompt strategy
- **Fallback_Strategy**: Alternative extraction method used when primary extraction fails
- **Extraction_Result**: The output from the Extraction_System containing question-answer pairs
- **GitHub_Repository**: A public code repository hosted on GitHub under username "Jagadeesh-Surendran"
- **Backend_API**: Flask-based REST API that handles extraction requests at /api/extract_key endpoint
- **Frontend_Client**: HTML/JavaScript application that displays extraction results and errors to users
- **Validation_Check**: Process to verify extracted answer keys meet quality criteria before returning results

## Requirements

### Requirement 1: Enhanced Answer Key Extraction Reliability

**User Story:** As a teacher using the OMR system, I want the AI to reliably extract answer keys from question paper images, so that I can quickly grade student exams without manual data entry.

#### Acceptance Criteria

1. WHEN a Question_Paper_Image is provided to the Extraction_System, THE Extraction_System SHALL attempt extraction using at least three different Fallback_Strategy approaches
2. WHEN the first Extraction_Pass fails to produce valid results, THE Extraction_System SHALL automatically retry with alternative prompt strategies
3. THE Extraction_System SHALL validate that each extracted Answer_Key contains at least one question-answer pair before returning success
4. WHEN all Extraction_Pass attempts fail, THE Extraction_System SHALL return a descriptive error message indicating the failure reason
5. THE Extraction_System SHALL log all extraction attempts and results to a debug log file for troubleshooting

### Requirement 2: Image Preprocessing for Improved Extraction

**User Story:** As a teacher, I want the system to automatically enhance poor quality images, so that answer keys can be extracted even from photos taken with mobile phones.

#### Acceptance Criteria

1. WHEN a Question_Paper_Image is received, THE Extraction_System SHALL apply image preprocessing before AI extraction
2. THE Extraction_System SHALL enhance image contrast and brightness to improve text visibility
3. THE Extraction_System SHALL resize images to optimal dimensions for the vision model
4. WHEN a PDF file is provided, THE Extraction_System SHALL convert it to high-resolution image format (minimum 200 DPI)
5. THE Extraction_System SHALL preserve the original image and only process a temporary copy

### Requirement 3: Extraction Result Validation

**User Story:** As a system administrator, I want extracted answer keys to be validated for correctness, so that invalid or incomplete extractions are caught before grading begins.

#### Acceptance Criteria

1. THE Extraction_System SHALL verify that all question numbers in the Extraction_Result are positive integers
2. THE Extraction_System SHALL verify that all answer values are single letters from the set {A, B, C, D, E}
3. WHEN an Extraction_Result contains fewer than 5 question-answer pairs, THE Extraction_System SHALL log a warning
4. THE Extraction_System SHALL remove duplicate question numbers, keeping only the first occurrence
5. THE Extraction_System SHALL return the count of successfully extracted question-answer pairs

### Requirement 4: Improved Error Reporting

**User Story:** As a teacher, I want clear error messages when extraction fails, so that I understand what went wrong and how to fix it.

#### Acceptance Criteria

1. WHEN extraction fails due to poor image quality, THE Backend_API SHALL return an error message suggesting image quality improvements
2. WHEN extraction fails due to no answers found, THE Backend_API SHALL return an error message with specific formatting requirements
3. THE Frontend_Client SHALL display extraction error messages in a user-friendly format with actionable guidance
4. WHEN extraction produces zero results, THE Backend_API SHALL return HTTP status code 422 with detailed error information
5. THE Backend_API SHALL distinguish between file errors (404), extraction errors (422), and server errors (500)

### Requirement 5: Alternative Vision Model Support

**User Story:** As a system administrator, I want the ability to use alternative AI vision models, so that I can improve extraction accuracy if moondream fails.

#### Acceptance Criteria

1. THE Extraction_System SHALL support configuration of alternative vision models through a configuration parameter
2. WHEN the primary vision model fails, THE Extraction_System SHALL optionally attempt extraction with a fallback model
3. THE Extraction_System SHALL log which vision model was used for each extraction attempt
4. WHERE a fallback model is configured, THE Extraction_System SHALL automatically use it after primary model failure
5. THE Extraction_System SHALL support at least two different vision model options

### Requirement 6: Extraction Performance Monitoring

**User Story:** As a system administrator, I want to monitor extraction success rates, so that I can identify when the AI model needs improvement or replacement.

#### Acceptance Criteria

1. THE Extraction_System SHALL record the success or failure status of each extraction attempt
2. THE Extraction_System SHALL record the processing time for each extraction attempt
3. THE Extraction_System SHALL record which Extraction_Pass strategy succeeded for successful extractions
4. THE Extraction_System SHALL maintain extraction statistics in the debug log file
5. THE Extraction_System SHALL include timestamp information for all logged extraction attempts

### Requirement 7: GitHub Repository Setup

**User Story:** As a developer, I want the project uploaded to GitHub, so that I can share the code and collaborate with others.

#### Acceptance Criteria

1. THE GitHub_Repository SHALL be created under the username "Jagadeesh-Surendran"
2. THE GitHub_Repository SHALL be configured as a public repository
3. THE GitHub_Repository SHALL contain all project source code including backend and frontend components
4. THE GitHub_Repository SHALL include a README.md file with project description and setup instructions
5. THE GitHub_Repository SHALL include a .gitignore file to exclude virtual environments, temporary files, and sensitive data

### Requirement 8: Repository Documentation

**User Story:** As a new developer, I want clear documentation in the repository, so that I can understand and run the project locally.

#### Acceptance Criteria

1. THE GitHub_Repository SHALL include a README.md file describing the project purpose and features
2. THE README.md file SHALL include installation instructions for all dependencies
3. THE README.md file SHALL include instructions for running the backend Flask server
4. THE README.md file SHALL include instructions for accessing the frontend application
5. THE README.md file SHALL include information about the Ollama setup and required models

### Requirement 9: Repository Structure Organization

**User Story:** As a developer, I want a well-organized repository structure, so that I can easily navigate and understand the codebase.

#### Acceptance Criteria

1. THE GitHub_Repository SHALL maintain the existing directory structure with backend and frontend folders
2. THE GitHub_Repository SHALL include a requirements.txt file listing all Python dependencies
3. THE GitHub_Repository SHALL exclude large binary files and model weights from version control
4. THE GitHub_Repository SHALL exclude temporary upload directories and debug output files
5. THE GitHub_Repository SHALL include license information if applicable

### Requirement 10: Extraction Retry Configuration

**User Story:** As a system administrator, I want to configure extraction retry behavior, so that I can balance between accuracy and performance.

#### Acceptance Criteria

1. THE Extraction_System SHALL support configuration of the maximum number of Extraction_Pass attempts
2. THE Extraction_System SHALL support configuration of timeout values for each extraction attempt
3. WHERE retry configuration is provided, THE Extraction_System SHALL respect the configured limits
4. THE Extraction_System SHALL use sensible default values when no configuration is provided
5. THE Extraction_System SHALL log when extraction attempts are skipped due to timeout or retry limits
