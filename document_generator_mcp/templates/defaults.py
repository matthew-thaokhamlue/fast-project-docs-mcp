"""
Default document templates for the MCP Document Generator.

This module contains the default templates for PRD, SPEC, and DESIGN documents
following Kiro's document creation best practices.
"""

from typing import Dict, Any
from ..models.core import Template


class DefaultTemplates:
    """Container for default document templates."""
    
    @staticmethod
    def get_prd_template() -> Template:
        """Get the default PRD template following Kiro's structure."""
        sections = {
            "frontmatter": """---
document_type: prd
version: "1.0"
author: "MCP Document Generator"
created_date: "{created_date}"
last_modified: "{last_modified}"
review_status: "draft"
---""",
            
            "introduction": """# {title}

## Introduction

{introduction_content}

This document outlines the product requirements for {project_name}, providing a comprehensive overview of the features, functionality, and constraints that will guide the development process.

## Project Context

{project_context}""",
            
            "objectives": """## Objectives

The primary objectives of this project are:

{objectives_list}

### Success Criteria

{success_criteria}""",
            
            "user_stories": """## Requirements

{user_stories_content}""",
            
            "acceptance_criteria": """## Acceptance Criteria

The following acceptance criteria must be met for successful completion:

{acceptance_criteria_list}""",
            
            "success_metrics": """## Success Metrics

{success_metrics_list}

### Key Performance Indicators (KPIs)

{kpi_list}""",
            
            "constraints": """## Constraints

### Technical Constraints

{technical_constraints}

### Business Constraints

{business_constraints}

### Timeline Constraints

{timeline_constraints}""",
            
            "assumptions": """## Assumptions

{assumptions_list}""",
            
            "dependencies": """## Dependencies

### Internal Dependencies

{internal_dependencies}

### External Dependencies

{external_dependencies}""",
            
            "appendix": """## Appendix

### Glossary

{glossary}

### References

{references}"""
        }
        
        return Template(
            name="default_prd",
            template_type="prd",
            sections=sections,
            metadata={
                "description": "Default PRD template following Kiro's best practices",
                "author": "MCP Document Generator",
                "supports_customization": True
            }
        )
    
    @staticmethod
    def get_spec_template() -> Template:
        """Get the default SPEC template following Kiro's structure."""
        sections = {
            "frontmatter": """---
document_type: spec
version: "1.0"
author: "MCP Document Generator"
created_date: "{created_date}"
last_modified: "{last_modified}"
review_status: "draft"
related_documents:
  - "{prd_document}"
---""",
            
            "overview": """# {title} - Technical Specification

## Overview

{overview_content}

This technical specification document provides detailed implementation guidance for {project_name}, building upon the requirements outlined in the Product Requirements Document.

## Scope

{scope_description}""",
            
            "architecture": """## Architecture

### System Architecture Pattern

{architecture_description}

```mermaid
{architecture_diagram}
```

### Design Principles

{design_principles}""",
            
            "components": """## Components and Interfaces

{components_description}

### Component Breakdown

{component_details}""",
            
            "interfaces": """## API Interfaces

{interfaces_description}

### Interface Specifications

{interface_details}""",
            
            "data_models": """## Data Models

{data_models_description}

### Data Structures

{data_structure_details}

### Data Relationships

```mermaid
{data_model_diagram}
```""",
            
            "implementation_details": """## Implementation Details

{implementation_description}

### Technology Stack

{technology_stack}

### Implementation Approach

{implementation_approach}""",
            
            "testing_strategy": """## Testing Strategy

{testing_description}

### Test Coverage Requirements

{test_coverage}

### Testing Approach

{testing_approach}""",
            
            "deployment": """## Deployment Considerations

{deployment_description}

### Infrastructure Requirements

{infrastructure_requirements}

### Deployment Pipeline

{deployment_pipeline}""",
            
            "appendix": """## Appendix

### Technical References

{technical_references}

### Configuration Examples

{configuration_examples}"""
        }
        
        return Template(
            name="default_spec",
            template_type="spec",
            sections=sections,
            metadata={
                "description": "Default SPEC template following Kiro's best practices",
                "author": "MCP Document Generator",
                "supports_customization": True,
                "requires_prd": True
            }
        )
    
    @staticmethod
    def get_design_template() -> Template:
        """Get the default DESIGN template following Kiro's structure."""
        sections = {
            "frontmatter": """---
document_type: design
version: "1.0"
author: "MCP Document Generator"
created_date: "{created_date}"
last_modified: "{last_modified}"
review_status: "draft"
related_documents:
  - "{prd_document}"
  - "{spec_document}"
---""",
            
            "system_design": """# {title} - Design Document

## System Design

{system_design_description}

### High-Level Design

{high_level_design}

### System Components

```mermaid
{system_diagram}
```""",
            
            "user_interface_design": """## User Interface Design

{ui_design_description}

### Design Principles

{ui_design_principles}

### User Experience Flow

```mermaid
{user_flow_diagram}
```

### Interface Specifications

{interface_specifications}""",
            
            "data_flow": """## Data Flow

{data_flow_description}

### Data Flow Diagram

```mermaid
{data_flow_diagram}
```

### Data Processing Pipeline

{data_processing_pipeline}""",
            
            "implementation_approach": """## Implementation Approach

{implementation_approach_description}

### Development Phases

{development_phases}

### Implementation Strategy

{implementation_strategy}""",
            
            "design_patterns": """## Design Patterns

{design_patterns_description}

### Recommended Patterns

{recommended_patterns}

### Pattern Implementation

{pattern_implementation}""",
            
            "constraints": """## Design Constraints

### Technical Constraints

{technical_constraints}

### Performance Constraints

{performance_constraints}

### Security Constraints

{security_constraints}""",
            
            "security_considerations": """## Security Considerations

{security_description}

### Security Requirements

{security_requirements}

### Security Implementation

{security_implementation}""",
            
            "performance_requirements": """## Performance Requirements

{performance_description}

### Performance Targets

{performance_targets}

### Optimization Strategy

{optimization_strategy}""",
            
            "appendix": """## Appendix

### Design Assets

{design_assets}

### Implementation Examples

{implementation_examples}

### References

{design_references}"""
        }
        
        return Template(
            name="default_design",
            template_type="design",
            sections=sections,
            metadata={
                "description": "Default DESIGN template following Kiro's best practices",
                "author": "MCP Document Generator",
                "supports_customization": True,
                "requires_spec": True
            }
        )
    
    @staticmethod
    def get_all_templates() -> Dict[str, Template]:
        """Get all default templates."""
        return {
            "prd": DefaultTemplates.get_prd_template(),
            "spec": DefaultTemplates.get_spec_template(),
            "design": DefaultTemplates.get_design_template()
        }
