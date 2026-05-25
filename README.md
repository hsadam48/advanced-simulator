# VT Engineering Review Platform — Advanced

This is the merged version of:

1. Your professional single-file VT engineering review app.
2. The modular advanced traffic analysis / simulation architecture.

## Features

- Project information page
- Company logo upload
- Project photo upload
- Tower and lift bank data editor
- Benchmark engine
- Pass/fail engineering review
- Recommendation engine
- Advanced Monte Carlo-style simulation engine
- Excel export
- PDF export
- CSV export
- Modular Python structure

## Structure

```text
vt-engineering-review-advanced/
├── .streamlit/
│   └── config.toml
├── app.py
├── core/
│   ├── models.py
│   ├── kinematics.py
│   ├── benchmark_engine.py
│   ├── analytical_engine.py
│   ├── simulation_engine.py
│   └── data_cleaning.py
├── reporting/
│   ├── pdf_generator.py
│   └── excel_generator.py
├── data/
│   └── default_banks.json
├── requirements.txt
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Recommended Workflow

1. Fill project information.
2. Add/edit tower and lift bank inputs.
3. Run advanced simulation if required.
4. Generate results.
5. Download Excel/PDF/CSV reports.

## Important

This is a preliminary engineering review and traffic simulation support tool.
Final VT design, authority submission, fire/life-safety compliance, shaft dimensions,
and traffic performance must be confirmed by the elevator specialist/manufacturer.