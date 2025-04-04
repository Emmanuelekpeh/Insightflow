from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import os
from ..lib.supabase import get_supabase_client
from ..services.email import send_email

router = APIRouter(prefix="/api/newsletter", tags=["newsletter"])

class NewsletterSubscription(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    preferences: Optional[dict] = {"market_insights": True, "competitor_updates": True}

@router.post("/subscribe")
async def subscribe_to_newsletter(subscription: NewsletterSubscription, background_tasks: BackgroundTasks):
    """Subscribe to the newsletter."""
    try:
        supabase = get_supabase_client()
        
        # Check if already subscribed
        existing = supabase.table("newsletter_subscribers").select("*").eq("email", subscription.email).execute()
        if existing.data and len(existing.data) > 0:
            if existing.data[0].get("unsubscribed"):
                # Reactivate subscription
                supabase.table("newsletter_subscribers").update({
                    "unsubscribed": False,
                    "preferences": subscription.preferences,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("email", subscription.email).execute()
            else:
                raise HTTPException(status_code=400, detail="Email already subscribed")
            return {"message": "Subscription reactivated successfully"}
        
        # Create new subscription
        supabase.table("newsletter_subscribers").insert({
            "email": subscription.email,
            "name": subscription.name,
            "preferences": subscription.preferences,
            "subscribed_at": datetime.utcnow().isoformat()
        }).execute()

        # Send welcome email in background
        background_tasks.add_task(send_welcome_email, subscription.email, subscription.name)
        
        return {"message": "Subscribed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unsubscribe/{email}")
async def unsubscribe_from_newsletter(email: str):
    """Unsubscribe from the newsletter."""
    try:
        supabase = get_supabase_client()
        
        # Mark as unsubscribed instead of deleting
        result = supabase.table("newsletter_subscribers").update({
            "unsubscribed": True,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("email", email).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        return {"message": "Unsubscribed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def send_welcome_email(email: str, name: Optional[str] = None):
    """Send a welcome email to new subscribers using MailerSend."""
    try:
        subject = 'Welcome to InsightFlow Newsletter!'
        html_content=f'''
            <h2>Welcome to InsightFlow!</h2>
            <p>Dear {name or "Valued Subscriber"},</p>
            <p>Thank you for subscribing to our newsletter. You'll receive regular updates about:</p>
            <ul>
                <li>Market Insights and Trends</li>
                <li>Competitor Analysis</li>
                <li>Industry News</li>
            </ul>
            <p>Stay tuned for your first newsletter!</p>
            <p>To manage your subscription, please visit your account settings (if applicable) or look for an unsubscribe link in future emails.</p>
            '''
        await send_email(to_email=email, subject=subject, html_content=html_content)
        print(f"Welcome email sent successfully to {email}")

    except Exception as e:
        print(f"Error sending welcome email: {str(e)}")
        # Don't raise the exception - this is a background task 