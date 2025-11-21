# 🔴 Fixing 401 Authentication Error in Hugging Face Spaces

## Error Message
```
openai.AuthenticationError: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-proj-...
```

## What This Means

The API key is being **read** by the app, but OpenAI is **rejecting** it. This usually means:

1. ❌ **API key is incomplete/truncated** (most common)
2. ❌ **API key has extra spaces or characters**
3. ❌ **API key is expired or revoked**
4. ❌ **Wrong API key copied**

## ✅ Step-by-Step Fix

### Step 1: Get a Fresh API Key

1. Go to https://platform.openai.com/api-keys
2. If you see your key, **delete it** and create a new one
3. Click **"Create new secret key"**
4. **Copy the ENTIRE key immediately** (you'll only see it once!)
5. The key should be about **51 characters** long
6. Should start with `sk-proj-` or `sk-`

### Step 2: Update Secret in Hugging Face

1. Go to your Space: https://huggingface.co/spaces/cybersecjs/SQL-Query-Buddy
2. Click **⚙️ Settings**
3. Go to **"Variables and secrets"** tab
4. Find the `OPENAI_API_KEY` secret
5. Click **"Edit"** or delete and recreate it
6. **Paste the FULL key** (no spaces, no quotes)
7. Make sure:
   - ✅ No spaces before the key
   - ✅ No spaces after the key
   - ✅ No quotes around the key
   - ✅ Full key is pasted (all 51 characters)
8. Click **"Save secret"**

### Step 3: Verify Key Format

The key should look like:
```
sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**NOT:**
- ❌ `"sk-proj-..."` (with quotes)
- ❌ ` sk-proj-...` (with leading space)
- ❌ `sk-proj-... ` (with trailing space)
- ❌ `sk-proj-...` (truncated/incomplete)

### Step 4: Restart Your Space

1. Click the **🔄 Restart** button in your Space
2. Or go to Settings → **"Restart this Space"**
3. Wait for rebuild (2-5 minutes)

### Step 5: Check Logs

1. Go to **"Logs"** tab
2. Look for: `✅ OpenAI API key found: sk-proj-xxxxx...xxxx (length: 51)`
3. If length is less than 40, the key is truncated!

## 🔍 How to Verify Your Key Works

### Test Locally First

```bash
export OPENAI_API_KEY="your-full-key-here"
python -c "from openai import OpenAI; client = OpenAI(); print('✅ Key works!')"
```

If this fails, your key is invalid.

### Check Key in OpenAI Dashboard

1. Go to https://platform.openai.com/api-keys
2. Check if your key is:
   - ✅ Active (not revoked)
   - ✅ Has permissions (not read-only if you need write)
   - ✅ Has credits/quota available

## 🛠️ Common Issues

### Issue 1: Key Truncated

**Symptom:** Error shows `sk-proj-` but cuts off

**Fix:**
- Make sure you copied the ENTIRE key
- Keys are ~51 characters
- Check the secret value in HF (it's hidden, but verify length)

### Issue 2: Extra Characters

**Symptom:** Key has spaces or quotes

**Fix:**
- Remove ALL spaces before/after
- Remove quotes if present
- Paste only the key itself

### Issue 3: Wrong Key Type

**Symptom:** Key format doesn't match

**Fix:**
- Use a **secret key** (starts with `sk-`)
- Not an organization key
- Not a project key (unless it's the full project key)

### Issue 4: Key Revoked/Expired

**Symptom:** Key was working but stopped

**Fix:**
- Create a new key
- Update the secret in HF Spaces
- Restart the Space

## 📝 Verification Checklist

After updating your key, verify:

- [ ] Key is exactly 51 characters (or close to it)
- [ ] Key starts with `sk-proj-` or `sk-`
- [ ] No spaces before or after the key
- [ ] No quotes around the key
- [ ] Secret name is exactly: `OPENAI_API_KEY`
- [ ] Secret is in "Repository secrets" (not variables)
- [ ] Space has been restarted
- [ ] Logs show: `✅ OpenAI API key found: sk-proj-xxxxx...xxxx (length: 51)`

## 🚨 Still Not Working?

1. **Delete and recreate the secret** in HF Spaces
2. **Get a completely new API key** from OpenAI
3. **Check OpenAI account** has credits/quota
4. **Verify key works** locally first
5. **Check Space logs** for specific error messages

## 💡 Pro Tip

To avoid truncation:
- Copy the key directly from OpenAI dashboard
- Paste it immediately into HF Spaces
- Don't edit or modify it
- Use a password manager if needed

