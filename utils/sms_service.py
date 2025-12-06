import os
from twilio.rest import Client

account_sid = "AC4be6a0fc5f7eb69e4d436e3fa65bebc7"
auth_token = "b0b95f8925227b22975976df27727250"
verify_sid = "VA7969e6648ebd03905a90207650a320c0"

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
