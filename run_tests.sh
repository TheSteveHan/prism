#!/bin/bash
SKIP_WORKERS=1 DB_URL=sqlite:///:memory: pytest -vs $@
