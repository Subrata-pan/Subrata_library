# KitabGhar Email Configuration Guide

## 🚀 **Contact Form Email Setup**

Your KitabGhar contact form is now configured to send emails using Flask-Mail and Gmail SMTP. Follow these steps to get it working:

### **Step 1: Configure Gmail App Password**

Gmail requires an "App Password" for SMTP authentication (not your regular password).

#### **How to Get Gmail App Password:**

1. **Go to Google Account Settings:**
   - Visit: https://myaccount.google.com/
   - Sign in to your Gmail account

2. **Enable 2-Factor Authentication (2FA):**
   - If you don't have 2FA enabled, enable it first
   - Go to Security → 2-Step Verification → Turn on

3. **Generate App Password:**
   - Go to Security → 2-Step Verification → App passwords
   - Select "Mail" and "Other (custom name)"
   - Enter "KitabGhar" as the custom name
   - Click "Generate"
   - **Copy the 16-character password** (ignore spaces)

### **Step 2: Configure Your .env File**

1. **Open the `.env` file** in your project directory
2. **Replace the placeholder values:**

```env
# Your Gmail credentials
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_16_character_app_password
```

**Example:**
```env
MAIL_USERNAME=john.doe@gmail.com
MAIL_PASSWORD=abcd-efgh-ijkl-mnop
```

### **Step 3: Restart Your Application**

After updating the `.env` file:
```bash
# Stop the current server (Ctrl+C)
# Then restart
python main.py
```

### **Step 4: Test the Contact Form**

1. **Visit:** `http://localhost:5000/contact`
2. **Fill out the form** with test data
3. **Submit** and check if you receive the email

## 🔧 **Troubleshooting**

### **Common Issues:**

#### **1. "Authentication Required" Error**
- **Cause:** Using regular Gmail password instead of App Password
- **Solution:** Generate and use App Password (see Step 1)

#### **2. "Email service is not configured" Warning**
- **Cause:** Missing MAIL_USERNAME or MAIL_PASSWORD in .env
- **Solution:** Add the credentials to your .env file

#### **3. "Connection failed" Error**
- **Cause:** Network issues or Gmail SMTP blocking
- **Solution:** Check internet connection, try again later

#### **4. Emails going to Spam**
- **Solution:** Check spam folder, add sender to contacts

### **Alternative Email Providers:**

If you prefer not to use Gmail, you can configure other SMTP providers:

#### **Outlook/Hotmail:**
```env
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@outlook.com
MAIL_PASSWORD=your_password
```

#### **Yahoo:**
```env
MAIL_SERVER=smtp.mail.yahoo.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@yahoo.com
MAIL_PASSWORD=your_app_password
```

## 📧 **Email Template**

When users submit the contact form, you'll receive emails like this:

```
Subject: KitabGhar Contact: [User's Subject]

New contact message from KitabGhar:

Name: John Doe
Email: john@example.com
Subject: Question about uploading books

Message:
I have a question about uploading PDF books to the library...

---
Sent from KitabGhar Contact Form
This message was sent by: John Doe (john@example.com)
```

## 🔒 **Security Notes**

- **Never commit** your `.env` file to version control
- **App Passwords** are specific to each application
- **Regular passwords** won't work for SMTP
- **Keep your credentials secure** and don't share them

## 📞 **Fallback Contact Information**

If email isn't working, users can still contact you directly:
- **Email:** simapan1996@gmail.com
- **Phone:** +91 62943 08077

The contact form will display these details as fallback options.

## ✅ **Verification**

To verify your email setup is working:

1. **Check console output** when starting the app (should not show email configuration warnings)
2. **Test the contact form** with real data
3. **Check your email inbox** for the test message
4. **Reply to the email** using the reply-to address

Your KitabGhar contact form is now ready to send emails! 🎉
