# End-User Testing Guide (Full MCP Integration)

## Prerequisites
1. **Install the package**: `pip install -e .` in the project directory
2. **Have Claude Desktop installed** (or another MCP-compatible client)

## Step 1: Configure Claude Desktop
1. Open Claude Desktop settings
2. Add this to your MCP configuration:
```json
{
  "mcpServers": {
    "document-generator": {
      "command": "document-generator-mcp",
      "args": ["--transport", "stdio", "--output-dir", "./generated_docs"],
      "env": {
        "DOCUMENT_GENERATOR_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Step 2: Restart Claude Desktop
Close and reopen Claude Desktop to load the MCP server.

## Step 3: Test the Full Workflow

**In Claude Desktop chat, try these commands:**

1. **Generate a PRD:**
```
Use the generate_prd tool to create a product requirements document for a mobile fitness tracking app with features like workout logging, progress tracking, and social sharing.
```

2. **Analyze reference resources:**
```
Use the analyze_resources tool to check what reference materials are available in the reference_resources folder.
```

3. **Save AI-generated content:**
```
After I generate content, use the save_generated_document tool to save it as PRD.md with validation enabled.
```

## Step 4: Expected End-User Experience

1. **You ask Claude** to generate a document
2. **Claude calls the MCP tool** (generate_prd, generate_spec, etc.)
3. **MCP returns an intelligent prompt** with structured guidance
4. **Claude processes the prompt** and generates high-quality content
5. **Claude calls save_generated_document** to save the final result
6. **You get a professional document** in your specified output directory

## Step 5: Verify Success

Check the `./generated_docs` folder for:
- PRD.md, SPEC.md, or DESIGN.md files
- Properly formatted markdown with sections
- Content that incorporates your requirements and any reference materials

The key difference from local testing is that you're experiencing the full AI-enhanced workflow where Claude's intelligence is guided by the MCP's structured prompts to create much better documents than either could produce alone.