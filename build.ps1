# Build a Nuitka executable for the project.
python -m nuitka --onefile `
    --output-dir=build `
    --include-data-files=./setting.yaml=setting.yaml `
    --jobs=8 `
    --verbose `
    ./src/main.py