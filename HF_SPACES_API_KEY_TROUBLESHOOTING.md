# 🔑 Troubleshooting OpenAI API Key in Hugging Face Spaces

## Common Issues and Solutions

### Issue 1: API Key Not Found

**Error:** `OPENAI_API_KEY not found!`

**Solution:**
1. Go to your Space Settings (⚙️ icon in your Space)
2. Click **"Variables and secrets"** tab
3. In the **"Repository secrets"** section, click **"New secret"**
4. Enter:
   - **Name:** `OPENAI_API_KEY` (must be exact, case-sensitive)
   - **Value:** Your OpenAI API key (starts with `sk-`)
5. Click **"Save"**
6. **Restart your Space** (click the restart button or push a new commit)

### Issue 2: API Key Format Issues

**Error:** API key doesn't start with 'sk-'

**Solution:**
- Make sure your API key starts with `sk-`
- Don't include quotes around the key
- Don't include spaces before or after the key
- The full key should be: `sk-proj-...` or `sk-...` (about 51 characters)

### Issue 3: API Key Set but Still Not Working

**Checklist:**
1. ✅ Secret name is exactly: `OPENAI_API_KEY` (case-sensitive)
2. ✅ Secret is in **"Repository secrets"** section (not "Repository variables")
3. ✅ Space has been restarted after adding the secret
4. ✅ No extra spaces or quotes in the key value

### Issue 4: API Key Not Visible After Adding

**Solution:**
- Secrets are hidden for security - you won't see the value after saving
- This is normal! Just verify the name is correct: `OPENAI_API_KEY`
- Check the Space logs to see if the key is being read

## How to Verify Your API Key is Set

### Method 1: Check Logs
1. Go to your Space → **"Logs"** tab
2. Look for: `✅ OpenAI API key found: sk-xxxxx...xxxx`
3. If you see an error instead, follow the error message instructions

### Method 2: Add Debug Code (Temporary)
Add this to `app.py` temporarily:
```python
import os
print(f"API Key exists: {bool(os.getenv('OPENAI_API_KEY'))}")
print(f"API Key length: {len(os.getenv('OPENAI_API_KEY', ''))}")
print(f"API Key starts with sk-: {os.getenv('OPENAI_API_KEY', '').startswith('sk-')}")
```

## Step-by-Step: Setting Up API Key in HF Spaces

1. **Get Your OpenAI API Key**
   - Go to https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Copy the key (you'll only see it once!)

2. **Add to Hugging Face Space**
   - Navigate to your Space on Hugging Face
   - Click the **⚙️ Settings** icon
   - Go to **"Variables and secrets"** tab
   - Under **"Repository secrets"**, click **"+ New secret"**
   - Name: `OPENAI_API_KEY`
   - Value: Paste your API key
   - Click **"Save secret"**

3. **Restart Your Space**
   - Option A: Click the **🔄 Restart** button in the Space UI
   - Option B: Push a new commit to trigger rebuild
   - Option C: Click **"Settings"** → **"Restart this Space"**

4. **Verify It Works**
   - Check the **"Logs"** tab for confirmation
   - Try asking a question in the app
   - If it still fails, check error messages in logs

## Important Notes

- **Secrets vs Variables**: Use **Secrets** (not Variables) for sensitive data like API keys
- **Case Sensitive**: `OPENAI_API_KEY` must be exact (all caps)
- **Restart Required**: You must restart the Space after adding secrets
- **Visibility**: Secrets are hidden - you can't view them after saving (this is normal)
- **Scope**: Secrets are available to your Space automatically via `os.getenv()`

## Testing Your API Key Locally

Before deploying, test your key locally:

```bash
export OPENAI_API_KEY="sk-your-key-here"
python app.py
```

If it works locally but not in HF Spaces, the issue is with how the secret is set in HF.

## Getting Help

If you've tried all of the above and it's still not working:

1. Check the Space **Logs** for specific error messages
2. Verify your OpenAI API key works at https://platform.openai.com/api-keys
3. Make sure your OpenAI account has credits/quota available
4. Check if there are any rate limits being hit

## Security Best Practices

- ✅ Never commit API keys to git
- ✅ Always use Secrets (not Variables) for sensitive data
- ✅ Rotate keys periodically
- ✅ Use read-only keys when possible
- ✅ Monitor API usage in OpenAI dashboard

