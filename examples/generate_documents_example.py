#!/usr/bin/env python3
"""
Example script demonstrating how to use the Document Generator MCP
to generate PRD, SPEC, and DESIGN documents.

This script shows how to use the document generation services directly
without going through the MCP protocol.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from document_generator_mcp.services.document_generator import DocumentGeneratorService


async def main():
    """Main example function."""
    print("Document Generator MCP - Example Usage")
    print("=" * 50)
    
    # Create output directory
    output_dir = Path("./example_output")
    output_dir.mkdir(exist_ok=True)
    
    # Initialize the document generator service
    service = DocumentGeneratorService(output_directory=output_dir)
    
    print(f"Output directory: {output_dir.absolute()}")
    print(f"Service statistics: {service.get_generation_statistics()}")
    print()
    
    # Example 1: Generate a PRD
    print("1. Generating PRD...")
    prd_input = """
    Create a mobile task management application with the following features:
    
    Core Features:
    - User registration and authentication
    - Create, edit, and delete tasks
    - Set task priorities and due dates
    - Organize tasks into projects
    - Team collaboration and task assignment
    - Push notifications for deadlines
    - Offline synchronization
    
    Target Users:
    - Individual professionals
    - Small to medium teams
    - Project managers
    
    Business Goals:
    - Increase productivity for remote teams
    - Provide intuitive task organization
    - Enable seamless collaboration
    - Support both iOS and Android platforms
    
    Success Metrics:
    - User engagement and retention
    - Task completion rates
    - Team collaboration metrics
    - App store ratings
    """
    
    try:
        prd_result = await service.generate_prd(
            user_input=prd_input,
            project_context="Mobile application for productivity and team collaboration",
            reference_folder="./reference_resources"  # This folder may not exist, which is fine
        )
        
        print(f"✓ PRD generated: {prd_result.file_path}")
        print(f"  Summary: {prd_result.summary}")
        print(f"  Sections: {', '.join(prd_result.sections_generated)}")
        print()
        
    except Exception as e:
        print(f"✗ PRD generation failed: {e}")
        return
    
    # Example 2: Generate a SPEC based on the PRD
    print("2. Generating SPEC...")
    spec_input = """
    Technical specification for the mobile task management application.
    
    Architecture Requirements:
    - RESTful API backend
    - Mobile-first responsive design
    - Real-time synchronization
    - Offline-first architecture
    - Push notification system
    - User authentication and authorization
    
    Technology Stack:
    - Backend: Node.js with Express
    - Database: PostgreSQL with Redis for caching
    - Mobile: React Native for cross-platform development
    - Authentication: JWT tokens
    - Real-time: WebSocket connections
    - Push notifications: Firebase Cloud Messaging
    
    Performance Requirements:
    - API response time < 200ms
    - Offline sync within 30 seconds when online
    - Support for 10,000+ concurrent users
    - 99.9% uptime availability
    """
    
    try:
        spec_result = await service.generate_spec(
            requirements_input=spec_input,
            existing_prd_path=str(prd_result.file_path),
            reference_folder="./reference_resources"
        )
        
        print(f"✓ SPEC generated: {spec_result.file_path}")
        print(f"  Summary: {spec_result.summary}")
        print(f"  Sections: {', '.join(spec_result.sections_generated)}")
        print()
        
    except Exception as e:
        print(f"✗ SPEC generation failed: {e}")
        return
    
    # Example 3: Generate a DESIGN based on the SPEC
    print("3. Generating DESIGN...")
    design_input = """
    Design document for the mobile task management application.
    
    User Interface Design:
    - Clean, minimalist interface
    - Material Design principles for Android
    - Human Interface Guidelines for iOS
    - Dark mode support
    - Accessibility compliance (WCAG 2.1)
    
    User Experience Flow:
    - Onboarding flow for new users
    - Quick task creation with minimal steps
    - Intuitive navigation between projects
    - Gesture-based interactions (swipe, drag)
    - Smart notifications that don't overwhelm
    
    Design System:
    - Consistent color palette
    - Typography hierarchy
    - Icon library
    - Component library
    - Animation guidelines
    
    Implementation Approach:
    - Component-based architecture
    - Responsive design patterns
    - Progressive enhancement
    - Performance optimization
    - Cross-platform consistency
    """
    
    try:
        design_result = await service.generate_design(
            specification_input=design_input,
            existing_spec_path=str(spec_result.file_path),
            reference_folder="./reference_resources"
        )
        
        print(f"✓ DESIGN generated: {design_result.file_path}")
        print(f"  Summary: {design_result.summary}")
        print(f"  Sections: {', '.join(design_result.sections_generated)}")
        print()
        
    except Exception as e:
        print(f"✗ DESIGN generation failed: {e}")
        return
    
    # Summary
    print("Document Generation Complete!")
    print("=" * 50)
    print(f"Generated documents in: {output_dir.absolute()}")
    print("Files created:")
    for file_path in output_dir.glob("*.md"):
        size = file_path.stat().st_size
        print(f"  - {file_path.name} ({size:,} bytes)")
    
    print("\nYou can now:")
    print("1. Review the generated documents")
    print("2. Edit them as needed")
    print("3. Use them as templates for future projects")
    print("4. Integrate with your development workflow")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExample interrupted by user")
    except Exception as e:
        print(f"\nExample failed: {e}")
        sys.exit(1)
