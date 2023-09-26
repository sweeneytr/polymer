#!/bin/bash
poetry run uvicorn polymer.app:app --log-config=logging.yaml
