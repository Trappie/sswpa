from fastapi import FastAPI, Request, Form, Cookie, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.cloud import secretmanager
import logging
import uuid
import os
from square import Square
from square.environment import SquareEnvironment
from pydantic import BaseModel
from dotenv import load_dotenv
from .database import (
    init_database, write_test_data, get_test_data,
    has_admin_password, set_admin_password, verify_admin_password,
    get_all_table_names, get_table_data, execute_custom_query,
    ensure_complete_schema
)
import time
import secrets

# Load environment variables from .env file for local development
load_dotenv()

app = FastAPI(title="Steinway Society of Western Pennsylvania")

# Simple session storage (in production, use Redis or database)
admin_sessions = {}

def is_admin_authenticated(session_id: str) -> bool:
    """Check if admin session is valid"""
    if not session_id or session_id not in admin_sessions:
        return False
    
    session_time = admin_sessions[session_id]
    # Session expires after 1 hour
    if time.time() - session_time > 3600:
        del admin_sessions[session_id]
        return False
    
    return True

def create_admin_session() -> str:
    """Create new admin session"""
    session_id = secrets.token_hex(32)
    admin_sessions[session_id] = time.time()
    return session_id

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    try:
        init_database()
        logging.info("Database initialized successfully")
    except Exception as e:
        logging.error(f"Database initialization failed, but continuing: {e}")
        # Continue without crashing - database will be created on first use

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "current_page": "home"})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request, "current_page": "about"})

@app.get("/mission", response_class=HTMLResponse)
async def mission(request: Request):
    return templates.TemplateResponse("mission.html", {"request": request, "current_page": "mission"})

@app.get("/programs", response_class=HTMLResponse)
async def programs(request: Request):
    return templates.TemplateResponse("programs.html", {"request": request, "current_page": "programs"})

@app.get("/board", response_class=HTMLResponse)
async def board(request: Request):
    return templates.TemplateResponse("board.html", {"request": request, "current_page": "board"})

@app.get("/tickets", response_class=HTMLResponse)
async def tickets(request: Request):
    return templates.TemplateResponse("tickets.html", {"request": request, "current_page": "tickets"})

@app.get("/young-artists/about", response_class=HTMLResponse)
async def young_artists_about(request: Request):
    return templates.TemplateResponse("young-artists-about.html", {"request": request, "current_page": "young-artists-about"})

@app.get("/young-artists/audition", response_class=HTMLResponse)
async def young_artists_audition(request: Request):
    return templates.TemplateResponse("young-artists-audition.html", {"request": request, "current_page": "young-artists-audition"})

@app.get("/young-artists/heinz-hall", response_class=HTMLResponse)
async def young_artists_heinz_hall(request: Request):
    return templates.TemplateResponse("young-artists-heinz-hall.html", {"request": request, "current_page": "young-artists-heinz-hall"})

@app.get("/young-artists/honors", response_class=HTMLResponse)
async def young_artists_honors(request: Request):
    return templates.TemplateResponse("young-artists-honors.html", {"request": request, "current_page": "young-artists-honors"})

@app.get("/membership", response_class=HTMLResponse)
async def membership(request: Request):
    return templates.TemplateResponse("membership.html", {"request": request, "current_page": "membership"})

@app.get("/support", response_class=HTMLResponse)
async def support(request: Request):
    return templates.TemplateResponse("support.html", {"request": request, "current_page": "support"})

@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request, "current_page": "contact"})

class PaymentRequest(BaseModel):
    source_id: str
    amount: int
    currency: str = "USD"
    buyer_email: str

def get_secret(secret_id: str):
    """Fetch secret from environment variable or Secret Manager"""
    # Check if running locally with environment variables
    if os.getenv('ENVIRONMENT') == 'local':
        env_map = {
            'square-sandbox-app-id': 'SQUARE_SANDBOX_APP_ID',
            'square-sandbox-location-id': 'SQUARE_SANDBOX_LOCATION_ID', 
            'square-sandbox-access-token': 'SQUARE_SANDBOX_ACCESS_TOKEN',
            'gmail-app-password': 'GMAIL_APP_PASSWORD'
        }
        env_var = env_map.get(secret_id)
        if env_var and os.getenv(env_var):
            return os.getenv(env_var)
    
    # Fallback to GCP Secret Manager
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = "tech-bridge-initiative"
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logging.error(f"Failed to retrieve secret {secret_id}: {e}")
        raise

def get_gmail_password():
    """Fetch Gmail app password from Secret Manager"""
    return get_secret("gmail-app-password")

def get_square_client():
    """Get Square client with sandbox credentials"""
    try:
        access_token = get_secret("square-sandbox-access-token")
        return Square(
            environment=SquareEnvironment.SANDBOX,
            token=access_token
        )
    except Exception as e:
        logging.error(f"Failed to create Square client: {e}")
        raise

def send_contact_email(form_data: dict):
    """Send contact form email using Gmail SMTP"""
    try:
        gmail_password = get_gmail_password()
        
        # Email configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = "wu.di.network@gmail.com"
        sender_password = gmail_password
        recipient_emails = ["marinaschmidt@comcast.net", "wu.di.network@gmail.com"]  # Send to both Marina and Di
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ", ".join(recipient_emails)
        msg['Subject'] = f"SSWPA Contact Form: Message from {form_data['firstName']} {form_data['lastName']}"
        
        # Email body
        body = f"""
New contact form submission from SSWPA website:

Name: {form_data['firstName']} {form_data['lastName']}
Email: {form_data['email']}
Phone: {form_data.get('phone', 'Not provided')}
Alt Phone: {form_data.get('altPhone', 'Not provided')}
Address: {form_data.get('address', 'Not provided')}
City: {form_data.get('city', 'Not provided')}
State: {form_data.get('state', 'Not provided')}
ZIP: {form_data.get('zip', 'Not provided')}

Message:
{form_data['message']}

---
Sent from SSWPA website contact form
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email to all recipients
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg, to_addrs=recipient_emails)
            
        logging.info(f"Contact form email sent successfully from {form_data['email']}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send contact email: {e}")
        return False

@app.post("/contact")
async def submit_contact_form(
    request: Request,
    firstName: str = Form(...),
    lastName: str = Form(...),
    email: str = Form(...),
    phone: str = Form(None),
    altPhone: str = Form(None),
    address: str = Form(None),
    city: str = Form(None),
    state: str = Form(None),
    zip: str = Form(None),
    message: str = Form(...)
):
    form_data = {
        'firstName': firstName,
        'lastName': lastName,
        'email': email,
        'phone': phone,
        'altPhone': altPhone,
        'address': address,
        'city': city,
        'state': state,
        'zip': zip,
        'message': message
    }
    
    # Send email
    success = send_contact_email(form_data)
    
    if success:
        # Redirect back to contact page with success message
        return templates.TemplateResponse("contact.html", {
            "request": request, 
            "current_page": "contact",
            "success_message": "Thank you for your message! We will get back to you soon."
        })
    else:
        # Redirect back to contact page with error message
        return templates.TemplateResponse("contact.html", {
            "request": request, 
            "current_page": "contact",
            "error_message": "Sorry, there was an error sending your message. Please try again or email us directly."
        })

@app.get("/tickets/{concert_slug}", response_class=HTMLResponse)
async def ticket_detail(request: Request, concert_slug: str):
    # For now, return the same template for all concerts
    # In the future, this would fetch concert data from a database
    return templates.TemplateResponse("ticket-detail.html", {
        "request": request, 
        "current_page": "tickets",
        "concert_slug": concert_slug,
        "artist_name": "John Novacek",  # This would come from database
    })

@app.get("/square-config")
async def get_square_config():
    """Get Square configuration for client-side initialization"""
    try:
        app_id = get_secret("square-sandbox-app-id")
        location_id = get_secret("square-sandbox-location-id")
        return {
            "appId": app_id,
            "locationId": location_id
        }
    except Exception as e:
        logging.error(f"Failed to get Square config: {e}")
        return {"error": "Failed to load payment configuration"}

@app.post("/process-payment")
async def process_payment(payment_request: PaymentRequest):
    """Process payment using Square API"""
    try:
        client = get_square_client()
        
        # Create a unique idempotency key
        idempotency_key = str(uuid.uuid4())
        
        # Process the payment using the correct API format (matching working example)
        result = client.payments.create(
            source_id=payment_request.source_id,
            idempotency_key=idempotency_key,
            amount_money={
                'amount': payment_request.amount,  # Amount in cents
                'currency': payment_request.currency
            },
            buyer_email_address=payment_request.buyer_email
            # Note: location_id removed as it's not in the working example
        )
        
        if result.errors:
            # Handle errors
            logging.error(f"Payment failed: {result.errors}")
            return {
                "success": False,
                "errors": [error.detail for error in result.errors],
                "message": "Payment failed. Please try again."
            }
        else:
            # Payment successful
            payment = result.payment
            logging.info(f"Payment successful: {payment.id}")
            
            return {
                "success": True,
                "payment_id": payment.id,
                "status": payment.status,
                "amount": payment.amount_money.amount,
                "receipt_url": payment.receipt_url,
                "message": "Payment processed successfully!"
            }
            
    except Exception as e:
        logging.error(f"Payment processing error: {e}")
        return {
            "success": False,
            "message": "An error occurred while processing your payment."
        }

@app.post("/test-db-write")
async def test_db_write(message: str = "Test message"):
    """Test endpoint to write data to database"""
    try:
        record_id = write_test_data(message)
        return {
            "success": True,
            "message": "Data written successfully",
            "record_id": record_id
        }
    except Exception as e:
        logging.error(f"Database write failed: {e}")
        return {
            "success": False,
            "message": f"Database write failed: {str(e)}"
        }

@app.get("/test-db-read")
async def test_db_read():
    """Test endpoint to read data from database"""
    try:
        data = get_test_data()
        return {
            "success": True,
            "data": data,
            "count": len(data)
        }
    except Exception as e:
        logging.error(f"Database read failed: {e}")
        return {
            "success": False,
            "message": f"Database read failed: {str(e)}"
        }

@app.route("/admin/wm", methods=["GET", "POST"])
async def admin_wm(request: Request):
    """Admin database management interface"""
    
    # Handle logout
    if request.query_params.get("action") == "logout":
        response = RedirectResponse(url="/admin/wm", status_code=302)
        response.delete_cookie("admin_session")
        return response
    
    # Check authentication
    session_id = request.cookies.get("admin_session", "")
    authenticated = is_admin_authenticated(session_id)
    
    # Handle POST requests
    if request.method == "POST":
        form = await request.form()
        action = form.get("action", "")
        
        if action == "create_password":
            password = form.get("password", "")
            confirm_password = form.get("confirm_password", "")
            
            if len(password) < 8:
                return templates.TemplateResponse("admin-wm.html", {
                    "request": request,
                    "authenticated": False,
                    "has_password": False,
                    "error_message": "Password must be at least 8 characters long"
                })
            
            if password != confirm_password:
                return templates.TemplateResponse("admin-wm.html", {
                    "request": request,
                    "authenticated": False,
                    "has_password": False,
                    "error_message": "Passwords do not match"
                })
            
            if set_admin_password(password):
                return templates.TemplateResponse("admin-wm.html", {
                    "request": request,
                    "authenticated": False,
                    "has_password": True,
                    "success_message": "Password created successfully! Please login."
                })
            else:
                return templates.TemplateResponse("admin-wm.html", {
                    "request": request,
                    "authenticated": False,
                    "has_password": False,
                    "error_message": "Failed to create password"
                })
        
        elif action == "login":
            password = form.get("password", "")
            
            if verify_admin_password(password):
                session_id = create_admin_session()
                response = RedirectResponse(url="/admin/wm", status_code=302)
                response.set_cookie("admin_session", session_id, httponly=True)
                return response
            else:
                return templates.TemplateResponse("admin-wm.html", {
                    "request": request,
                    "authenticated": False,
                    "has_password": True,
                    "error_message": "Invalid password"
                })
        
        elif action == "reset_password" and authenticated:
            old_password = form.get("old_password", "")
            new_password = form.get("new_password", "")
            confirm_new_password = form.get("confirm_new_password", "")
            
            if not verify_admin_password(old_password):
                # Stay on the page, but this would need JavaScript to show modal again
                pass
            elif len(new_password) < 8:
                pass
            elif new_password != confirm_new_password:
                pass
            elif set_admin_password(new_password):
                # Clear all sessions
                admin_sessions.clear()
                response = RedirectResponse(url="/admin/wm", status_code=302)
                response.delete_cookie("admin_session")
                return response
        
        elif action == "execute_query" and authenticated:
            query = form.get("query", "").strip()
            if query:
                query_result = execute_custom_query(query)
                
                # Get table data for display
                tables = get_all_table_names()
                table_data = {}
                for table in tables:
                    try:
                        table_data[table] = get_table_data(table)
                    except:
                        table_data[table] = []
                
                return templates.TemplateResponse("admin-wm.html", {
                    "request": request,
                    "authenticated": True,
                    "tables": tables,
                    "table_data": table_data,
                    "query_result": query_result
                })
    
    # Handle GET requests
    if not authenticated:
        has_password = has_admin_password()
        return templates.TemplateResponse("admin-wm.html", {
            "request": request,
            "authenticated": False,
            "has_password": has_password
        })
    
    # Show admin dashboard
    try:
        # Ensure complete database schema exists
        schema_success, schema_message = ensure_complete_schema()
        
        tables = get_all_table_names()
        table_data = {}
        for table in tables:
            try:
                table_data[table] = get_table_data(table)
            except Exception as e:
                logging.error(f"Error loading table {table}: {e}")
                table_data[table] = []
        
        template_data = {
            "request": request,
            "authenticated": True,
            "tables": tables,
            "table_data": table_data
        }
        
        # Add schema status message if any action was taken
        if "created" in schema_message.lower():
            template_data["success_message"] = schema_message
        elif not schema_success:
            template_data["error_message"] = schema_message
        
        return templates.TemplateResponse("admin-wm.html", template_data)
        
    except Exception as e:
        logging.error(f"Error loading admin dashboard: {e}")
        return templates.TemplateResponse("admin-wm.html", {
            "request": request,
            "authenticated": True,
            "tables": [],
            "table_data": {},
            "error_message": "Error loading database tables"
        })

@app.get("/health")
async def health_check():
    return {"status": "healthy"}