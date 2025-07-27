# Testing Guide for Hybrid MCP Document Generator

This guide covers testing the upgraded MCP Document Generator that uses the hybrid prompt-based workflow.

## 🔄 What Changed After the Upgrade

### Before (Template-Based)
- Tools returned final `DocumentResult` objects with generated content
- Tests validated document structure and content directly
- Simple template filling workflow

### After (Hybrid Prompt-Based)
- Tools return `PromptResult` objects with intelligent prompts
- Claude Desktop processes prompts to generate content
- New `save_generated_document` and `validate_generated_content` tools
- Tests cover prompt generation, AI content handling, and validation

## 📁 Test Structure

```
tests/
├── conftest.py                     # Shared fixtures and configuration
├── test_basic_functionality.py     # Updated basic tests + new models
├── test_prompt_generation.py       # Prompt generation tests
├── test_ai_content_handling.py     # AI content saving/validation tests
├── test_hybrid_integration.py      # End-to-end hybrid workflow tests
├── test_mocked_hybrid_workflow.py  # Mocked workflow tests
├── test_security.py               # Security tests (existing)
└── test_integration.py            # Legacy integration tests (deprecated)
```

## 🧪 Test Categories

### 1. Basic Functionality Tests (`test_basic_functionality.py`)
**Updated for hybrid workflow**

- ✅ Import tests for new models (`PromptResult`, `AIGeneratedContent`, etc.)
- ✅ Model creation and serialization tests
- ✅ Document structure `to_dict()` method tests

```python
def test_prompt_result_creation():
    """Test creating a PromptResult for hybrid workflow."""
    prompt_result = PromptResult(
        document_type="prd",
        prompt="Create a comprehensive PRD...",
        template_structure={"introduction": "# Introduction\n{content}"},
        extracted_data={"objectives": ["Test objective"]},
        context_summary="Test context",
        suggested_filename="PRD.md"
    )
    assert prompt_result.document_type == "prd"
```

### 2. Prompt Generation Tests (`test_prompt_generation.py`)
**New test suite for intelligent prompt creation**

- ✅ PRD, SPEC, and DESIGN prompt generation
- ✅ Context analysis and data extraction
- ✅ Template integration
- ✅ Reference resource inclusion
- ✅ Prompt quality validation

```python
@pytest.mark.asyncio
async def test_prd_prompt_generation(temp_workspace):
    """Test PRD prompt generation with context analysis."""
    service = DocumentGeneratorService(output_directory=temp_workspace)
    
    result = await service.generate_prd_prompt(
        user_input="As a user, I want to login...",
        project_context="Building a secure web application",
        template_config="default_prd"
    )
    
    assert isinstance(result, PromptResult)
    assert "login" in result.prompt
    assert "secure web application" in result.prompt
```

### 3. AI Content Handling Tests (`test_ai_content_handling.py`)
**New test suite for AI-generated content processing**

- ✅ Saving AI-generated documents
- ✅ Content validation (structure, quality, completeness)
- ✅ Error handling for invalid content
- ✅ Document-specific validation rules

```python
@pytest.mark.asyncio
async def test_save_ai_generated_prd(temp_workspace, sample_prd_content):
    """Test saving AI-generated PRD content."""
    service = DocumentGeneratorService(output_directory=temp_workspace)
    
    ai_content = AIGeneratedContent(
        document_type="prd",
        content=sample_prd_content,
        filename="AI_GENERATED_PRD.md",
        validation_requested=True
    )
    
    result = await service.save_ai_generated_content(ai_content)
    assert result.file_path.exists()
```

### 4. Hybrid Integration Tests (`test_hybrid_integration.py`)
**New end-to-end tests for complete workflow**

- ✅ Complete PRD workflow: prompt → AI content → saving
- ✅ SPEC workflow with existing PRD reference
- ✅ DESIGN workflow with complete document chain
- ✅ Validation error handling
- ✅ Workflow error scenarios

```python
@pytest.mark.asyncio
async def test_complete_prd_workflow(temp_workspace):
    """Test complete PRD workflow: prompt generation → AI content → saving."""
    service = DocumentGeneratorService(output_directory=temp_workspace)
    
    # Step 1: Generate prompt
    prompt_result = await service.generate_prd_prompt(...)
    
    # Step 2: Simulate AI response
    mock_ai_response = """# Product Requirements Document..."""
    
    # Step 3: Save AI content
    ai_content = AIGeneratedContent(...)
    save_result = await service.save_ai_generated_content(ai_content)
    
    assert save_result.file_path.exists()
```

### 5. Mocked Workflow Tests (`test_mocked_hybrid_workflow.py`)
**New tests using mocks to simulate complete workflows**

- ✅ Mocked AI responses for testing
- ✅ MCP tools integration testing
- ✅ Error scenario simulation
- ✅ Concurrent workflow testing
- ✅ Resource analysis mocking

```python
@pytest.mark.asyncio
async def test_mocked_end_to_end_prd_workflow(temp_workspace, mocker):
    """Test complete PRD workflow with mocked AI response."""
    service = DocumentGeneratorService(output_directory=temp_workspace)
    
    # Mock resource analyzer
    mocker.patch.object(service.resource_analyzer, 'analyze_folder', ...)
    
    # Test real prompt generation + mocked AI response + real saving
    prompt_result = await service.generate_prd_prompt(...)
    # ... simulate AI response and test saving
```

## 🔧 Running Tests

### Quick Test Run
```bash
# Run all tests
python run_tests.py

# Run specific test category
python -m pytest tests/test_prompt_generation.py -v

# Run with coverage
python -m pytest --cov=document_generator_mcp tests/
```

### Test Markers
```bash
# Run only hybrid workflow tests
python -m pytest -m hybrid

# Run only prompt generation tests  
python -m pytest -m prompt

# Run only AI content tests
python -m pytest -m ai_content

# Skip slow tests
python -m pytest -m "not slow"
```

### Debug Mode
```bash
# Run with detailed output
python -m pytest tests/ -v -s

# Run single test with debugging
python -m pytest tests/test_prompt_generation.py::TestPromptGeneration::test_prd_prompt_generation -v -s
```

## 🎯 Key Testing Patterns

### 1. Async Testing
All service methods are async, so use `@pytest.mark.asyncio`:

```python
@pytest.mark.asyncio
async def test_async_method():
    result = await service.some_async_method()
    assert result is not None
```

### 2. Mocking with pytest-mock
Use the `mocker` fixture for clean mocking:

```python
def test_with_mock(mocker):
    mock_method = mocker.patch.object(service, 'method_name')
    mock_method.return_value = "mocked_result"
    
    result = service.call_method()
    assert result == "mocked_result"
```

### 3. Fixture Usage
Leverage shared fixtures from `conftest.py`:

```python
def test_with_fixtures(temp_workspace, sample_prd_structure):
    # temp_workspace provides clean directory
    # sample_prd_structure provides test data
    assert temp_workspace.exists()
    assert len(sample_prd_structure.objectives) > 0
```

## 🚨 Common Issues and Solutions

### Issue: Import Errors for New Models
**Solution:** Ensure new models are exported in `__init__.py` files

### Issue: Async Test Failures
**Solution:** Use `@pytest.mark.asyncio` decorator and `await` for async calls

### Issue: Template Not Found Errors
**Solution:** Use correct template names (`default_prd`, `default_spec`, `default_design`)

### Issue: Mock Not Working
**Solution:** Patch the correct object path and use `mocker.patch.object()`

## 📊 Coverage Goals

- **Overall Coverage:** > 90%
- **New Hybrid Features:** > 95%
- **Critical Paths:** 100% (prompt generation, content saving)

## 🔄 Migration from Old Tests

If you have existing tests that expect the old workflow:

1. **Update return type expectations:** `DocumentResult` → `PromptResult`
2. **Update method calls:** `generate_prd()` → `generate_prd_prompt()`
3. **Add AI content simulation:** Mock the AI response step
4. **Update assertions:** Test prompt content instead of final document

## 🎉 Success Criteria

Tests pass when:
- ✅ All prompt generation produces valid, substantial prompts
- ✅ AI content saving works with validation
- ✅ Error handling works correctly
- ✅ Integration workflows complete successfully
- ✅ Security and validation rules are enforced

The upgraded testing suite ensures the hybrid MCP Document Generator works reliably with Claude Desktop while maintaining code quality and security standards.
