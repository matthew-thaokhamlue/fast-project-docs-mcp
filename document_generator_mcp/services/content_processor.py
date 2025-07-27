"""
Content processor for the MCP Document Generator.

This service handles content generation, template rendering, and document formatting
following Kiro's document creation patterns and best practices.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
import re
from datetime import datetime

from ..models.core import (
    ProcessingContext,
    ResourceAnalysis,
    Template,
    ValidationResult,
    PromptResult,
    ContentValidationResult
)
from ..models.document_structures import PRDStructure, SPECStructure, DESIGNStructure, DocumentMetadata
from ..templates.manager import TemplateManager
from ..exceptions import ContentGenerationError, ValidationError


logger = logging.getLogger(__name__)


class ContentProcessor:
    """Service for processing and generating document content."""
    
    def __init__(self, template_manager: Optional[TemplateManager] = None):
        """Initialize the content processor."""
        self.template_manager = template_manager or TemplateManager()
        
        # Content generation patterns
        self.user_story_patterns = [
            r"as\s+(?:a|an)\s+([^,]+),?\s+i\s+want\s+([^,]+),?\s+so\s+that\s+(.+)",
            r"user\s+story:?\s*(.+)",
            r"story:?\s*(.+)"
        ]
        
        self.acceptance_criteria_patterns = [
            r"when\s+(.+?)\s+then\s+(.+?)(?:\s+shall\s+(.+))?",
            r"if\s+(.+?)\s+then\s+(.+?)(?:\s+shall\s+(.+))?",
            r"given\s+(.+?)\s+when\s+(.+?)\s+then\s+(.+)"
        ]
    
    async def process_prd_content(self, context: ProcessingContext) -> str:
        """Process and generate PRD content."""
        try:
            logger.info("Starting PRD content processing")
            
            # Get PRD template
            template = self.template_manager.get_template(context.template_config or "prd")
            
            # Extract PRD structure from user input and resources
            prd_structure = self._extract_prd_structure(context)
            
            # Generate content for each section
            section_content = {}
            for section_name, section_template in template.sections.items():
                content = await self._generate_prd_section(
                    section_name, 
                    section_template, 
                    prd_structure, 
                    context
                )
                section_content[section_name] = content
            
            # Render the complete document
            document_content = self._render_document(template, section_content, context)
            
            # Validate and enhance content
            enhanced_content = await self._enhance_content(document_content, "prd", context)
            
            logger.info("PRD content processing completed")
            return enhanced_content
            
        except Exception as e:
            logger.error(f"PRD content processing failed: {e}")
            raise ContentGenerationError("prd", "content_processing", str(e))
    
    async def process_spec_content(self, context: ProcessingContext) -> str:
        """Process and generate SPEC content."""
        try:
            logger.info("Starting SPEC content processing")
            
            # Get SPEC template
            template = self.template_manager.get_template(context.template_config or "spec")
            
            # Extract SPEC structure from user input and resources
            spec_structure = self._extract_spec_structure(context)
            
            # Generate content for each section
            section_content = {}
            for section_name, section_template in template.sections.items():
                content = await self._generate_spec_section(
                    section_name, 
                    section_template, 
                    spec_structure, 
                    context
                )
                section_content[section_name] = content
            
            # Render the complete document
            document_content = self._render_document(template, section_content, context)
            
            # Validate and enhance content
            enhanced_content = await self._enhance_content(document_content, "spec", context)
            
            logger.info("SPEC content processing completed")
            return enhanced_content
            
        except Exception as e:
            logger.error(f"SPEC content processing failed: {e}")
            raise ContentGenerationError("spec", "content_processing", str(e))
    
    async def process_design_content(self, context: ProcessingContext) -> str:
        """Process and generate DESIGN content."""
        try:
            logger.info("Starting DESIGN content processing")
            
            # Get DESIGN template
            template = self.template_manager.get_template(context.template_config or "design")
            
            # Extract DESIGN structure from user input and resources
            design_structure = self._extract_design_structure(context)
            
            # Generate content for each section
            section_content = {}
            for section_name, section_template in template.sections.items():
                content = await self._generate_design_section(
                    section_name, 
                    section_template, 
                    design_structure, 
                    context
                )
                section_content[section_name] = content
            
            # Render the complete document
            document_content = self._render_document(template, section_content, context)
            
            # Validate and enhance content
            enhanced_content = await self._enhance_content(document_content, "design", context)
            
            logger.info("DESIGN content processing completed")
            return enhanced_content
            
        except Exception as e:
            logger.error(f"DESIGN content processing failed: {e}")
            raise ContentGenerationError("design", "content_processing", str(e))
    
    def _extract_prd_structure(self, context: ProcessingContext) -> PRDStructure:
        """Extract PRD structure from context."""
        prd = PRDStructure()
        
        # Extract introduction from user input
        prd.introduction = self._extract_introduction(context.user_input)
        
        # Extract objectives
        prd.objectives = self._extract_objectives(context.user_input)
        
        # Extract user stories
        user_stories = self._extract_user_stories(context.user_input)
        for story in user_stories:
            prd.user_stories.append(story)
        
        # Extract acceptance criteria
        criteria = self._extract_acceptance_criteria(context.user_input)
        for criterion in criteria:
            prd.add_acceptance_criteria(criterion)
        
        # Extract from reference resources if available
        if context.reference_resources:
            self._enhance_prd_from_resources(prd, context.reference_resources)
        
        return prd
    
    def _extract_spec_structure(self, context: ProcessingContext) -> SPECStructure:
        """Extract SPEC structure from context."""
        spec = SPECStructure()
        
        # Extract technical overview
        spec.overview = self._extract_technical_overview(context.user_input)
        
        # Extract architecture information
        spec.architecture = self._extract_architecture_info(context.user_input)
        
        # Extract components
        components = self._extract_components(context.user_input)
        for component in components:
            spec.components.append(component)
        
        # Extract from reference resources if available
        if context.reference_resources:
            self._enhance_spec_from_resources(spec, context.reference_resources)
        
        return spec
    
    def _extract_design_structure(self, context: ProcessingContext) -> DESIGNStructure:
        """Extract DESIGN structure from context."""
        design = DESIGNStructure()
        
        # Extract system design information
        design.system_design = self._extract_system_design(context.user_input)
        
        # Extract UI design information
        design.user_interface_design = self._extract_ui_design(context.user_input)
        
        # Extract data flow information
        design.data_flow = self._extract_data_flow(context.user_input)
        
        # Extract implementation approach
        design.implementation_approach = self._extract_implementation_approach(context.user_input)
        
        # Extract from reference resources if available
        if context.reference_resources:
            self._enhance_design_from_resources(design, context.reference_resources)
        
        return design
    
    def _extract_introduction(self, user_input: str) -> str:
        """Extract introduction content from user input."""
        # Look for introduction patterns
        intro_patterns = [
            r"introduction:?\s*(.+?)(?:\n\n|\n[A-Z]|$)",
            r"overview:?\s*(.+?)(?:\n\n|\n[A-Z]|$)",
            r"summary:?\s*(.+?)(?:\n\n|\n[A-Z]|$)"
        ]
        
        for pattern in intro_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # If no specific introduction found, use first paragraph
        paragraphs = user_input.split('\n\n')
        if paragraphs:
            return paragraphs[0].strip()
        
        return user_input[:200] + "..." if len(user_input) > 200 else user_input
    
    def _extract_objectives(self, user_input: str) -> List[str]:
        """Extract objectives from user input."""
        objectives = []
        
        # Look for objective patterns
        objective_patterns = [
            r"objectives?:?\s*(.+?)(?:\n\n|\n[A-Z]|$)",
            r"goals?:?\s*(.+?)(?:\n\n|\n[A-Z]|$)",
            r"aims?:?\s*(.+?)(?:\n\n|\n[A-Z]|$)"
        ]
        
        for pattern in objective_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE | re.DOTALL)
            if match:
                objective_text = match.group(1).strip()
                # Split by bullet points or numbered lists
                objective_lines = re.split(r'\n[-*•]\s*|\n\d+\.\s*', objective_text)
                objectives.extend([obj.strip() for obj in objective_lines if obj.strip()])
        
        # If no specific objectives found, infer from user input
        if not objectives:
            objectives.append(f"Implement the features and functionality described in the user requirements")
        
        return objectives
    
    def _extract_user_stories(self, user_input: str) -> List[Dict[str, Any]]:
        """Extract user stories from user input."""
        stories = []
        
        for pattern in self.user_story_patterns:
            matches = re.finditer(pattern, user_input, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 3:
                    story = {
                        "role": match.group(1).strip(),
                        "feature": match.group(2).strip(),
                        "benefit": match.group(3).strip(),
                        "story": f"As a {match.group(1).strip()}, I want {match.group(2).strip()}, so that {match.group(3).strip()}",
                        "criteria": []
                    }
                    stories.append(story)
        
        return stories
    
    def _extract_acceptance_criteria(self, user_input: str) -> List[str]:
        """Extract acceptance criteria from user input."""
        criteria = []
        
        for pattern in self.acceptance_criteria_patterns:
            matches = re.finditer(pattern, user_input, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    criterion = f"WHEN {match.group(1).strip()} THEN the system SHALL {match.group(2).strip()}"
                    if len(match.groups()) >= 3 and match.group(3):
                        criterion += f" {match.group(3).strip()}"
                    criteria.append(criterion)
        
        return criteria

    def _extract_technical_overview(self, user_input: str) -> str:
        """Extract technical overview from user input."""
        # Look for technical overview patterns
        tech_patterns = [
            r"technical\s+overview:?\s*(.+?)(?:\n\n|\n[A-Z]|$)",
            r"architecture\s+overview:?\s*(.+?)(?:\n\n|\n[A-Z]|$)",
            r"system\s+overview:?\s*(.+?)(?:\n\n|\n[A-Z]|$)"
        ]

        for pattern in tech_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        # Default technical overview
        return f"This document provides the technical specification for implementing the requirements outlined in the user input."

    def _extract_architecture_info(self, user_input: str) -> str:
        """Extract architecture information from user input."""
        arch_patterns = [
            r"architecture:?\s*(.+?)(?:\n\n|\n[A-Z]|$)",
            r"system\s+design:?\s*(.+?)(?:\n\n|\n[A-Z]|$)",
            r"technical\s+approach:?\s*(.+?)(?:\n\n|\n[A-Z]|$)"
        ]

        for pattern in arch_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        return "The system follows a modular architecture with clear separation of concerns."

    def _extract_components(self, user_input: str) -> List[Dict[str, Any]]:
        """Extract system components from user input."""
        components = []

        # Look for component mentions
        component_patterns = [
            r"component[s]?:?\s*(.+?)(?:\n\n|\n[A-Z]|$)",
            r"module[s]?:?\s*(.+?)(?:\n\n|\n[A-Z]|$)",
            r"service[s]?:?\s*(.+?)(?:\n\n|\n[A-Z]|$)"
        ]

        for pattern in component_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE | re.DOTALL)
            if match:
                component_text = match.group(1).strip()
                # Split by bullet points or numbered lists
                component_lines = re.split(r'\n[-*•]\s*|\n\d+\.\s*', component_text)
                for line in component_lines:
                    if line.strip():
                        components.append({
                            "name": line.strip().split(':')[0] if ':' in line else line.strip(),
                            "description": line.strip().split(':', 1)[1].strip() if ':' in line else "Component description",
                            "responsibilities": [],
                            "dependencies": []
                        })

        return components

    def _extract_system_design(self, user_input: str) -> str:
        """Extract system design information from user input."""
        design_patterns = [
            r"system\s+design:?\s*(.+?)(?:\n\n|\n[A-Z]|$)",
            r"design:?\s*(.+?)(?:\n\n|\n[A-Z]|$)",
            r"implementation:?\s*(.+?)(?:\n\n|\n[A-Z]|$)"
        ]

        for pattern in design_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        return "The system design follows established patterns and best practices."

    def _extract_ui_design(self, user_input: str) -> str:
        """Extract UI design information from user input."""
        ui_patterns = [
            r"ui\s+design:?\s*(.+?)(?:\n\n|\n[A-Z]|$)",
            r"user\s+interface:?\s*(.+?)(?:\n\n|\n[A-Z]|$)",
            r"interface\s+design:?\s*(.+?)(?:\n\n|\n[A-Z]|$)"
        ]

        for pattern in ui_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        return "The user interface design prioritizes usability and accessibility."

    def _extract_data_flow(self, user_input: str) -> str:
        """Extract data flow information from user input."""
        flow_patterns = [
            r"data\s+flow:?\s*(.+?)(?:\n\n|\n[A-Z]|$)",
            r"workflow:?\s*(.+?)(?:\n\n|\n[A-Z]|$)",
            r"process\s+flow:?\s*(.+?)(?:\n\n|\n[A-Z]|$)"
        ]

        for pattern in flow_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        return "Data flows through the system in a structured and efficient manner."

    def _extract_implementation_approach(self, user_input: str) -> str:
        """Extract implementation approach from user input."""
        impl_patterns = [
            r"implementation\s+approach:?\s*(.+?)(?:\n\n|\n[A-Z]|$)",
            r"development\s+approach:?\s*(.+?)(?:\n\n|\n[A-Z]|$)",
            r"technical\s+approach:?\s*(.+?)(?:\n\n|\n[A-Z]|$)"
        ]

        for pattern in impl_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        return "The implementation follows an iterative development approach with continuous testing and validation."

    def _enhance_prd_from_resources(self, prd: PRDStructure, resources: ResourceAnalysis) -> None:
        """Enhance PRD structure with information from reference resources."""
        # Extract requirements from reference files
        requirements_files = resources.get_files_by_category('requirements')
        for file_content in requirements_files:
            # Extract additional user stories
            stories = self._extract_user_stories(file_content.extracted_text)
            prd.user_stories.extend(stories)

            # Extract additional acceptance criteria
            criteria = self._extract_acceptance_criteria(file_content.extracted_text)
            for criterion in criteria:
                prd.add_acceptance_criteria(criterion)

    def _enhance_spec_from_resources(self, spec: SPECStructure, resources: ResourceAnalysis) -> None:
        """Enhance SPEC structure with information from reference resources."""
        # Extract technical information from reference files
        technical_files = resources.get_files_by_category('technical')
        for file_content in technical_files:
            # Extract components
            components = self._extract_components(file_content.extracted_text)
            spec.components.extend(components)

    def _enhance_design_from_resources(self, design: DESIGNStructure, resources: ResourceAnalysis) -> None:
        """Enhance DESIGN structure with information from reference resources."""
        # Extract design information from reference files
        design_files = resources.get_files_by_category('design')
        for file_content in design_files:
            # Extract design patterns and constraints
            if 'pattern' in file_content.extracted_text.lower():
                design.design_patterns.append({
                    "name": "Referenced Pattern",
                    "description": "Pattern found in reference materials",
                    "use_case": "As specified in reference documentation"
                })

    async def _generate_prd_section(self, section_name: str, section_template: str,
                                   prd_structure: PRDStructure, context: ProcessingContext) -> str:
        """Generate content for a PRD section."""
        # Create placeholder values based on section and structure
        placeholders = self._create_prd_placeholders(section_name, prd_structure, context)

        # Replace placeholders in template
        return self._replace_placeholders(section_template, placeholders)

    async def _generate_spec_section(self, section_name: str, section_template: str,
                                    spec_structure: SPECStructure, context: ProcessingContext) -> str:
        """Generate content for a SPEC section."""
        # Create placeholder values based on section and structure
        placeholders = self._create_spec_placeholders(section_name, spec_structure, context)

        # Replace placeholders in template
        return self._replace_placeholders(section_template, placeholders)

    async def _generate_design_section(self, section_name: str, section_template: str,
                                      design_structure: DESIGNStructure, context: ProcessingContext) -> str:
        """Generate content for a DESIGN section."""
        # Create placeholder values based on section and structure
        placeholders = self._create_design_placeholders(section_name, design_structure, context)

        # Replace placeholders in template
        return self._replace_placeholders(section_template, placeholders)

    def _create_prd_placeholders(self, section_name: str, prd_structure: PRDStructure,
                                context: ProcessingContext) -> Dict[str, str]:
        """Create placeholder values for PRD sections."""
        now = datetime.now()
        placeholders = {
            'title': self._extract_title(context.user_input),
            'project_name': self._extract_project_name(context.user_input),
            'created_date': now.strftime('%Y-%m-%d'),
            'last_modified': now.strftime('%Y-%m-%d'),
            'introduction_content': prd_structure.introduction,
            'project_context': context.project_context or "Project context to be defined",
            'objectives_list': self._format_list(prd_structure.objectives),
            'success_criteria': "Success criteria to be defined based on objectives",
            'user_stories_content': self._format_user_stories(prd_structure.user_stories),
            'acceptance_criteria_list': self._format_list(prd_structure.acceptance_criteria),
            'success_metrics_list': self._format_list(prd_structure.success_metrics) if prd_structure.success_metrics else "Success metrics to be defined",
            'kpi_list': "Key performance indicators to be defined",
            'technical_constraints': "Technical constraints to be identified",
            'business_constraints': "Business constraints to be identified",
            'timeline_constraints': "Timeline constraints to be identified",
            'assumptions_list': self._format_list(prd_structure.assumptions) if prd_structure.assumptions else "Assumptions to be documented",
            'internal_dependencies': "Internal dependencies to be identified",
            'external_dependencies': "External dependencies to be identified",
            'glossary': "Terms and definitions to be added",
            'references': "Reference materials and sources"
        }

        return placeholders

    def _create_spec_placeholders(self, section_name: str, spec_structure: SPECStructure,
                                 context: ProcessingContext) -> Dict[str, str]:
        """Create placeholder values for SPEC sections."""
        now = datetime.now()
        placeholders = {
            'title': self._extract_title(context.user_input),
            'project_name': self._extract_project_name(context.user_input),
            'created_date': now.strftime('%Y-%m-%d'),
            'last_modified': now.strftime('%Y-%m-%d'),
            'prd_document': "PRD.md",
            'overview_content': spec_structure.overview,
            'scope_description': "Scope description based on requirements",
            'architecture_description': spec_structure.architecture,
            'architecture_diagram': self._generate_architecture_diagram(context),
            'design_principles': "Design principles to be documented",
            'components_description': "System components overview",
            'component_details': self._format_components(spec_structure.components),
            'interfaces_description': "API interfaces overview",
            'interface_details': self._format_interfaces(spec_structure.interfaces),
            'data_models_description': "Data models overview",
            'data_structure_details': self._format_data_models(spec_structure.data_models),
            'data_model_diagram': self._generate_data_model_diagram(context),
            'implementation_description': "Implementation details overview",
            'technology_stack': "Technology stack to be defined",
            'implementation_approach': "Implementation approach to be documented",
            'testing_description': spec_structure.testing_strategy,
            'test_coverage': "Test coverage requirements to be defined",
            'testing_approach': "Testing approach to be documented",
            'deployment_description': "Deployment considerations overview",
            'infrastructure_requirements': "Infrastructure requirements to be defined",
            'deployment_pipeline': "Deployment pipeline to be documented",
            'technical_references': "Technical references and documentation",
            'configuration_examples': "Configuration examples to be provided"
        }

        return placeholders

    def _create_design_placeholders(self, section_name: str, design_structure: DESIGNStructure,
                                   context: ProcessingContext) -> Dict[str, str]:
        """Create placeholder values for DESIGN sections."""
        now = datetime.now()
        placeholders = {
            'title': self._extract_title(context.user_input),
            'project_name': self._extract_project_name(context.user_input),
            'created_date': now.strftime('%Y-%m-%d'),
            'last_modified': now.strftime('%Y-%m-%d'),
            'prd_document': "PRD.md",
            'spec_document': "SPEC.md",
            'system_design_description': design_structure.system_design,
            'high_level_design': "High-level design overview",
            'system_diagram': self._generate_system_diagram(context),
            'ui_design_description': design_structure.user_interface_design,
            'ui_design_principles': "UI design principles to be documented",
            'user_flow_diagram': self._generate_user_flow_diagram(context),
            'interface_specifications': "Interface specifications to be defined",
            'data_flow_description': design_structure.data_flow,
            'data_flow_diagram': self._generate_data_flow_diagram(context),
            'data_processing_pipeline': "Data processing pipeline to be documented",
            'implementation_approach_description': design_structure.implementation_approach,
            'development_phases': "Development phases to be defined",
            'implementation_strategy': "Implementation strategy to be documented",
            'design_patterns_description': "Design patterns overview",
            'recommended_patterns': self._format_design_patterns(design_structure.design_patterns),
            'pattern_implementation': "Pattern implementation guidelines",
            'technical_constraints': self._format_list(design_structure.constraints) if design_structure.constraints else "Technical constraints to be identified",
            'performance_constraints': "Performance constraints to be defined",
            'security_constraints': "Security constraints to be defined",
            'security_description': "Security considerations overview",
            'security_requirements': self._format_list(design_structure.security_considerations) if design_structure.security_considerations else "Security requirements to be defined",
            'security_implementation': "Security implementation guidelines",
            'performance_description': "Performance requirements overview",
            'performance_targets': self._format_list(design_structure.performance_requirements) if design_structure.performance_requirements else "Performance targets to be defined",
            'optimization_strategy': "Optimization strategy to be documented",
            'design_assets': "Design assets and resources",
            'implementation_examples': "Implementation examples to be provided",
            'design_references': "Design references and documentation"
        }

        return placeholders

    def _extract_title(self, user_input: str) -> str:
        """Extract project title from user input."""
        # Look for title patterns
        title_patterns = [
            r"title:?\s*(.+?)(?:\n|$)",
            r"project:?\s*(.+?)(?:\n|$)",
            r"name:?\s*(.+?)(?:\n|$)"
        ]

        for pattern in title_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Default title based on first line or words
        first_line = user_input.split('\n')[0].strip()
        if len(first_line) < 100:
            return first_line

        # Use first few words
        words = user_input.split()[:5]
        return ' '.join(words) + "..."

    def _extract_project_name(self, user_input: str) -> str:
        """Extract project name from user input."""
        title = self._extract_title(user_input)
        # Clean up title to make it a proper project name
        project_name = re.sub(r'[^\w\s-]', '', title)
        return project_name.strip() or "Project"

    def _format_list(self, items: List[str]) -> str:
        """Format a list of items as markdown."""
        if not items:
            return "- Items to be defined"

        return '\n'.join([f"- {item}" for item in items])

    def _format_user_stories(self, stories: List[Dict[str, Any]]) -> str:
        """Format user stories as markdown."""
        if not stories:
            return "### User stories to be defined based on requirements"

        formatted = []
        for i, story in enumerate(stories, 1):
            formatted.append(f"### Requirement {i}")
            formatted.append(f"**User Story:** {story['story']}")
            if story.get('criteria'):
                formatted.append("#### Acceptance Criteria")
                for j, criteria in enumerate(story['criteria'], 1):
                    formatted.append(f"{j}. {criteria}")
            formatted.append("")  # Empty line

        return '\n'.join(formatted)

    def _format_components(self, components: List[Dict[str, Any]]) -> str:
        """Format components as markdown."""
        if not components:
            return "Components to be defined based on architecture"

        formatted = []
        for component in components:
            formatted.append(f"### {component['name']}")
            formatted.append(f"{component['description']}")
            if component.get('responsibilities'):
                formatted.append("**Responsibilities:**")
                for resp in component['responsibilities']:
                    formatted.append(f"- {resp}")
            formatted.append("")

        return '\n'.join(formatted)

    def _format_interfaces(self, interfaces: List[Dict[str, Any]]) -> str:
        """Format interfaces as markdown."""
        if not interfaces:
            return "Interfaces to be defined based on system requirements"

        formatted = []
        for interface in interfaces:
            formatted.append(f"### {interface['name']}")
            formatted.append(f"**Type:** {interface['type']}")
            formatted.append(f"{interface['description']}")
            formatted.append("")

        return '\n'.join(formatted)

    def _format_data_models(self, models: List[Dict[str, Any]]) -> str:
        """Format data models as markdown."""
        if not models:
            return "Data models to be defined based on system requirements"

        formatted = []
        for model in models:
            formatted.append(f"### {model['name']}")
            formatted.append(f"{model['description']}")
            if model.get('fields'):
                formatted.append("**Fields:**")
                for field in model['fields']:
                    formatted.append(f"- {field}")
            formatted.append("")

        return '\n'.join(formatted)

    def _format_design_patterns(self, patterns: List[Dict[str, Any]]) -> str:
        """Format design patterns as markdown."""
        if not patterns:
            return "Design patterns to be identified based on system requirements"

        formatted = []
        for pattern in patterns:
            formatted.append(f"### {pattern['name']}")
            formatted.append(f"{pattern['description']}")
            if pattern.get('use_case'):
                formatted.append(f"**Use Case:** {pattern['use_case']}")
            formatted.append("")

        return '\n'.join(formatted)

    def _generate_architecture_diagram(self, context: ProcessingContext) -> str:
        """Generate a basic architecture diagram in Mermaid format."""
        return """graph TB
    A[Client] --> B[API Gateway]
    B --> C[Application Layer]
    C --> D[Business Logic]
    D --> E[Data Layer]
    E --> F[Database]"""

    def _generate_data_model_diagram(self, context: ProcessingContext) -> str:
        """Generate a basic data model diagram in Mermaid format."""
        return """erDiagram
    Entity1 {
        id int
        name string
        created_at datetime
    }
    Entity2 {
        id int
        entity1_id int
        value string
    }
    Entity1 ||--o{ Entity2 : has"""

    def _generate_system_diagram(self, context: ProcessingContext) -> str:
        """Generate a basic system diagram in Mermaid format."""
        return """graph LR
    A[User Interface] --> B[Application Core]
    B --> C[Data Processing]
    C --> D[Storage Layer]
    B --> E[External APIs]"""

    def _generate_user_flow_diagram(self, context: ProcessingContext) -> str:
        """Generate a basic user flow diagram in Mermaid format."""
        return """flowchart TD
    A[User Login] --> B[Dashboard]
    B --> C[Select Action]
    C --> D[Process Request]
    D --> E[Display Result]"""

    def _generate_data_flow_diagram(self, context: ProcessingContext) -> str:
        """Generate a basic data flow diagram in Mermaid format."""
        return """flowchart LR
    A[Input Data] --> B[Validation]
    B --> C[Processing]
    C --> D[Storage]
    D --> E[Output]"""

    def _replace_placeholders(self, template: str, placeholders: Dict[str, str]) -> str:
        """Replace placeholders in template with actual values."""
        result = template

        for placeholder, value in placeholders.items():
            pattern = f"{{{placeholder}}}"
            result = result.replace(pattern, str(value))

        return result

    def _render_document(self, template: Template, section_content: Dict[str, str],
                        context: ProcessingContext) -> str:
        """Render the complete document from template and section content."""
        # Combine all sections in the order defined by the template
        document_parts = []

        for section_name in template.sections.keys():
            if section_name in section_content:
                content = section_content[section_name]
                if content.strip():  # Only add non-empty sections
                    document_parts.append(content)

        return '\n\n'.join(document_parts)

    async def _enhance_content(self, content: str, doc_type: str,
                              context: ProcessingContext) -> str:
        """Enhance generated content with additional formatting and validation."""
        enhanced = content

        # Add document metadata
        metadata = DocumentMetadata(
            document_type=doc_type,
            created_date=datetime.now().strftime('%Y-%m-%d'),
            last_modified=datetime.now().strftime('%Y-%m-%d')
        )

        # Clean up formatting
        enhanced = self._clean_formatting(enhanced)

        # Add cross-references if applicable
        enhanced = self._add_cross_references(enhanced, doc_type, context)

        # Validate content
        validation_result = self._validate_content(enhanced, doc_type)
        if not validation_result.is_valid:
            logger.warning(f"Content validation issues: {validation_result.issues}")

        return enhanced

    def _clean_formatting(self, content: str) -> str:
        """Clean up document formatting."""
        # Remove excessive whitespace
        lines = content.split('\n')
        cleaned_lines = []

        for line in lines:
            cleaned_lines.append(line.rstrip())

        # Remove excessive empty lines
        result = '\n'.join(cleaned_lines)
        result = re.sub(r'\n{3,}', '\n\n', result)

        return result.strip()

    def _add_cross_references(self, content: str, doc_type: str,
                             context: ProcessingContext) -> str:
        """Add cross-references to related documents."""
        # This would be enhanced to add actual cross-references
        # For now, return content as-is
        return content

    def _validate_content(self, content: str, doc_type: str) -> ValidationResult:
        """Validate generated content for quality and completeness."""
        validation_result = ValidationResult(is_valid=True)

        # Check minimum content length
        if len(content) < 500:
            validation_result.add_issue(
                "Content is too short",
                "Ensure all sections have adequate content"
            )

        # Check for placeholder content that wasn't replaced
        placeholder_pattern = r'\{[^}]+\}'
        placeholders = re.findall(placeholder_pattern, content)
        if placeholders:
            validation_result.add_issue(
                f"Unreplaced placeholders found: {', '.join(placeholders)}",
                "Check template placeholders and ensure all values are provided"
            )

        # Check for required sections based on document type
        required_sections = self._get_required_sections_for_validation(doc_type)
        for section in required_sections:
            if section.lower() not in content.lower():
                validation_result.add_issue(
                    f"Missing required section: {section}",
                    f"Add the '{section}' section to the document"
                )

        return validation_result

    def _get_required_sections_for_validation(self, doc_type: str) -> List[str]:
        """Get required sections for content validation."""
        required_sections = {
            'prd': ['Introduction', 'Objectives', 'Requirements'],
            'spec': ['Overview', 'Architecture', 'Components'],
            'design': ['System Design', 'Data Flow', 'Implementation']
        }
        return required_sections.get(doc_type, [])

    async def generate_prd_prompt(self, context: ProcessingContext) -> PromptResult:
        """Generate intelligent prompt for PRD creation."""
        try:
            logger.info("Generating PRD prompt")

            # Get PRD template structure
            template = self.template_manager.get_template(context.template_config or "prd")

            # Extract PRD structure from context
            prd_structure = self._extract_prd_structure(context)

            # Create intelligent prompt
            prompt = self._create_prd_prompt(context, prd_structure, template)

            # Create context summary
            context_summary = self._create_context_summary(context, "PRD")

            return PromptResult(
                document_type="prd",
                prompt=prompt,
                template_structure=template.sections,
                extracted_data=prd_structure.to_dict(),
                context_summary=context_summary,
                references_used=self._get_references_list(context),
                suggested_filename="PRD.md",
                metadata={
                    "template_used": context.template_config,
                    "has_reference_resources": context.reference_resources is not None,
                    "user_stories_count": len(prd_structure.user_stories),
                    "objectives_count": len(prd_structure.objectives)
                }
            )

        except Exception as e:
            logger.error(f"PRD prompt generation failed: {e}")
            raise ContentGenerationError("prd", "prompt_generation", str(e))

    async def generate_spec_prompt(self, context: ProcessingContext) -> PromptResult:
        """Generate intelligent prompt for SPEC creation."""
        try:
            logger.info("Generating SPEC prompt")

            # Get SPEC template structure
            template = self.template_manager.get_template(context.template_config or "spec")

            # Extract SPEC structure from context
            spec_structure = self._extract_spec_structure(context)

            # Create intelligent prompt
            prompt = self._create_spec_prompt(context, spec_structure, template)

            # Create context summary
            context_summary = self._create_context_summary(context, "SPEC")

            return PromptResult(
                document_type="spec",
                prompt=prompt,
                template_structure=template.sections,
                extracted_data=spec_structure.to_dict(),
                context_summary=context_summary,
                references_used=self._get_references_list(context),
                suggested_filename="SPEC.md",
                metadata={
                    "template_used": context.template_config,
                    "has_reference_resources": context.reference_resources is not None,
                    "components_count": len(spec_structure.components),
                    "interfaces_count": len(spec_structure.interfaces)
                }
            )

        except Exception as e:
            logger.error(f"SPEC prompt generation failed: {e}")
            raise ContentGenerationError("spec", "prompt_generation", str(e))

    async def generate_design_prompt(self, context: ProcessingContext) -> PromptResult:
        """Generate intelligent prompt for DESIGN creation."""
        try:
            logger.info("Generating DESIGN prompt")

            # Get DESIGN template structure
            template = self.template_manager.get_template(context.template_config or "design")

            # Extract DESIGN structure from context
            design_structure = self._extract_design_structure(context)

            # Create intelligent prompt
            prompt = self._create_design_prompt(context, design_structure, template)

            # Create context summary
            context_summary = self._create_context_summary(context, "DESIGN")

            return PromptResult(
                document_type="design",
                prompt=prompt,
                template_structure=template.sections,
                extracted_data=design_structure.to_dict(),
                context_summary=context_summary,
                references_used=self._get_references_list(context),
                suggested_filename="DESIGN.md",
                metadata={
                    "template_used": context.template_config,
                    "has_reference_resources": context.reference_resources is not None,
                    "ui_components_count": len(design_structure.ui_components),
                    "workflows_count": len(design_structure.workflows)
                }
            )

        except Exception as e:
            logger.error(f"DESIGN prompt generation failed: {e}")
            raise ContentGenerationError("design", "prompt_generation", str(e))

    async def validate_ai_generated_content(self, document_type: str, content: str) -> ContentValidationResult:
        """Validate AI-generated content structure and quality."""
        try:
            logger.info(f"Validating AI-generated {document_type} content")

            validation_result = ContentValidationResult(
                is_valid=True,
                document_type=document_type
            )

            # Check for required sections
            required_sections = self._get_required_sections_for_validation(document_type)
            sections_found = []
            missing_sections = []

            for section in required_sections:
                if self._section_exists_in_content(content, section):
                    sections_found.append(section)
                else:
                    missing_sections.append(section)
                    validation_result.add_issue(
                        f"Missing required section: {section}",
                        f"Add a '{section}' section to the document"
                    )

            validation_result.sections_found = sections_found
            validation_result.missing_sections = missing_sections

            # Check content quality
            self._validate_content_quality(content, document_type, validation_result)

            return validation_result

        except Exception as e:
            logger.error(f"AI content validation failed: {e}")
            return ContentValidationResult(
                is_valid=False,
                document_type=document_type,
                quality_issues=[f"Validation error: {str(e)}"],
                suggestions=["Check content format and structure"]
            )

    def _create_prd_prompt(self, context: ProcessingContext, prd_structure: PRDStructure, template: Template) -> str:
        """Create intelligent prompt for PRD generation."""
        reference_summary = ""
        if context.reference_resources:
            reference_summary = f"\n**Reference Materials Summary:**\n{context.reference_resources.content_summary}\n"

        user_stories_text = ""
        if prd_structure.user_stories:
            user_stories_text = "\n**Extracted User Stories:**\n"
            for story in prd_structure.user_stories:
                user_stories_text += f"- {story.get('story', 'N/A')}\n"

        objectives_text = ""
        if prd_structure.objectives:
            objectives_text = "\n**Identified Objectives:**\n"
            for obj in prd_structure.objectives:
                objectives_text += f"- {obj}\n"

        prompt = f"""Create a comprehensive Product Requirements Document (PRD) following Kiro's standards and best practices.

**User Input:** {context.user_input}

**Project Context:** {context.project_context or "Not specified"}
{reference_summary}{user_stories_text}{objectives_text}

Please generate a complete PRD with the following sections:

1. **Introduction** - Clear overview of the product/feature and its purpose
2. **Objectives** - Specific, measurable goals that align with business needs
3. **User Stories** - Well-formatted user stories with acceptance criteria
4. **Success Metrics** - Quantifiable KPIs and success measures
5. **Constraints and Dependencies** - Technical and business limitations
6. **Assumptions** - Key assumptions being made

**Guidelines:**
- Use clear, professional language
- Make objectives specific and measurable
- Include acceptance criteria for each user story
- Focus on user value and business impact
- Consider technical feasibility
- Follow Kiro's PRD template structure

Generate comprehensive, actionable content for each section based on the provided context and requirements."""

        return prompt

    def _create_spec_prompt(self, context: ProcessingContext, spec_structure: SPECStructure, template: Template) -> str:
        """Create intelligent prompt for SPEC generation."""
        reference_summary = ""
        if context.reference_resources:
            reference_summary = f"\n**Reference Materials Summary:**\n{context.reference_resources.content_summary}\n"

        components_text = ""
        if spec_structure.components:
            components_text = "\n**Identified Components:**\n"
            for comp in spec_structure.components:
                components_text += f"- {comp.get('name', 'N/A')}: {comp.get('description', 'N/A')}\n"

        prompt = f"""Create a comprehensive Technical Specification Document (SPEC) following Kiro's standards and best practices.

**Requirements Input:** {context.user_input}

**Project Context:** {context.project_context or "Not specified"}
{reference_summary}{components_text}

Please generate a complete SPEC with the following sections:

1. **Technical Overview** - High-level technical approach and architecture
2. **System Architecture** - Detailed system design and component relationships
3. **Components** - Individual system components with interfaces and responsibilities
4. **Data Models** - Database schemas, API contracts, and data structures
5. **Implementation Details** - Technical implementation specifics and considerations
6. **Testing Strategy** - Testing approach, types, and coverage requirements
7. **Deployment Considerations** - Infrastructure, scaling, and operational requirements

**Guidelines:**
- Focus on technical accuracy and feasibility
- Include specific implementation details
- Consider scalability and performance
- Address security and reliability concerns
- Provide clear component interfaces
- Follow industry best practices

Generate detailed, technically sound content for each section based on the provided requirements."""

        return prompt

    def _create_design_prompt(self, context: ProcessingContext, design_structure: DESIGNStructure, template: Template) -> str:
        """Create intelligent prompt for DESIGN generation."""
        reference_summary = ""
        if context.reference_resources:
            reference_summary = f"\n**Reference Materials Summary:**\n{context.reference_resources.content_summary}\n"

        ui_components_text = ""
        if design_structure.ui_components:
            ui_components_text = "\n**Identified UI Components:**\n"
            for comp in design_structure.ui_components:
                ui_components_text += f"- {comp.get('name', 'N/A')}: {comp.get('description', 'N/A')}\n"

        prompt = f"""Create a comprehensive Design Document (DESIGN) following Kiro's standards and best practices.

**Specification Input:** {context.user_input}

**Project Context:** {context.project_context or "Not specified"}
{reference_summary}{ui_components_text}

Please generate a complete DESIGN with the following sections:

1. **System Design** - Overall system architecture and design patterns
2. **User Interface Design** - UI/UX design specifications and wireframes
3. **Data Flow** - Data movement and processing workflows
4. **Implementation Plan** - Step-by-step implementation approach
5. **Security Considerations** - Security measures and compliance requirements
6. **Performance Requirements** - Performance targets and optimization strategies
7. **Monitoring and Maintenance** - Operational monitoring and maintenance procedures

**Guidelines:**
- Focus on user experience and usability
- Include specific design patterns and principles
- Consider accessibility and responsive design
- Address performance and scalability
- Provide clear implementation guidance
- Follow modern design best practices

Generate comprehensive, actionable design content for each section based on the provided specifications."""

        return prompt

    def _create_context_summary(self, context: ProcessingContext, doc_type: str) -> str:
        """Create a summary of the processing context."""
        summary_parts = [f"Document Type: {doc_type}"]

        if context.project_context:
            summary_parts.append(f"Project Context: {context.project_context[:100]}...")

        if context.reference_resources:
            summary_parts.append(f"Reference Files: {context.reference_resources.total_files}")

        summary_parts.append(f"Template: {context.template_config}")
        summary_parts.append(f"Generation Mode: {context.generation_mode}")

        return " | ".join(summary_parts)

    def _get_references_list(self, context: ProcessingContext) -> List[str]:
        """Get list of reference materials used."""
        references = []
        if context.reference_resources:
            for category, files in context.reference_resources.categorized_files.items():
                for file_content in files:
                    references.append(f"{category}: {file_content.file_path.name}")
        return references

    def _section_exists_in_content(self, content: str, section_name: str) -> bool:
        """Check if a section exists in the content."""
        # Look for markdown headers with the section name
        patterns = [
            rf"^#{1,6}\s*{re.escape(section_name)}\s*$",
            rf"^#{1,6}\s*{re.escape(section_name.lower())}\s*$",
            rf"^#{1,6}\s*{re.escape(section_name.upper())}\s*$",
        ]

        for pattern in patterns:
            if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                return True
        return False

    def _validate_content_quality(self, content: str, document_type: str, validation_result: ContentValidationResult):
        """Validate content quality and add issues to validation result."""
        # Check minimum content length
        if len(content.strip()) < 500:
            validation_result.add_issue(
                "Content appears too short for a comprehensive document",
                "Expand the content with more detailed information"
            )

        # Check for placeholder text
        placeholder_patterns = [
            r"\[.*?\]",  # [placeholder text]
            r"TODO",
            r"TBD",
            r"PLACEHOLDER"
        ]

        for pattern in placeholder_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                validation_result.add_issue(
                    f"Found placeholder text: {pattern}",
                    "Replace placeholder text with actual content"
                )

        # Check for proper markdown formatting
        if not re.search(r"^#{1,6}\s+", content, re.MULTILINE):
            validation_result.add_issue(
                "No markdown headers found",
                "Use proper markdown headers (# ## ###) to structure the document"
            )

        # Document-specific validations
        if document_type == "prd":
            self._validate_prd_specific_content(content, validation_result)
        elif document_type == "spec":
            self._validate_spec_specific_content(content, validation_result)
        elif document_type == "design":
            self._validate_design_specific_content(content, validation_result)

    def _validate_prd_specific_content(self, content: str, validation_result: ContentValidationResult):
        """Validate PRD-specific content requirements."""
        # Check for user stories
        if not re.search(r"as\s+(?:a|an)\s+.*?i\s+want.*?so\s+that", content, re.IGNORECASE):
            validation_result.add_issue(
                "No properly formatted user stories found",
                "Include user stories in the format: 'As a [user], I want [goal] so that [benefit]'"
            )

        # Check for acceptance criteria
        if not re.search(r"acceptance\s+criteria", content, re.IGNORECASE):
            validation_result.add_issue(
                "No acceptance criteria section found",
                "Include acceptance criteria for user stories"
            )

    def _validate_spec_specific_content(self, content: str, validation_result: ContentValidationResult):
        """Validate SPEC-specific content requirements."""
        # Check for technical details
        technical_keywords = ["API", "database", "component", "interface", "architecture"]
        if not any(keyword.lower() in content.lower() for keyword in technical_keywords):
            validation_result.add_issue(
                "Limited technical content found",
                "Include more technical details about APIs, databases, components, etc."
            )

    def _validate_design_specific_content(self, content: str, validation_result: ContentValidationResult):
        """Validate DESIGN-specific content requirements."""
        # Check for design elements
        design_keywords = ["UI", "UX", "interface", "workflow", "user experience"]
        if not any(keyword.lower() in content.lower() for keyword in design_keywords):
            validation_result.add_issue(
                "Limited design content found",
                "Include more design details about UI, UX, workflows, etc."
            )
