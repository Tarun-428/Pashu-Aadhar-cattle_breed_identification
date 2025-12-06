import os
from twilio.rest import Client
from dotenv import load_dotenv

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_ACC_AUTH_TOKEN")
verify_sid = os.getenv("TWILIO_ACC_VERIFY_SID")
client = Client(account_sid, auth_token)

def send_otp(mobile):
    """Send OTP using Twilio Verify API"""
    verification = client.verify \
        .v2 \
        .services(verify_sid) \
        .verifications \
        .create(to=f'+91{mobile}', channel='sms')
    print(verification.status)
    return verification.sid

def verify_otp(mobile, code):
    """Check OTP using Twilio Verify API"""
    verification_check = client.verify \
        .v2 \
        .services(verify_sid) \
        .verification_checks \
        .create(to=f'+91{mobile}', code=code)
    return verification_check.status == "approved"
