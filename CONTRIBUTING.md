# Contributing to Torre Control

## Welcome! 👋

Torre Control is an open-source data warehouse and analytics platform for supply chain intelligence. We welcome contributions from data engineers, analysts, and developers.

---

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and grow
- Report issues responsibly

---

## How to Contribute

### 1. Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/Torre_Control.git
cd Torre_Control

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install pandas sqlalchemy psycopg2-binary

# Verify PostgreSQL is running
docker ps | grep supply_chain_db
```

### 2. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# Or for bug fixes:
git checkout -b fix/issue-description
```

**Branch naming conventions:**
- `feature/description` - New features
- `fix/issue-number` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code improvements
- `test/description` - Test additions

### 3. Make Your Changes

- Follow PEP 8 for Python code
- Add comments for complex logic
- Test your changes thoroughly
- Update documentation as needed

### 4. Commit Your Work

```bash
git add .
git commit -m "feat: Add feature description"
# Or:
git commit -m "fix: Resolve issue #123"
git commit -m "docs: Update README"
```

**Commit message format:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `refactor:` - Code refactoring
- `test:` - Test additions
- `chore:` - Maintenance

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title describing the change
- Detailed description of what changed and why
- Reference to any related issues (#123)
- Before/after screenshots if applicable

---

## Development Workflow

### SQL Development

**Location:** `src/sql/`

1. Test queries locally in PostgreSQL
2. Name files descriptively: `01_feature_name.sql`
3. Add comments explaining complex logic
4. Include expected row counts in comments

```sql
-- Description of what this query does
-- Expected result: 186,638 rows
SELECT COUNT(*) FROM dw.fact_orders;
```

### Python Development

**Location:** `src/etl/`

1. Follow PEP 8 style guide
2. Add docstrings to functions
3. Include error handling
4. Test with sample data

```python
def load_data_to_database(csv_path, chunk_size=50000):
    """
    Load CSV data to PostgreSQL database.
    
    Args:
        csv_path (str): Path to CSV file
        chunk_size (int): Number of rows per batch
    
    Returns:
        int: Number of rows loaded
    """
    # Implementation here
    pass
```

### Documentation

**Location:** `docs/`

1. Use Markdown formatting
2. Include code examples
3. Keep language clear and concise
4. Update table of contents if adding sections

---

## Testing

Before submitting a PR, test:

```bash
# SQL: Verify query returns expected row counts
docker exec supply_chain_db psql -U admin -d supply_chain_dw -f src/sql/your_query.sql

# Python: Run your ETL script
python src/etl/your_script.py

# Data validation: Check for NULLs, duplicates, type mismatches
SELECT COUNT(*) FROM dw.fact_orders WHERE order_key IS NULL;
```

---

## Pull Request Checklist

- [ ] Branch created from `main`
- [ ] Code follows project style guidelines
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No large data files committed
- [ ] All tests passing locally
- [ ] Changes validated in PostgreSQL
- [ ] Commit messages follow convention

---

## Areas for Contribution

### High Priority
- [ ] Phase 4: Power BI dashboard completion
- [ ] Advanced SQL: Predictive models
- [ ] Documentation: API reference
- [ ] Tests: Data quality validations

### Medium Priority
- [ ] Performance optimization
- [ ] Additional visualizations
- [ ] Code refactoring
- [ ] Example datasets

### Low Priority
- [ ] README improvements
- [ ] Comment enhancements
- [ ] Formatting fixes

---

## Questions?

- Check `docs/guides/` for existing documentation
- Open an issue with the `question` label
- Reach out in discussions

---

## License

By contributing, you agree your code will be licensed under the MIT License.

**Thank you for contributing to Torre Control! 🚀**
