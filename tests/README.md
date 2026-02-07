# Tests Directory

This directory contains all test files for the AWS RAG Bot project.

## Structure

```
tests/
├── unit/               # Unit tests for individual components
│   ├── test_chunking.py
│   └── test_security.py
└── integration/        # Integration tests (future)
```

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run Unit Tests Only

```bash
pytest tests/unit/ -v
```

### Run Specific Test File

```bash
pytest tests/unit/test_chunking.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=backend --cov-report=html
```

## Writing Tests

### Unit Test Example

```python
# tests/unit/test_example.py
import pytest
from backend.services.example import ExampleService

def test_example_function():
    service = ExampleService()
    result = service.process("test")
    assert result == "expected_output"
```

### Async Test Example

```python
import pytest
from backend.services.async_example import AsyncService

@pytest.mark.asyncio
async def test_async_function():
    service = AsyncService()
    result = await service.async_process("test")
    assert result == "expected_output"
```

## Test Configuration

Test configuration is managed in `conftest.py` (to be created).

## Coverage Goals

- Unit tests: 80%+ coverage
- Integration tests: Critical paths covered
- E2E tests: Main user flows covered

## Future Tests

- [ ] API endpoint tests
- [ ] Vector store tests
- [ ] Cloud provider integration tests
- [ ] LLM service tests
- [ ] Document processor tests
