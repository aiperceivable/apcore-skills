# Audit Implementation Repo — Sub-agent Prompt Template

Variables to fill: `{impl_repo_path}`, `{verified_api}`

---

Audit documentation in {impl_repo_path} for consistency with the verified API surface.

This is an IMPLEMENTATION REPO. It should contain only code and a README (plus optional examples).
It does NOT contain PRD/SRS/Tech Design/Test Plan/Feature Specs.

VERIFIED API (ground truth from Phase A):
{verified_api for this repo — the confirmed-correct API symbols, signatures, types}

=== SCOPE 1: README ===

1. Read README.md
2. Check required sections: Title/badges, Description, Installation, Quick Start, Features, API Overview, Docs link, License
3. For Installation: verify package name matches build config (pyproject.toml/package.json)
4. For Quick Start code examples: extract all API references, verify they match verified API
   - Import names correct?
   - Class names correct?
   - Method names correct?
   - Parameter names and order correct?
5. For API Overview: verify listed classes/functions exist in verified API with correct descriptions
6. For version references: verify they match current version in build config

=== SCOPE 2: API References in Markdown ===

Search ALL markdown files in the repo (README.md, docs/**/*.md) for API symbol references:
1. For EACH symbol reference found:
   a. Does the symbol exist in the verified API?
   b. Do parameter names/order match the verified signature?
   c. Are import paths correct?
   d. Are return types correctly described?
2. Cross-check: do different markdown files contradict each other?
   - If README says `get_module(id)` but docs/usage.md says `get_module(module_id)` → CONTRADICTION

=== SCOPE 3: Example Code ===

1. Scan examples/, demo/, example/ directories
2. For each example source file (*.py, *.ts, *.js):
   a. Extract import statements and API usage
   b. Cross-reference against verified API — correct class names, method names, params?
   c. Check dependency versions reference correct SDK version
3. Check example README exists with setup instructions
4. Build an inventory of example scenarios (list each example by purpose/scenario name):
   - e.g., "basic_usage", "custom_config", "middleware_chain", "error_handling"
   - Include this inventory in the EXAMPLES section of the return format below

=== SCOPE 4: Test Consistency ===

1. Scan tests/, test/, __tests__/, spec/ directories
2. Build a test scenario inventory:
   a. For each test file, extract:
      - Test file name (normalized: test_registry.py → registry, registry.test.ts → registry)
      - Test case names/descriptions (normalized to snake_case for comparison)
      - API symbols under test (which classes/functions/methods each test exercises)
   b. Group by feature area (registry, executor, config, etc.)
   c. For parameterized/table-driven tests, expand each parameter set as a separate scenario in the inventory. For pytest.mark.parametrize, each parameter tuple is one scenario. For test.each/it.each, each row is one scenario. This ensures fair cross-language comparison.
3. Cross-reference test API usage against verified API:
   a. Are class names, method names, and params correct?
   b. Are deprecated or renamed APIs still used in tests?
4. Include all extracted data in the TESTS section of the return format below

=== SCOPE 5: Cross-Document Contradiction Detection ===

For every API symbol mentioned in more than one place within this repo:
1. Collect all references (file, line, what it says)
2. Compare: do all references agree on name, params, behavior?
3. Flag any contradictions between documents

Return findings in this exact format:
REPO: {repo-name}

README:
  SECTIONS_PRESENT: {list}
  SECTIONS_MISSING: {list}
  API_MISMATCHES: {list of references that don't match verified API}
  VERSION_MISMATCHES: {list}
  INSTALL_CORRECT: true|false

API_REFS:
  REFERENCES_CHECKED: {N}
  MISMATCHES: {N}

EXAMPLES:
  EXAMPLE_DIRS: {list or "none"}
  MISMATCHES: {N}
  SCENARIO_INVENTORY:
  - {scenario_name}: {brief description}
  - ...

TESTS:
  TEST_DIRS: {list or "none"}
  TOTAL_TEST_FILES: {N}
  TOTAL_TEST_CASES: {N}
  API_MISMATCHES: {N}
  FEATURE_AREAS: {list with test counts}
  SCENARIO_INVENTORY:
  - area: {feature_area}
    tests: [{test_name_1}, {test_name_2}, ...]
  - ...

CONTRADICTIONS: {N}
  {list of cases where different docs within this repo say different things}

FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  scope: {readme|api-refs|examples|tests|contradiction}
  detail: {description}
  location: {file:section or file:line}
  verified_api_says: {correct value from Phase A}
  doc_says: {what the doc currently says}
  fix: {suggested fix}

Error handling:
- If the repo path does not exist, return: REPO: {repo-name}, STATUS: NOT_FOUND
- If README.md is missing, report SECTIONS_PRESENT: [], SECTIONS_MISSING: ["all"], and continue checking other scopes
- If no markdown files are found, skip API_REFS scope and report REFERENCES_CHECKED: 0
- If no example directories exist, report EXAMPLE_DIRS: "none", MISMATCHES: 0, SCENARIO_INVENTORY: []
- If no test directories exist, report TEST_DIRS: "none", TOTAL_TEST_FILES: 0, TOTAL_TEST_CASES: 0, SCENARIO_INVENTORY: []
