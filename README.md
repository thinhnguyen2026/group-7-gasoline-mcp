# Group 7 Gasoline MCP Project

**Members:** Thinh Nguyen, Timmy Nguyen, Aman Patel, Joseph Francolino.

This classroom project connects an Ollama model to published U.S. gasoline prices through MCP tools, Flask APIs, MongoDB, and Redis.

## Included files

- `code/`: source code, pinned Python dependencies, and local database configuration.
- `code/data/`: the saved EIA source pages, extracted annual records, and provenance.
- `code/results/`: recorded direct checks and actual Ollama responses, including failures.
- `SOURCES.txt`: original source links, units, and limitations.

The report, slides, and presentation practice script are not part of this repository.

## Data and recorded results

The source is the U.S. Energy Information Administration annual U.S. Regular All Formulations Retail Gasoline Prices series, EMM_EPMR_PTE_NUS_DPG. The included snapshot contains 16 annual observations for 2010–2025 in nominal dollars per gallon, including taxes. MongoDB stores these observations; Redis caches 256 ordered year-pair calculations derived from them.

The published values are $2.429/gallon in 2015 and $2.168/gallon in 2020, a decrease of $0.261/gallon, or about 10.75% using 2015 as the baseline. EIA changed its survey methods in 2018, so interpret the comparison as descriptive. It does not identify causes or adjust for inflation.

The saved direct tests passed. An earlier guided Ollama run made three real tool calls and matched EIA. A separate matched comparison ran once per condition: both answers were wrong, and the MCP-available trial executed zero tools. The guided run used different instructions, so it does not establish an accuracy improvement caused by MCP.

These are recorded classroom results, not a guarantee about new runs, model accuracy, performance, or public deployment security.

## Setup and verification

The commands below run from the `code/` directory after cloning or downloading this repository. They install dependencies and start local services; no training is required.

```text
FRESH SETUP
Python 3.12 recommended. Install and start Docker Desktop and install Ollama if needed:
https://www.docker.com/products/docker-desktop/
https://ollama.com/download

Open a terminal inside code/:
python -m venv .venv
Windows: .\.venv\Scripts\python.exe -m pip install -r requirements.txt
Linux/macOS: .venv/bin/python -m pip install -r requirements.txt
Use that virtual environment's Python for every command below, or activate it.

1. Start the database containers:
   docker compose up -d
   Wait for database startup before the seed step. Retry the seed step if the
   containers are still starting. The recorded run used local MongoDB and Redis
   in WSL; Docker is the supplied alternative setup.

2. Extract the included EIA source snapshot and load the databases:
   python prepare_data.py
   python seed_data.py
   No EIA API key or live download is needed for these included snapshots.
   MongoDB stores 16 annual records. Redis stores 256 calculated year pairs.
   This uses only mcp_group7_gasoline and mcp_group7:gasoline: namespaced keys.

3. In terminal 1 start the application services:
   python run_services.py

4. In terminal 2 run the tests without AI:
   python mcptest.py
   python verify_limits.py
   Both should print PASS and save JSON under code/results/.

5. Start Ollama if it is not already running:
   ollama serve
   In another terminal:
   ollama pull qwen3:0.6b
   python ollama_client.py
   A new run can take time on a CPU. Results are saved in results/ollama_test.json.
   Read the final answer yourself as well as the saved automatic checks.
   The local 4B attempt timed out; its saved failure is included. The default
   is the smaller model used for the earlier guided test. To try another model, pull it
   and set OLLAMA_MODEL, for example qwen3:4b. This is a configuration choice,
   not a claim about model accuracy across questions.

6. To ask another question:
   python ollama_client.py "What was the U.S. regular gasoline price in 2016?"

7. Stop the application services with Ctrl+C. Stop Docker databases with:
   docker compose down
   Volumes remain available for the next run.

PORTS
MongoDB 27028, Redis 6388, Mongo Flask 5001, Redis Flask 5002,
MCP http://127.0.0.1:5000/mcp, Ollama 11434.
Use config.py environment overrides for existing database servers.
Flask health endpoints check the application process, not the database connection.
If a test returns HTTP 429, wait a minute before repeating it.

EXPECTED DEMONSTRATION
2015: $2.429/gallon. 2020: $2.168/gallon. Change: -$0.261/gallon.
Percentage change uses 2015 as the denominator: about a 10.75% decrease.
These are nominal, tax-inclusive national annual estimates for regular gasoline.
Mention EIA's 2018 survey-method change when interpreting the comparison.

SAFETY SCOPE
Local classroom demonstration, no authentication. The API exposes reads only.
Setup writes are separate. Add authentication, HTTPS, read-only database users,
shared rate/concurrency limits, and cache versioning before public deployment.


PROFESSOR FEEDBACK ADDITION RECORDED NOVEMBER 23 2026
The recorded evidence includes an actual Ollama-only comparison.
We ran qwen3:0.6b once in each condition with identical model digest, fresh
messages, prompts, temperature 0, thinking enabled, seed 7 and a 2048-token cap.
The no-MCP run received no tools, database records, or source prices.
The other run had live MCP tools available. Both gave wrong prices; the
MCP-available run wrote tool names as text and executed zero real tool calls.
The earlier guided run in ollama_test.json made 3 calls and matched EIA.
It used different instructions and is NOT part of the fresh matched pair.
No accuracy rate or guaranteed improvement is claimed from one pair.

Recorded evidence:
results/paired_without_mcp.json: exact no-tools answer and shared prompts.
results/paired_with_mcp.json: exact fresh answer with tool definitions available.
results/comparison_summary.json: reference and manual review of both answers.

To repeat with the same configured local services and model running:
python compare_ollama_modes.py without_mcp
python compare_ollama_modes.py with_mcp
New outputs use results/rerun_*.json so the recorded evidence remains intact.
Inspect both the answer and the structured calls list. Text such as <tools>
does not prove that any database operation occurred.
```

## Source

[EIA annual gasoline price series](https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?f=A&n=PET&s=EMM_EPMR_PTE_NUS_DPG)

[EIA definitions and survey methodology](https://www.eia.gov/dnav/pet/TblDefs/pet_pri_gnd_tbldef2.asp)
