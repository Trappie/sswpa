# Local Development Setup

This guide explains how to run the SSWPA website locally for development.

## Prerequisites

- Python 3.11+
- pip

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   
   Copy your credentials to the `.env` file:
   ```bash
   # The .env file should contain:
   SQUARE_SANDBOX_APP_ID=your-sandbox-app-id-here
   SQUARE_SANDBOX_LOCATION_ID=your-sandbox-location-id-here  
   SQUARE_SANDBOX_ACCESS_TOKEN=your-sandbox-access-token-here
   GMAIL_APP_PASSWORD=your-gmail-app-password-here
   ENVIRONMENT=local
   ```

3. **Get your Square credentials:**
   - Go to [Square Developer Dashboard](https://developer.squareup.com/)
   - Select your application
   - Copy the Sandbox Application ID and Access Token
   - Get the Location ID from Locations section

4. **Get Gmail app password:**
   ```bash
   # You can get it from GCP if you have access:
   gcloud secrets versions access latest --secret=gmail-app-password
   ```

## Running Locally

**Option 1: Using the run script (recommended):**
```bash
python run_local.py
```

**Option 2: Using uvicorn directly:**
```bash
ENVIRONMENT=local uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Accessing the Website

- **Main website:** http://localhost:8000
- **Ticket page:** http://localhost:8000/tickets/test
- **Health check:** http://localhost:8000/health

## Testing Payments

Use Square's test card numbers:
- **Card Number:** `4111 1111 1111 1111`
- **Expiry:** Any future date (e.g., `12/26`)
- **CVC:** Any 3 digits (e.g., `123`)

## How It Works

- When `ENVIRONMENT=local`, the app reads credentials from `.env` file
- When deployed to GCP, it automatically uses Secret Manager
- The same code works in both environments without changes

## Troubleshooting

1. **"Failed to retrieve secret" errors:**
   - Make sure your `.env` file has all required variables
   - Check that `ENVIRONMENT=local` is set

2. **Square errors:**
   - Verify your Square credentials are correct
   - Make sure you're using Sandbox credentials, not Production

3. **Gmail errors:**
   - Ensure you have a valid Gmail app password
   - Check that 2FA is enabled on the Gmail account