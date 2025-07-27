# Document Generator MCP Server

A Python-based Model Context Protocol (MCP) server that automates the generation of project documentation including PRD.md (Product Requirements Document), SPEC.md (Technical Specification), and DESIGN.md (Design Document). The server follows Kiro's document creation best practices and integrates seamlessly with MCP-compatible clients.

## Features

- **Automated Document Generation**: Generate PRD, SPEC, and DESIGN documents from user input
- **Reference Resource Analysis**: Analyze and incorporate content from reference files
- **Multi-Format Support**: Process Markdown, Text, JSON, YAML, PDF, and image files
- **Customizable Templates**: Use default templates or create custom ones
- **Cross-Document References**: Maintain consistency across related documents
- **MCP Integration**: Full Model Context Protocol support for various clients

## Supported Document Types

### PRD (Product Requirements Document)
- Introduction and project context
- Objectives and success criteria
- User stories with acceptance criteria
- Constraints and assumptions
- Dependencies and references

### SPEC (Technical Specification)
- Technical overview and architecture
- System components and interfaces
- Data models and relationships
- Implementation details and testing strategy
- Deployment considerations

### DESIGN (Design Document)
- System and UI design specifications
- Data flow and processing pipelines
- Implementation approach and patterns
- Security and performance considerations
- Design constraints and guidelines

## Installation

### Using pip

```bash
pip install document-generator-mcp
```

### From source

```bash
git clone <repository-url>
cd document-generator-mcp
pip install -e .
```

### Development installation

```bash
git clone <repository-url>
cd document-generator-mcp
pip install -e ".[dev]"
```

## Quick Start

### 1. Start the MCP Server

```bash
# Using STDIO transport (for Claude Desktop)
document-generator-mcp --transport stdio

# Using SSE transport (for web clients)
document-generator-mcp --transport sse --host localhost --port 8000
```

### 2. Configure MCP Client

#### Claude Desktop Configuration

Add to your Claude Desktop configuration file:

```json
{
  "mcpServers": {
    "document-generator": {
      "command": "document-generator-mcp",
      "args": ["--transport", "stdio"]
    }
  }
}
```

#### VS Code Configuration

Add to your VS Code settings:

```json
{
  "mcp": {
    "servers": {
      "document-generator": {
        "type": "stdio",
        "command": "document-generator-mcp",
        "args": ["--transport", "stdio"]
      }
    }
  }
}
```

### 3. Use the Tools

Once connected, you can use these MCP tools:

- `generate_prd`: Generate Product Requirements Document
- `generate_spec`: Generate Technical Specification
- `generate_design`: Generate Design Document
- `analyze_resources`: Analyze reference resources
- `list_templates`: List available templates
- `customize_template`: Customize document templates

## Usage Examples

### Generate a PRD

```python
# Through MCP client
result = generate_prd(
    user_input="Create a task management application with user authentication, task creation, and team collaboration features.",
    project_context="Web application for small teams",
    reference_folder="./reference_resources"
)
```

### Generate a SPEC from PRD

```python
result = generate_spec(
    requirements_input="Technical requirements for the task management app",
    existing_prd_path="./PRD.md",
    reference_folder="./reference_resources"
)
```

### Analyze Reference Resources

```python
analysis = analyze_resources(folder_path="./reference_resources")
print(f"Found {analysis['total_files']} files in {len(analysis['categories'])} categories")
```

## Reference Resources

The system can analyze and incorporate various file types from a `reference_resources` folder:

### Supported Formats

- **Markdown** (.md): Documentation, requirements, specifications
- **Text** (.txt): Plain text documents and notes
- **JSON** (.json): Configuration files, API specifications
- **YAML** (.yaml, .yml): Configuration files, data structures
- **PDF** (.pdf): Documents, specifications, manuals
- **Images** (.png, .jpg, .jpeg): Screenshots, diagrams, mockups (with OCR)

### File Organization

```
reference_resources/
├── requirements/
│   ├── user_stories.md
│   └── business_requirements.txt
├── technical/
│   ├── api_spec.json
│   └── architecture.yaml
├── design/
│   ├── mockups.png
│   └── style_guide.md
└── documentation/
    ├── existing_docs.md
    └── references.pdf
```

## Template Customization

### Using Default Templates

The system includes default templates for PRD, SPEC, and DESIGN documents following Kiro's best practices.

### Creating Custom Templates

Create YAML template files in your templates directory:

```yaml
# custom_prd.yaml
name: "custom_prd"
template_type: "prd"
version: "1.0"
sections:
  introduction: |
    # {title}
    
    ## Custom Introduction
    {introduction_content}
  
  objectives: |
    ## Project Objectives
    {objectives_list}
  
  # ... more sections
```

### Template Customization via API

```python
customize_template(
    template_type="prd",
    sections={
        "add": {
            "risk_assessment": "## Risk Assessment\n{risk_analysis}"
        },
        "modify": {
            "objectives": "## Enhanced Objectives\n{objectives_list}\n\n### Success Metrics\n{success_metrics}"
        },
        "remove": ["assumptions"]
    }
)
```

## Configuration

### Command Line Options

```bash
document-generator-mcp --help

Options:
  --transport {stdio,sse}   Transport protocol (default: stdio)
  --host HOST              Host for SSE transport (default: localhost)
  --port PORT              Port for SSE transport (default: 8000)
  --output-dir PATH        Output directory for documents
  --templates-dir PATH     Custom templates directory
  --log-level {DEBUG,INFO,WARNING,ERROR}  Logging level
```

### Environment Variables

```bash
export DOCUMENT_GENERATOR_OUTPUT_DIR="/path/to/output"
export DOCUMENT_GENERATOR_TEMPLATES_DIR="/path/to/templates"
export DOCUMENT_GENERATOR_LOG_LEVEL="INFO"
```

## Development

### Project Structure

```
document_generator_mcp/
├── __init__.py
├── exceptions.py
├── models/
│   ├── core.py
│   └── document_structures.py
├── processors/
│   ├── base.py
│   ├── registry.py
│   └── [format processors]
├── services/
│   ├── document_generator.py
│   ├── resource_analyzer.py
│   └── content_processor.py
├── templates/
│   ├── manager.py
│   └── defaults.py
└── server/
    ├── mcp_server.py
    ├── tools.py
    └── main.py
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=document_generator_mcp

# Run specific test categories
pytest -m unit
pytest -m integration
```

### Code Quality

```bash
# Format code
black document_generator_mcp/
isort document_generator_mcp/

# Type checking
mypy document_generator_mcp/

# Linting
flake8 document_generator_mcp/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions, please visit the project repository or contact the development team.
