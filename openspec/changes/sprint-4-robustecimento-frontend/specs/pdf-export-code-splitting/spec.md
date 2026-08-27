## ADDED Requirements

### Requirement: PDF export libraries load only when the user exports
The system SHALL load `jsPDF` and `html2canvas` via dynamic `import()` at the moment the user triggers PDF export, not as part of the initial page bundle.

#### Scenario: Loading the Home page does not load PDF libraries
- **WHEN** a user loads the Home page without clicking "Exportar PDF"
- **THEN** `jsPDF` and `html2canvas` are not present in the JavaScript already downloaded

#### Scenario: Clicking export loads and uses the libraries
- **WHEN** a user clicks "Exportar PDF"
- **THEN** the system loads `jsPDF`/`html2canvas` on demand and produces the PDF as before
