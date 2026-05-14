# 🚀 Subtext: Daily Sync Setup Guide

This guide covers the steps required to enable the **Daily Mass Sync** pipeline, which automatically refreshes the "Taste DNA" and library for all users every 24 hours.

## 1. Backend Configuration (.env)
You need to define an administrative secret in your `backend/.env` file. This prevents unauthorized users from triggering a mass sync.

```bash
# Add this to backend/.env
ADMIN_SECRET="your_strong_password_here"
```

## 2. GitHub Secrets Configuration
To allow GitHub Actions to talk to your backend safely, you must add two secrets to your repository.

1. Go to your repository on GitHub.
2. Navigate to **Settings > Secrets and Variables > Actions**.
3. Click **New repository secret**.
4. Add the following:
   - **`ADMIN_SECRET`**: The exact same password you used in your `.env`.
   - **`BACKEND_URL`**: Your Hugging Face Space URL (e.g., `https://yourname-subtext.hf.space`).

## 3. Verify the Workflow
The workflow is located at `.github/workflows/daily_sync.yml`. It is scheduled to run at **Midnight UTC** every day.

**To test it manually:**
1. Go to the **Actions** tab in your GitHub repo.
2. Select **Daily Library Sync** from the left sidebar.
3. Click the **Run workflow** dropdown and hit the button.

## 4. Sync Intelligence
- **Live Sync**: Labeled as "Daily." Best for additions.
- **ZIP Sync**: Labeled as "Full Reset." Best for deletions and total parity.
- **Mass Sync**: The automated job. It runs a "Quick Sync" for every user sequentially to keep the platform alive.

---
*Note: The mass sync includes a 5-10 second delay between users to ensure Letterboxd does not flag the server as a bot.*
