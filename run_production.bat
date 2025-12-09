@echo off
echo Starting MIC Production Server with Gunicorn...
echo.
echo Make sure you have installed all dependencies from requirements.txt:
echo pip install -r requirements.txt
echo.
echo Starting server with Gunicorn on http://0.0.0.0:8001
echo Press Ctrl+C to stop the server.
echo.

gunicorn -w 4 -k uvicorn.workers.UvicornWorker server:app --bind 0.0.0.0:8001
