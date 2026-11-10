# Security Guide for Document Generator MCP

This document outlines the security measures implemented in the Document Generator MCP and provides guidance for secure deployment and usage.

## Security Features

### 1. Input Validation and Sanitization

The system implements comprehensive input validation to prevent injection attacks:

- **User Input Validation**: All user inputs are validated for length, content, and dangerous patterns
- **Path Validation**: File paths are validated to prevent directory traversal attacks
- **Template Validation**: Template configurations are validated against allowed values
- **Content Sanitization**: All content is sanitized to remove potentially dangerous elements

```python
# Example: User input is automatically validated
validated_input = validate_user_input(user_input, max_length=50000)
```

### 2. Path Security

Protection against path traversal and unauthorized file access:

- **Directory Traversal Prevention**: Blocks `../` and similar path traversal attempts
- **Base Directory Restriction**: Restricts file access to allowed directories only
- **Path Normalization**: Normalizes paths to prevent bypass attempts
- **Safe Path Joining**: Secure path joining that prevents escaping base directories

```python
# Example: Secure path validation
safe_path = validate_file_access(file_path, base_directory=allowed_base)
```

### 3. Template Security

Prevention of template injection attacks:

- **Template Injection Prevention**: Blocks dangerous template patterns
- **Safe Placeholder Validation**: Only allows safe placeholder formats
- **Template Structure Validation**: Validates template structure and content
- **Context Sanitization**: Sanitizes template context variables

### 4. Content Security

Protection against content-based attacks:

- **HTML Sanitization**: Removes or escapes dangerous HTML elements
- **Script Blocking**: Prevents execution of embedded scripts
- **Content Pattern Detection**: Detects and blocks suspicious content patterns
- **Anomaly Detection**: Identifies unusual content characteristics

### 5. Resource Protection

Limits to prevent resource exhaustion:

- **File Size Limits**: Maximum file size restrictions (50MB default)
- **Processing Time Limits**: Maximum processing time (3 minutes default)
- **Concurrent Processing Limits**: Maximum concurrent file processing
- **Memory Usage Limits**: Memory usage restrictions
- **Rate Limiting**: Request rate limiting (30 requests/minute default)

### 6. Secure Logging

Security-focused logging that doesn't leak sensitive information:

- **Sensitive Data Filtering**: Automatically removes passwords, tokens, and keys from logs
- **Log Sanitization**: Sanitizes log messages to prevent log injection
- **Security Event Logging**: Logs security-relevant events for monitoring
- **Structured Logging**: Uses structured logging format for better analysis

### 7. Error Handling Security

Secure error handling that doesn't expose sensitive information:

- **Generic Error Messages**: Shows generic error messages to users
- **Detailed Internal Logging**: Logs detailed errors internally for debugging
- **Error Classification**: Classifies errors by security relevance
- **Recovery Suggestions**: Provides safe recovery suggestions

## Security Configuration

### Default Security Settings

The system uses secure defaults:

```yaml
# Secure defaults
max_input_length: 50000
max_file_size: 52428800  # 50MB
restrict_to_base_directory: true
allow_absolute_paths: false
enable_content_sanitization: true
enable_template_validation: true
expose_detailed_errors: false
log_user_input: false
```

### Production Security Configuration

For production deployments, use even more restrictive settings:

```yaml
# Production settings
max_input_length: 25000
max_file_size: 26214400  # 25MB
max_concurrent_files: 3
max_requests_per_minute: 20
expose_detailed_errors: false
```

## Deployment Security

### 1. Network Security

- **Bind to Localhost**: By default, bind only to `127.0.0.1`
- **Use HTTPS**: Enable HTTPS for production deployments
- **Security Headers**: Implement HTTP security headers
- **Firewall Rules**: Configure appropriate firewall rules

### 2. File System Security

- **Restrictive Permissions**: Use restrictive file permissions (600/700)
- **Separate Directories**: Use separate directories for different file types
- **Regular Cleanup**: Implement regular cleanup of temporary files
- **Backup Security**: Secure backup procedures

### 3. Process Security

- **Resource Limits**: Set appropriate resource limits
- **User Privileges**: Run with minimal required privileges
- **Process Isolation**: Use process isolation where possible
- **Core Dump Disable**: Disable core dumps to prevent information leakage

## Security Monitoring

### 1. Security Events

The system logs various security events:

- Input validation failures
- Path traversal attempts
- Template injection attempts
- File access violations
- Rate limit violations
- Authentication failures (if implemented)

### 2. Monitoring Setup

```python
# Enable security monitoring
from document_generator_mcp.security import log_security_event

log_security_event("suspicious_activity", {
    "event_type": "path_traversal_attempt",
    "attempted_path": "../../etc/passwd",
    "client_ip": "192.168.1.100"
}, severity="WARNING")
```

### 3. Alert Thresholds

Configure alerts for:
- Multiple failed validation attempts
- Repeated suspicious patterns
- Resource usage spikes
- Error rate increases

## Security Testing

### 1. Automated Security Testing

Run security tests regularly:

```bash
# Run security tests
pytest tests/test_security.py -v

# Run with Bandit security scanner
bandit -r document_generator_mcp/

# Run with Semgrep
semgrep --config=auto document_generator_mcp/
```

### 2. Manual Security Testing

Perform manual testing for:
- Path traversal attempts
- Template injection attempts
- Input validation bypass attempts
- Resource exhaustion attacks

## Incident Response

### 1. Security Incident Detection

Monitor for:
- Unusual error patterns
- Repeated validation failures
- Suspicious file access patterns
- Resource usage anomalies

### 2. Response Procedures

1. **Immediate Response**:
   - Log the incident
   - Block suspicious sources if possible
   - Preserve evidence

2. **Investigation**:
   - Analyze logs
   - Determine scope of impact
   - Identify root cause

3. **Recovery**:
   - Apply fixes
   - Update security measures
   - Monitor for recurrence

## Security Updates

### 1. Dependency Updates

Regularly update dependencies:

```bash
# Check for security updates
pip-audit

# Update dependencies
pip install --upgrade -r requirements.txt
```

### 2. Security Patches

- Monitor security advisories
- Apply patches promptly
- Test patches in staging environment
- Document all security updates

## Best Practices

### 1. For Developers

- Always validate inputs
- Use parameterized queries/templates
- Follow secure coding practices
- Regular security code reviews
- Keep dependencies updated

### 2. For Operators

- Use secure configurations
- Monitor security logs
- Regular security assessments
- Implement proper access controls
- Maintain incident response procedures

### 3. For Users

- Use strong authentication
- Don't include sensitive data in inputs
- Report suspicious behavior
- Follow organizational security policies

## Security Contacts

For security issues:

1. **Security Vulnerabilities**: Report to security team
2. **Security Questions**: Contact development team
3. **Incident Response**: Follow organizational procedures

## Compliance

This system implements security measures aligned with:

- OWASP Top 10 security risks
- NIST Cybersecurity Framework
- Industry best practices for secure software development

## Security Checklist

Before deployment, verify:

- [ ] Input validation enabled
- [ ] Path security configured
- [ ] Template injection prevention active
- [ ] Content sanitization enabled
- [ ] Resource limits set
- [ ] Secure logging configured
- [ ] Error handling secured
- [ ] Security monitoring enabled
- [ ] Regular security testing scheduled
- [ ] Incident response plan ready

## Additional Resources

- [OWASP Security Guidelines](https://owasp.org/)
- [Python Security Best Practices](https://python.org/dev/security/)
- [Bandit Security Scanner](https://bandit.readthedocs.io/)
- [Semgrep Security Rules](https://semgrep.dev/)

---

**Note**: Security is an ongoing process. Regularly review and update security measures as threats evolve.
