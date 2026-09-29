# CODMA-A3 QuantStudio Parser
 
This script converts QuantStudio multicomponent export files and a plate-layout CSV into grouped replicate files and a combined Excel workbook for downstream CODMA-A3 analysis.
 
## Requirements
 
- Python (pick flavor)
- pandas
 
Install pandas if needed:
 
pip install pandas
 
## Input Files
 
Place the following files in the same directory as the script:
 
- One QuantStudio multicomponent export (`.txt`)
	HEADER LINES MUST BE DELETED
- One plate-layout file (`.csv`)
 
The script expects exactly one `.txt` and one `.csv` file. If additional files are present it will stop with an error.

NOTE: The input multicomponent file must be in plain text with all numbers in the format of 123456789 exported as a tab delimited txt file. ANY DEVIATIONS, i.e. decimals and commas in your cell strings will have unhappy results.
 
## Running
 
Run from the command line:
 
python CODMA.py
 
## Workflow
 
The script:
 
1. Reads the QuantStudio multicomponent export.
2. Splits data into individual well files.
3. Matches wells to sample IDs using the plate-layout CSV.
4. Combines technical replicates.
5. Generates a multi-sheet Excel workbook (`combined.xlsx`).
 
## Output
 
A folder named after the QuantStudio export file (.txt) is created containing:
 
- Original `.txt` file
- Original `.csv` file
- `combined.xlsx`
 
## Example Files
 
`Synthetic_Data.xlsx` demonstrates:
 
- Example plate layout (Plate layout - .csv file)
- Example QuantStudio input (Cleaned input (tsv txt file)
- Example parser output (A3 example)
- Example downstream calculations (A3 example)
 
The data are synthetic and provided only to demonstrate workflow structure.
 
## Notes
 
The script was developed for the CODMA-A3 workflow described in:
 
Rorex C., Springman-Rodriguez R., Mendez A.D., Lehle J.D., Ebrahimi D.
*Competitive Oligo-Based DNA Modification Assay Applied to APOBEC Enzymes.*
 
No warranties are provided. If the script breaks, I sure can't help you - Colin.
