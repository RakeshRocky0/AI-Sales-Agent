# AI Call Assistant Deployment Guide

This project is an AI-powered voice sales agent built with Flask, Twilio, and Google Gemini API. It handles incoming/outbound voice calls and lets you schedule student slot bookings with natural, conversational voice interactions.

Because the app is a unified Flask web service (serving templates from `/templates` and static files from `/static`), it acts as **both the frontend and backend**. You deploy it as a single Web Service on Render.

---

## Prerequisites

Before deploying, ensure you have:
1. A **GitHub** account.
2. A **Render** account.
3. A **Twilio** account with:
   - Account SID and Auth Token
   - A purchased Twilio voice phone number
4. A **Google Gemini API Key**.

---

## Option 1: One-Click Blueprint Deployment (Recommended)

Render supports deploying from a `render.yaml` blueprint file which automatically configures the web service and lists environment variables:

1. **Push your code to GitHub:** Ensure your local repository is pushed to a private GitHub repository. (Make sure `.env`, `student_bookings.json`, and other gitignored files are *not* pushed).
2. **Go to Render:** Navigate to the [Render Dashboard](https://dashboard.render.com/).
3. **Select Blueprints:** Click **New +** in the top right and select **Blueprint**.
4. **Connect Repository:** Select your GitHub repository.
5. **Name the Group:** Provide a name for the blueprint group (e.g. `ai-call-assistant-group`).
6. **Set Secrets:** Render will prompt you to enter values for:
   - `GEMINI_API_KEY`
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_FROM_NUMBER` (your E.164 Twilio phone number, e.g. `+16592215195`)
   - `VOICE_WEBHOOK_URL` (Wait until the service begins deploying to see the URL Render assigns it, then update this variable. It will look like `https://ai-call-assistant-xxxx.onrender.com/voice`)
7. **Deploy:** Click **Apply** to deploy the services.

---

## Option 2: Manual Web Service Deployment

If you prefer to configure the Web Service manually:

1. **Create Web Service:** Click **New +** in Render and select **Web Service**.
2. **Connect Repository:** Connect your GitHub repository.
3. **Configure Service Settings:**
   - **Name:** `ai-call-assistant`
   - **Runtime:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Instance Type:** Select `Free` (or a paid tier if you need persistent disk support).
4. **Configure Environment Variables:**
   Under the **Environment** tab, add the following variables:
   - `GEMINI_API_KEY` = `<Your Google Gemini API Key>`
   - `TWILIO_ACCOUNT_SID` = `<Your Twilio Account SID>`
   - `TWILIO_AUTH_TOKEN` = `<Your Twilio Auth Token>`
   - `TWILIO_FROM_NUMBER` = `<Your Twilio From Number>`
   - `SIMULATE_MODE` = `false` (set to `true` if you want browser-only simulator mode)
   - `VOICE_WEBHOOK_URL` = `https://<your-render-subdomain>.onrender.com/voice` (Get your service URL from the top of the Render page, add `/voice` at the end)

---

## Crucial Post-Deployment Step: Twilio Webhook URL

Twilio must know where to forward incoming phone calls or trigger outbound webhook events.

1. Log in to your [Twilio Console](https://console.twilio.com/).
2. Navigate to **Phone Numbers** > **Manage** > **Active Numbers**.
3. Click on your active Twilio phone number.
4. Scroll down to the **Voice & Fax** section:
   - Under **A CALL COMES IN**, select **Webhook**.
   - In the URL field, paste your Render URL: `https://<your-render-subdomain>.onrender.com/voice`
   - Set the HTTP method to **HTTP POST**.
5. Click **Save**.

---

## Data Persistence (Keeping Bookings Across Restarts)

By default, Render's filesystem is ephemeral. If the app restarts (which happens at least once a day on the Free tier) or if you deploy new changes, all bookings in `student_bookings.json` will be wiped.

### How to Persist Data (Requires paid instance tier like "Starter"):
1. In the Render Dashboard, go to your Web Service settings.
2. Scroll to the **Disks** section.
3. Click **Add Disk**:
   - **Name:** `bookings-volume`
   - **Mount Path:** `/data`
   - **Size:** `1 GB` (minimum)
4. Go to the **Environment** tab and add:
   - `DATA_DIR` = `/data`
5. Save changes. Render will redeploy and mount the persistent volume. All bookings will now be saved in `/data/student_bookings.json` and persist permanently.
