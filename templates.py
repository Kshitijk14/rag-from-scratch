import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s]: %(message)s:')


project_name = "rag_from_scratch"

list_of_files = [
    "artifacts/data/.gitkeep",
    "artifacts/vectordb/.gitkeep",
    "artifacts/results/.gitkeep",

    # notebooks
    "notebooks/.gitkeep",
    
    # pipeline
    "rag_pipeline/__init__.py",
    "rag_pipeline/stage_01.py",
    "rag_pipeline/stage_02.py",
    "rag_pipeline/stage_03.py",
    "rag_pipeline/stage_04.py",

    # utils
    "utils/__init__.py",
    "utils/config.py",
    "utils/logger.py",
    "utils/server.py",
    
    "utils/telemetry/__init__.py",
    "utils/telemetry/tracing.py",
    
    "utils/notebooks/__init__.py",
    "utils/notebooks/common.py",
    
    "utils/helpers/__init__.py",
    "utils/populate/__init__.py",
    
    "utils/llm/__init__.py",
    "utils/llm/get_prompt_temps.py",
    "utils/llm/get_models.py",

    # tests
    "tests/__init__.py",

    # docs
    "docs/README.md",

    "params.yaml",
    "dvc.yaml",
    "Dockerfile",
    ".dockerignore",
    ".env.local",
    ".env.example",
]


for filepath in list_of_files:
    filepath = Path(filepath) #to solve the windows path issue
    filedir, filename = os.path.split(filepath) # to handle the project_name folder


    if filedir !="":
        os.makedirs(filedir, exist_ok=True)
        logging.info(f"Creating directory; {filedir} for the file: {filename}")

    if (not os.path.exists(filepath)) or (os.path.getsize(filepath) == 0):
        with open(filepath, "w") as f:
            pass
            logging.info(f"Creating empty file: {filepath}")


    else:
        logging.info(f"{filename} is already exists")