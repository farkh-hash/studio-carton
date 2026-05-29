import aiosqlite
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from app.db.database import get_db
from app.core.config import settings

router = APIRouter(prefix="/users", tags=["users"])


class EmailRequest(BaseModel):
    email: str


@router.post("/login")
async def login_or_register(req: EmailRequest, db: aiosqlite.Connection = Depends(get_db)):
    email = req.email.lower().strip()
    row = await (await db.execute("SELECT * FROM users WHERE email=?", (email,))).fetchone()
    if not row:
        await db.execute("INSERT INTO users (email, credits) VALUES (?, 3)", (email,))
        await db.commit()
        row = await (await db.execute("SELECT * FROM users WHERE email=?", (email,))).fetchone()
    return dict(row)


@router.get("/{email}")
async def get_user(email: str, db: aiosqlite.Connection = Depends(get_db)):
    row = await (await db.execute("SELECT * FROM users WHERE email=?", (email.lower(),))).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)


@router.post("/checkout")
async def create_checkout(req: EmailRequest, db: aiosqlite.Connection = Depends(get_db)):
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    stripe.api_key = settings.STRIPE_SECRET_KEY
    email = req.email.lower().strip()

    row = await (await db.execute("SELECT * FROM users WHERE email=?", (email,))).fetchone()
    if not row:
        await db.execute("INSERT INTO users (email, credits) VALUES (?, 3)", (email,))
        await db.commit()
        row = await (await db.execute("SELECT * FROM users WHERE email=?", (email,))).fetchone()

    user = dict(row)

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": settings.STRIPE_PRICE_ID, "quantity": 1}],
        customer_email=email,
        success_url=f"{settings.APP_URL}?success=1&email={email}",
        cancel_url=f"{settings.APP_URL}?canceled=1",
        metadata={"user_email": email},
    )
    return {"checkout_url": session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook not configured")

    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        email = session.get("metadata", {}).get("user_email") or session.get("customer_email", "")
        if email:
            await db.execute("UPDATE users SET is_pro=1 WHERE email=?", (email.lower(),))
            await db.commit()

    return {"ok": True}
