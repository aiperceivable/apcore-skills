### Shared Conformance Fixtures

Use the selected package's discovered `conformance_path` and `path`. Core
packages share `apcore/conformance/`. Each Surface component has a suite under
`apcore-surfaces/<component>/conformance/`. Resolve relative fixture paths from
that suite root. A Core or Surface suite can define its own JSON case schema.

#### Inventory

Read the suite's existing drivers and its `README.md` and schema when present. Inventory
JSON cases under `fixtures/` and any other locations named by the suite. Treat
files such as YAML bindings or OpenAPI documents as inputs when a driver refers
to them. Use a case ID or name supplied in the fixture. When absent, use the JSON
pointer to the case as its ID. Key a cross-language result by suite, relative
fixture path, and case ID. Compare only implementations that share the suite.

When a fixture or driver identifies a normative assertion, check that its cases
exercise the applicable inputs, errors and properties from the Contract. Report
coverage gaps at the fixture path and cite the relevant Contract clause.

#### Run the Package's Tests

Use the native fixture-driven tests under the package path. Read the owning
checkout's CI workflow for the full setup and invocation, including the Surface
toolkit dependency from the same checkout where CI links it. Typical entry
points include pytest test files, Vitest files through pnpm, and Cargo
integration test targets. Select test files by the canonical fixtures they load.
When a driver accepts a fixture override, set it for the test process to the
discovered fixture directory. For example, MCP drivers accepting
`APCORE_CONFORMANCE_FIXTURES` receive `<conformance_path>/fixtures`. Confirm the
loaded path before recording results from a driver with directory fallbacks.
For a test or driver that runs multiple cases, use parameter IDs or verify from
its source and run output which cases executed and which expectations were
asserted. A checkout-verification test alone only proves fixture availability.

Record the command and suite status, then capture each provable case outcome as
`PASS`, `FAIL`, `SKIPPED`, `UNSUPPORTED`, or `ERROR`. Mark a case `UNVERIFIED`
when the available evidence does not identify its outcome. A missing test entry
point, dependency error or timeout is a suite gap. An aggregate pass alone
does not prove that every listed case passed.

#### Adapters and New SDKs

Port the reference package's native fixture-driven tests to the new SDK's test
framework and load the same suite data. Keep case IDs visible in parameterized
test names or diagnostics. Existing adapters that emit `CONFORMANCE_CASE`
blocks can continue to report `file`, `case_id`, `status`, `details`, and
`duration_ms`. The `file` field is relative to the suite root. Keep optional
`method` and assertion details when the driver supplies them.

`tester` compares proven outcomes for the same case in Matrix B. A mixed
PASS/FAIL is a behavioral divergence. Treat missing execution and unverified
case outcomes as coverage gaps and report them separately from divergences.
