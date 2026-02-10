# Project Constitution

## Data Schemas
> [!IMPORTANT]
> **Core Data Structure**

### Input Payload
```json
{
  "source_code": "String (Raw Selenium Java Code with TestNG annotations)",
  "output_directory": "String (Target directory for generated files, optional)",
  "options": {
    "framework": "Playwright",
    "language": "TypeScript"
  }
}
```

### Output Payload
```json
{
  "converted_code": "String (Playwright TypeScript Code)",
  "file_path": "String (Absolute path where file is saved)",
  "status": "success | error",
  "conversion_notes": "String (Explanation of changes or warnings)"
}
```

## Behavioral Rules
> [!NOTE]
> **Guiding Principles**
1.  **Readability First**: Prioritize readable, idiomatic Playwright/TypeScript code over strict 1:1 line mapping from Java.
2.  **TestNG to Playwright**: Convert TestNG annotations (`@Test`, `@BeforeClass`, etc.) to their Playwright equivalents (`test`, `test.beforeAll`, etc.).
3.  **UI Feedback**: The system must display the converted code in the User Interface.
4.  **File Persistence**: The converted code must also be saved to a new directory.

## Architectural Invariants
> [!IMPORTANT]
> 1.  **Input Source**: User Interface (Text Area).
> 2.  **Output Targets**: Dual target - UI Display AND File System.
> 3.  **Language Target**: TypeScript (preferred over JS for Playwright best practices).
> 4.  **AI Engine**: Ollama (Local) running `codellama`.

## Maintenance Log
- [x] Project Initialized.
- [x] Discovery Phase Completed. Schemas Defined.
- [x] Phase 1 completed. Architecture chosen (Flask + Ollama).
