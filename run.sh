#!/bin/bash
poetry run uvicorn polymer.api:app # --log-config=logging.yaml
