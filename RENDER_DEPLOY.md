# Render Deployment Guide

This guide helps you deploy the Email Monitor to Render's free plan with keep-alive functionality.

## 🚀 Quick Deployment Steps

### 1. Prepare Your Repository

1. **Push your code to GitHub** (or GitLab/Bitbucket)
   - Make sure your `.env` file is **NOT** pushed (it should be in `.gitignore`)
   - Only push the code files, not your credentials

### 2. Create Render Service

1. **Go to [Render Dashboard](https://dashboard.render.com/)**
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub repository**
4. **Configure the service:**
   - **Name**: `email-monitor` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python email_monitor.py`
   - **Plan**: `Free`

### 3. Set Environment Variables

In the Render dashboard, go to your service → **Environment** tab and add:

```
EMAIL_USER=daveayeni880@gmail.com
EMAIL_PASSWORD=ixok hjhh imvr nxrp
TELEGRAM_BOT_TOKEN=8145899840:AAEV0CGPd20vPfLDhwzz-5hHSBK1-RAOxtU
TELEGRAM_CHAT_ID=7415735107
MONITORED_SENDERS=support@acctbazaar.com
CHECK_INTERVAL_MINUTES=0.25
```

### 4. Deploy

1. **Click "Create Web Service"**
2. **Wait for deployment** (usually 2-5 minutes)
3. **Check the logs** for any errors

## 🔄 How Keep-Alive Works

The free plan limitations:
- ✅ **Free for 750 hours/month**
- ⚠️ **Sleeps after 15 minutes of inactivity**
- ✅ **Wakes up on HTTP request**

Our solution:
- 📡 **HTTP server** runs on port 10000 (set by Render)
- 🔄 **Self-ping every 14 minutes** to prevent sleep
- 🩺 **Health check endpoint** at `/health`
- 🏠 **Status page** at `/` (your app URL)

## 📋 Service Endpoints

After deployment, your service will have:

- **Main Page**: `https://your-app.onrender.com/`
- **Health Check**: `https://your-app.onrender.com/health`
- **Ping**: `https://your-app.onrender.com/ping`

## 🔧 Monitoring Your Service

### Check Service Status
Visit your app URL to see if it's running:
```
https://your-app-name.onrender.com/
```

### View Logs
In Render dashboard → Your Service → **Logs** tab

### Health Check
```bash
curl https://your-app-name.onrender.com/health
```

## ⚡ Performance Tips

### Optimize for Free Plan:
1. **Keep CHECK_INTERVAL_MINUTES at 0.25** (15 seconds) for fast email delivery
2. **Monitor your 750-hour limit** in Render dashboard
3. **Consider upgrading** if you need 24/7 uptime

### Cost Breakdown:
- **750 hours = ~31 days** of continuous running
- **Free plan is perfect** for personal email monitoring
- **Upgrade to $7/month** for unlimited hours if needed

## 🚨 Troubleshooting

### Common Issues:

1. **Build Fails:**
   - Check if all files are pushed to GitHub
   - Verify `requirements.txt` is correct
   - Check build logs in Render dashboard

2. **Service Crashes:**
   - Check environment variables are set correctly
   - Look at service logs for errors
   - Verify Gmail app password is correct

3. **Keep-Alive Not Working:**
   - Check if `RENDER_EXTERNAL_URL` is set automatically
   - Look for keep-alive logs in service logs
   - Visit your app URL manually to test

4. **Emails Not Being Detected:**
   - Check Gmail credentials
   - Verify monitored senders list
   - Test locally first with `python email_monitor.py --once`

### Debug Commands:
```bash
# Test configuration locally
python -c "import config; print('Config loaded successfully')"

# Test keep-alive service locally
python keep_alive.py

# Test startup notification
python email_monitor.py --test-notification

# Run email check once
python email_monitor.py --once

# Test all deployment readiness
python test_render.py
```

## 🔒 Security Notes

- ✅ **Environment variables** are encrypted at rest
- ✅ **Logs don't show** environment variable values
- ✅ **HTTPS** is provided automatically
- ⚠️ **Never commit** your `.env` file
- ✅ **Use Gmail app passwords** (not your main password)

## 📈 Monitoring & Alerts

The service will send Telegram notifications for:
- 🚀 **Service startup**: "🚀 Email Monitor Started!" with full configuration details
- ✅ **New emails**: Real-time email forwarding
- ⚠️ **Errors**: Automatic error notifications with recovery status
- ⏹️ **Service shutdown**: "⏹️ Email Monitor Stopped" when manually stopped
- 🧪 **Test notifications**: Use `--test-notification` flag for testing

Startup notification includes:
- 📧 Monitored Gmail account
- 🕐 Check interval settings  
- 📋 List of monitored senders
- 🔄 Keep-alive status for Render
- ⏰ Service start timestamp

Your email monitoring service will now run 24/7 on Render's free plan! 🎉