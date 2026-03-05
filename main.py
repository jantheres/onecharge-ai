import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import Optional

# LangChain Imports
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

# 1. LOAD THE VAULT
load_dotenv()

# 2. START THE FRAMEWORK
app = FastAPI(title="OneCharge AI Backend")

# --- ADDED CORS MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)
# -----------------------------

# ==========================================
# 3. CREATE THE TOOLS (Diagnostic Upgraded)
# ==========================================

@tool
def get_booking_details(user_id: str) -> str:
    """Get the user's scheduled booking time, payment status, and failure reasons."""
    return json.dumps({
        "scheduled_time_hours_from_now": 1.0, 
        "payment_method": "online",
        "payment_status": "failed",
        "error_reason": "CARD_EXPIRED" # <-- The AI will read this and analyze the problem!
    })

@tool
def get_ticket_status(user_id: str) -> str:
    """Get the current stage of the ticket, wait times, and invoice status."""
    return json.dumps({
        "status": "pending", 
        "wait_time_minutes": 10,
        "sla_minutes": 5,
        "invoice_exists": False
    })

@tool
def get_driver_gps(user_id: str) -> str:
    """Get the age of the driver's last GPS update in minutes."""
    return json.dumps({
        "gps_age_minutes": 35 
    })

tools = [get_booking_details, get_ticket_status, get_driver_gps]

# ==========================================
# 4. SYSTEM PROMPT (The AI's Brain Rules)
# ==========================================

SYSTEM_PROMPT = """
You are a helpful customer support chatbot for "OneCharge" (also known as Electro), an on-demand EV service app providing battery swaps, roadside assistance, and maintenance.

CRITICAL RULES:
1. NEVER make up information. ALWAYS use the provided tools to look up the user's data before answering dynamic questions.
2. If you are unable to answer a question, reply EXACTLY with: "I am unable to resolve this issue. Please contact our human support team directly."
3. For "How-to" questions about the app, use the exact workflows provided in the FAQ Knowledge Base below. Format your answer clearly using bullet points or steps if necessary.

APP USAGE & FAQ KNOWLEDGE BASE:
- How to Book a Service: To book a service in OneCharge: Open the Home Screen. Select a service category (e.g., Low Battery or Breakdown). Choose your vehicle from the vehicle selection sheet. Confirm your service location. Select booking type — Instant or Scheduled (minimum 3 hours in advance). Choose issue sub-type or charging unit. Add description or attachments if needed. Apply redeem or company code (optional). Select payment method. Submit the request to create your ticket.
- How to Select a Vehicle: After selecting a service category, a vehicle selection bottom sheet will appear. Choose one of your registered vehicles. If no vehicle is available, go to Settings -> My Vehicle to add a new one.
- How to Apply Redeem Code: While filling the booking form, locate the "Redeem Code" section. Enter your valid promo code and tap Apply. The discount will be validated in real-time and reflected in the payment breakdown.
- How to Choose Issue Sub-Type / Charging Unit: After selecting a service category, you will see available issue sub-types or charging unit options. Select the option that best matches your vehicle's issue before proceeding.
- How to Do Payment: After submitting the booking request: If payment is required, a payment breakdown screen will appear. Review base amount, VAT, discount, and total. Tap Confirm to open the secure payment gateway. Complete payment to start service tracking. If the total amount is zero (redeem/company code applied), service will begin automatically.
- How to Edit Profile: To edit your profile: Go to Settings. Tap Profile. Update your name or profile details. Save the changes.
- How to Check Recent / View Past Bookings: Go to Settings -> Recent Bookings. You will see a list of all your previous service requests with status and details. Tap any booking to view detailed information and invoice (if available).
- Manage Registered Vehicles: To manage your vehicles: Go to Settings. Tap My Vehicle. Add, view, or delete your registered EVs. Each vehicle includes brand, model, plate number, and vehicle type.
- How to Log Out: To log out: Open Settings. Tap Log Out. Confirm logout in the dialog. Your session will be securely cleared.
- How to Delete Account: To permanently delete your account: Go to Settings. Tap Delete Account. Confirm the deletion warning. This action is permanent and cannot be undone.

DIAGNOSTIC & BUSINESS LOGIC:
- If `scheduled_time_hours_from_now` is < 1.5 hours, say: "Scheduled bookings must be at least 1.5 hours from now. Please choose a later time slot."
- If payment failed, you MUST analyze the `error_reason` from the tool and explain it logically. Example: "Your payment failed because your card is expired. Please update it."
- If status is 'pending' or 'offered', say: "Your service request is currently in the Finding stage. We are assigning the nearest available EV driver." 
  * NOTE: If wait_time_minutes > sla_minutes, say: "We are experiencing high demand right now. Please contact support."
- If status is 'assigned' or 'reaching', and driver GPS age > 30 minutes, say: "For accuracy, driver locations older than 30 minutes are automatically ignored by our map. Please wait for an updated GPS signal from the driver."
- If status is 'at_location', 'in_progress', 'solving', or 'reached', say: "Your driver has arrived and service is currently in progress."
- If status is 'completed' or 'resolved' but invoice_exists is false, say: "Your service is marked completed. Invoice will be generated shortly. Please refresh the app."

INTENT CLASSIFICATION (App Errors):
If the user reports an app bug or error, classify it into: [Location/Map issue, EV Vehicle/Garage issue, Payment/Gateway issue, Promo/Code issue, App crash, Notification issue]. 
Acknowledge the specific issue type, and tell them to contact support.
"""

# ==========================================
# 5. INITIALIZE THE LANGGRAPH AGENT
# ==========================================

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
memory = MemorySaver()

agent_executor = create_react_agent(llm, tools, checkpointer=memory)

# ==========================================
# 6. PYDANTIC MODEL (The Bouncer)
# ==========================================
class ChatRequest(BaseModel):
    message: str
    user_name: Optional[str] = Field(default=None, max_length=50)
    
    # <-- ADDED THIS: The secret mailbox for the Flutter app to send crash logs!
    hidden_app_error: Optional[str] = Field(default=None, max_length=500) 

# ==========================================
# 7. THE API ENDPOINTS
# ==========================================

@app.get("/api/chat/history/{user_id}")
async def get_chat_history(user_id: str):
    config = {"configurable": {"thread_id": user_id}}
    state = agent_executor.get_state(config)
    
    messages_in_history = state.values.get("messages", []) if state and hasattr(state, 'values') else []
    
    formatted_messages = []
    for msg in messages_in_history:
        if msg.type == "human":
            formatted_messages.append({"role": "user", "content": msg.content})
        elif msg.type == "ai" and msg.content: 
            formatted_messages.append({"role": "bot", "content": msg.content})

    return {"messages": formatted_messages}


@app.post("/api/chat/send/{user_id}")
async def send_chat_message(user_id: str, request: ChatRequest):
    config = {"configurable": {"thread_id": user_id}}
    state = agent_executor.get_state(config)
    
    messages_in_history = state.values.get("messages", []) if state and hasattr(state, 'values') else []
    
    input_messages = []
    
    if len(messages_in_history) == 0:
        personalized_prompt = SYSTEM_PROMPT
        
        if request.user_name:
            personalized_prompt += f"\n\nIMPORTANT NOTE: The user's name is {request.user_name}. Always greet them politely using their name in your first response."
            
        input_messages.append(SystemMessage(content=personalized_prompt))
        
    # --- ADDED LOGIC FOR DIAGNOSTICS ---
    actual_message = request.message
    # If the Flutter app sent a secret error code, we attach it to the message so the AI can read it!
    if request.hidden_app_error:
        actual_message += f"\n\n[SECRET SYSTEM LOG: The app reported this error: {request.hidden_app_error}. Diagnose this for the user.]"
    # -----------------------------------

    input_messages.append(HumanMessage(content=actual_message))
    
    try:
        response = await agent_executor.ainvoke(
            {"messages": input_messages}, 
            config
        )
        bot_reply = response["messages"][-1].content
    except Exception as e:
        print(f"CRITICAL AI ERROR: {e}")
        bot_reply = "I'm currently experiencing technical difficulties. Please try again in a moment or contact human support."
        
    return {"role": "bot", "content": bot_reply}


@app.delete("/api/chat/history/{user_id}")
async def delete_chat_history(user_id: str):
    """Flutter calls this when the user clicks 'Clear Chat'."""
    config = {"configurable": {"thread_id": user_id}}
    state = agent_executor.get_state(config)
    
    messages_in_history = state.values.get("messages", []) if state and hasattr(state, 'values') else []
    
    if not messages_in_history:
        return {"status": "success", "message": "Chat is already empty."}
        
    delete_commands = [RemoveMessage(id=m.id) for m in messages_in_history]
    
    await agent_executor.aupdate_state(config, {"messages": delete_commands})
    
    return {"status": "success", "message": f"Chat history deleted for {user_id}."}