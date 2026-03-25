# B12-applying (Python)

Small starter project: an HTTP GET example using the third-party `requests` library.

## Setup
```bash
cd "/home/vlad/projects/B12-applying"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
python main.py --url "https://httpbin.org/get" --print-headers
```
