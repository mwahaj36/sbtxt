# Setting up Gmail API via OAuth2

This guide explains how to generate or rotate the Gmail API OAuth2 credentials used for sending automated emails (like password resets) from the backend. 

We use the Gmail REST API instead of standard SMTP because cloud providers (like Hugging Face Spaces) strictly block outbound connections on SMTP ports (25, 465, 587) to prevent spam.

## Prerequisites

1. A **Google Cloud Project** with the **Gmail API** enabled.
2. An **OAuth 2.0 Client ID** and **Client Secret** generated in the Google Cloud Console.

## Step 1: Whitelist the OAuth Playground (One-Time Setup)

To easily generate a refresh token without writing a custom OAuth flow, we use the Google OAuth 2.0 Playground. First, we must allow the Playground to use our Client ID.

1. Go to your [Google Cloud Console](https://console.cloud.google.com/).
2. Navigate to **APIs & Services** > **Credentials**.
3. Click the pencil icon to edit your **OAuth 2.0 Client ID**.
4. Scroll down to **Authorized redirect URIs** and click **ADD URI**.
5. Paste exactly: `https://developers.google.com/oauthplayground`
6. Click **Save**.

## Step 2: Add the Sender Email as a Test User

If your Google Cloud OAuth consent screen is in "Testing" mode (not published), you must explicitly allow the email address you want to send *from*.

1. In the Google Cloud Console, go to **APIs & Services** > **OAuth consent screen**.
2. Scroll down to **Test users** and click **Add Users**.
3. Add the email address you want the app to send emails from (e.g., `mwahaj25@gmail.com`).
4. Click **Save**.

## Step 3: Generate the Refresh Token

1. Open the [Google OAuth 2.0 Playground](https://developers.google.com/oauthplayground/) in a new tab.
2. In the top right corner, click the **Gear Icon (Settings)** ⚙️.
3. Check the box that says **"Use your own OAuth credentials"**.
4. Paste your `CLIENT_ID` and `CLIENT_SECRET` from Google Cloud into the boxes and click **Close**.
5. On the left panel (**Step 1**), scroll all the way to the bottom to the box that says **"Input your own scopes"**.
6. Type exactly: `https://mail.google.com/` and click the **Authorize APIs** button.
7. You will be redirected to a Google Login screen. **Log in with the exact email address you added as a test user.**
   * *Note: If you see a "Google hasn't verified this app" warning, click **Advanced** -> **Go to [App Name] (unsafe)**.*
8. Click **Continue** to grant the app permission to send emails on your behalf.
9. You will be redirected back to the Playground. Under **Step 2** on the left panel, click the blue button that says **"Exchange authorization code for tokens"**.
10. A new box labeled **Refresh token** will appear. Copy that entire string.

## Step 4: Update Environment Variables

Open your backend `.env` file (and don't forget to update your production Secrets!) and configure the following variables:

```dotenv
# The email you logged in with during Step 3
EMAIL_USER="your-email@gmail.com"

# The credentials from Google Cloud
EMAIL_CLIENT_ID="your-client-id.apps.googleusercontent.com"
EMAIL_CLIENT_SECRET="your-client-secret"

# The token you just generated from the Playground
EMAIL_REFRESH_TOKEN="1//your-refresh-token"
```

*Note: You do not need to update the Client ID and Secret when switching emails. You only need to repeat Steps 2, 3, and 4 to generate a new Refresh Token for the new email address.*
