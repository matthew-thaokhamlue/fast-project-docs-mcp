"""
Template manager for the MCP Document Generator.

This module manages document templates, including loading, validation,
customization, and storage of templates.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from ..models.core import Template, ValidationResult
from ..exceptions import TemplateValidationError, ConfigurationError
from .defaults import DefaultTemplates


logger = logging.getLogger(__name__)


class TemplateManager:
    """Manager for document templates."""
    
    def __init__(self, custom_templates_path: Optional[Path] = None):
        """Initialize the template manager."""
        self.custom_templates_path = custom_templates_path
        self._templates: Dict[str, Template] = {}
        self._load_default_templates()
        
        if custom_templates_path and custom_templates_path.exists():
            self._load_custom_templates()
    
    def _load_default_templates(self) -> None:
        """Load default templates."""
        try:
            default_templates = DefaultTemplates.get_all_templates()
            for template_type, template in default_templates.items():
                self._templates[f"default_{template_type}"] = template
            
            logger.info(f"Loaded {len(default_templates)} default templates")
        except Exception as e:
            logger.error(f"Failed to load default templates: {e}")
            raise ConfigurationError(
                "default_templates",
                f"Failed to load default templates: {str(e)}"
            )
    
    def _load_custom_templates(self) -> None:
        """Load custom templates from the templates directory."""
        if not self.custom_templates_path or not self.custom_templates_path.exists():
            return
        
        try:
            template_files = list(self.custom_templates_path.glob("*.yaml"))
            template_files.extend(self.custom_templates_path.glob("*.yml"))
            
            for template_file in template_files:
                try:
                    template = self._load_template_file(template_file)
                    if template:
                        self._templates[template.name] = template
                        logger.info(f"Loaded custom template: {template.name}")
                except Exception as e:
                    logger.error(f"Failed to load template {template_file}: {e}")
            
            logger.info(f"Loaded {len(template_files)} custom template files")
        except Exception as e:
            logger.error(f"Failed to load custom templates: {e}")
    
    def _load_template_file(self, template_file: Path) -> Optional[Template]:
        """Load a template from a YAML file."""
        try:
            import yaml
            
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f)
            
            # Validate required fields
            required_fields = ['name', 'template_type', 'sections']
            for field in required_fields:
                if field not in template_data:
                    raise TemplateValidationError(
                        template_file.name,
                        [f"Missing required field: {field}"]
                    )
            
            template = Template(
                name=template_data['name'],
                template_type=template_data['template_type'],
                sections=template_data['sections'],
                metadata=template_data.get('metadata', {}),
                version=template_data.get('version', '1.0')
            )
            
            # Validate template structure
            validation_result = self.validate_template(template)
            if not validation_result.is_valid:
                raise TemplateValidationError(
                    template.name,
                    validation_result.issues
                )
            
            return template
            
        except Exception as e:
            logger.error(f"Failed to load template from {template_file}: {e}")
            return None
    
    def get_template(self, template_name: str) -> Template:
        """Get a template by name."""
        if template_name not in self._templates:
            # Try with default prefix
            default_name = f"default_{template_name}"
            if default_name in self._templates:
                return self._templates[default_name]
            
            available_templates = list(self._templates.keys())
            raise TemplateValidationError(
                template_name,
                [f"Template not found. Available templates: {', '.join(available_templates)}"]
            )
        
        return self._templates[template_name]
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates."""
        templates_info = []
        
        for name, template in self._templates.items():
            templates_info.append({
                'name': name,
                'type': template.template_type,
                'version': template.version,
                'description': template.metadata.get('description', ''),
                'sections': list(template.sections.keys()),
                'supports_customization': template.metadata.get('supports_customization', False)
            })
        
        return templates_info
    
    def customize_template(self, base_template_name: str, 
                          customizations: Dict[str, Any]) -> Template:
        """Create a customized version of a template."""
        base_template = self.get_template(base_template_name)
        
        # Create a copy of the base template
        custom_sections = base_template.sections.copy()
        custom_metadata = base_template.metadata.copy()
        
        # Apply customizations
        if 'sections' in customizations:
            section_customizations = customizations['sections']
            
            # Add new sections
            if 'add' in section_customizations:
                for section_name, section_content in section_customizations['add'].items():
                    custom_sections[section_name] = section_content
            
            # Modify existing sections
            if 'modify' in section_customizations:
                for section_name, section_content in section_customizations['modify'].items():
                    if section_name in custom_sections:
                        custom_sections[section_name] = section_content
                    else:
                        logger.warning(f"Cannot modify non-existent section: {section_name}")
            
            # Remove sections
            if 'remove' in section_customizations:
                for section_name in section_customizations['remove']:
                    if section_name in custom_sections:
                        del custom_sections[section_name]
                    else:
                        logger.warning(f"Cannot remove non-existent section: {section_name}")
        
        # Update metadata
        if 'metadata' in customizations:
            custom_metadata.update(customizations['metadata'])
        
        # Create custom template
        custom_name = customizations.get('name', f"{base_template_name}_custom")
        custom_template = Template(
            name=custom_name,
            template_type=base_template.template_type,
            sections=custom_sections,
            metadata=custom_metadata,
            version=customizations.get('version', base_template.version)
        )
        
        # Validate customized template
        validation_result = self.validate_template(custom_template)
        if not validation_result.is_valid:
            raise TemplateValidationError(
                custom_name,
                validation_result.issues
            )
        
        # Store the customized template
        self._templates[custom_name] = custom_template
        
        logger.info(f"Created customized template: {custom_name}")
        return custom_template
    
    def validate_template(self, template: Template) -> ValidationResult:
        """Validate a template structure and content."""
        validation_result = ValidationResult(is_valid=True)
        
        # Check basic structure
        if not template.name:
            validation_result.add_issue("Template name is required")
        
        if not template.template_type:
            validation_result.add_issue("Template type is required")
        
        if not template.sections:
            validation_result.add_issue("Template must have at least one section")
        
        # Validate template type
        valid_types = ['prd', 'spec', 'design']
        if template.template_type not in valid_types:
            validation_result.add_issue(
                f"Invalid template type: {template.template_type}. "
                f"Must be one of: {', '.join(valid_types)}"
            )
        
        # Check for required sections based on template type
        required_sections = self._get_required_sections(template.template_type)
        for section in required_sections:
            if section not in template.sections:
                validation_result.add_issue(
                    f"Missing required section for {template.template_type}: {section}",
                    f"Add the '{section}' section to the template"
                )
        
        # Check for empty sections
        for section_name, content in template.sections.items():
            if not content or not content.strip():
                validation_result.add_issue(
                    f"Empty section: {section_name}",
                    f"Add content to the '{section_name}' section or remove it"
                )
        
        # Validate placeholder syntax
        for section_name, content in template.sections.items():
            placeholder_issues = self._validate_placeholders(content)
            for issue in placeholder_issues:
                validation_result.add_issue(
                    f"Placeholder issue in section '{section_name}': {issue}"
                )
        
        return validation_result
    
    def _get_required_sections(self, template_type: str) -> List[str]:
        """Get required sections for a template type."""
        required_sections = {
            'prd': ['introduction', 'objectives', 'user_stories', 'acceptance_criteria'],
            'spec': ['overview', 'architecture', 'components', 'implementation_details'],
            'design': ['system_design', 'data_flow', 'implementation_approach']
        }
        return required_sections.get(template_type, [])
    
    def _validate_placeholders(self, content: str) -> List[str]:
        """Validate placeholder syntax in template content."""
        import re
        issues = []
        
        # Find all placeholders
        placeholder_pattern = r'\{([^}]+)\}'
        placeholders = re.findall(placeholder_pattern, content)
        
        for placeholder in placeholders:
            # Check for valid placeholder names (alphanumeric and underscore)
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', placeholder):
                issues.append(f"Invalid placeholder name: {{{placeholder}}}")
        
        # Check for unmatched braces
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            issues.append("Unmatched braces in template content")
        
        return issues
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """Get detailed information about a template."""
        template = self.get_template(template_name)
        
        return {
            'name': template.name,
            'type': template.template_type,
            'version': template.version,
            'created_time': template.created_time.isoformat(),
            'metadata': template.metadata,
            'sections': {
                name: {
                    'length': len(content),
                    'placeholders': self._extract_placeholders(content)
                }
                for name, content in template.sections.items()
            },
            'validation': self.validate_template(template).to_dict()
        }
    
    def _extract_placeholders(self, content: str) -> List[str]:
        """Extract placeholder names from template content."""
        import re
        placeholder_pattern = r'\{([^}]+)\}'
        return re.findall(placeholder_pattern, content)
