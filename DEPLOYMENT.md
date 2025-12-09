# Deployment Instructions

This guide provides instructions on how to deploy the application to a cloud server.

## 1. Prerequisites

*   **Python 3.10+:** Make sure Python is installed on your server.
*   **Nginx:** Nginx is recommended as a reverse proxy to handle incoming traffic and serve static files.
*   **Git:** Git is required to clone the repository.

## 2. Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-name>
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    ```

3.  **Activate the virtual environment:**
    *   **Windows:**
        ```bash
        .\.venv\Scripts\activate
        ```
    *   **Linux/macOS:**
        ```bash
        source .venv/bin/activate
        ```

4.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 3. Configuration

1.  **Create a `.env` file:**
    Create a `.env` file in the root of the project and add the following environment variables:

    ```
    RAZORPAY_KEY_ID=<your-razorpay-key-id>
    RAZORPAY_KEY_SECRET=<your-razorpay-key-secret>
    EXCHANGE_RATE_API_KEY=<your-exchange-rate-api-key>
    HF_HOME="E:/mic/LLM" 
    ```

    **Note:** You will need to replace the placeholder values with your actual keys and secrets.

## 4. Running the Application

1.  **Run the production server:**
    *   **Windows:**
        ```bash
        run_production.bat
        ```
    *   **Linux/macOS:**
        You will need to create a `run_production.sh` script with the following content:
        ```bash
        #!/bin/bash
        echo "Starting the server in production mode with Gunicorn..."
        source .venv/bin/activate
        gunicorn -w 4 -k uvicorn.workers.UvicornWorker server:app --bind 0.0.0.0:8001
        deactivate
        ```
        Then make it executable and run it:
        ```bash
        chmod +x run_production.sh
        ./run_production.sh
        ```

## 5. Nginx Configuration

1.  **Create an Nginx configuration file:**
    Create a new file in your Nginx configuration directory (e.g., `/etc/nginx/sites-available/mic`) and add the following configuration:

    ```nginx
    server {
        listen 80;
        server_name your_domain.com;

        location / {
            proxy_pass http://127.0.0.1:8001;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /static {
            alias /path/to/your/project/static;
        }
    }
    ```

2.  **Enable the configuration:**
    Create a symbolic link to the configuration file in the `sites-enabled` directory:

    ```bash
    sudo ln -s /etc/nginx/sites-available/mic /etc/nginx/sites-enabled/
    ```

3.  **Test and reload Nginx:**
    ```bash
    sudo nginx -t
    sudo systemctl reload nginx
    ```

    **Note:** You will need to replace `your_domain.com` and `/path/to/your/project/static` with your actual domain name and the absolute path to the `static` directory of your project.
