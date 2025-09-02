from fastapi import FastAPI, Request, Form, File, UploadFile, Cookie, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
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
    ensure_complete_schema, get_recitals, get_recital_by_id, get_recital_by_slug,
    create_recital, update_recital, delete_recital,
    get_ticket_types_for_recital, get_ticket_type_by_id,
    create_ticket_type, update_ticket_type, delete_ticket_type,
    create_order, update_order_payment_status, get_order_by_id
)
import time
import secrets
import shutil
from pathlib import Path

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

async def save_uploaded_image(image: UploadFile) -> str:
    """Save uploaded image to persistent storage and return relative path"""
    if not image or not image.filename:
        return None
    
    # Create images directory in persistent storage
    images_dir = Path("/data/images")
    images_dir.mkdir(exist_ok=True)
    
    # Generate unique filename
    file_extension = Path(image.filename).suffix.lower()
    unique_filename = f"{secrets.token_hex(8)}{file_extension}"
    file_path = images_dir / unique_filename
    
    # Save the uploaded file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        # Return relative path for URL serving
        return f"/images/{unique_filename}"
    except Exception as e:
        logging.error(f"Failed to save image: {e}")
        return None

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    try:
        init_database()
        logging.info("Database initialized successfully")
        
        # Create images directory
        images_dir = Path("/data/images")
        images_dir.mkdir(exist_ok=True)
        logging.info("Images directory ensured")
        
        # Mount images directory if it exists now
        if images_dir.exists():
            app.mount("/images", StaticFiles(directory="/data/images"), name="images")
            
    except Exception as e:
        logging.error(f"Startup initialization failed, but continuing: {e}")
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
    try:
        # Get upcoming and on_sale recitals
        recitals = get_recitals(include_past=False)
        # Filter to only show upcoming and on_sale recitals
        display_recitals = [r for r in recitals if r['status'] in ['upcoming', 'on_sale']]
        
        # Add ticket types and price range for each recital
        for recital in display_recitals:
            ticket_types = get_ticket_types_for_recital(recital['id'])
            active_tickets = [t for t in ticket_types if t['active']]
            recital['ticket_types'] = active_tickets
            
            if active_tickets:
                prices = [t['price_cents'] / 100 for t in active_tickets]
                recital['min_price'] = min(prices)
                recital['max_price'] = max(prices)
            else:
                recital['min_price'] = 0
                recital['max_price'] = 0
        
        return templates.TemplateResponse("tickets.html", {
            "request": request, 
            "current_page": "tickets",
            "recitals": display_recitals
        })
    except Exception as e:
        logging.error(f"Error loading tickets page: {e}")
        return templates.TemplateResponse("tickets.html", {
            "request": request, 
            "current_page": "tickets",
            "recitals": [],
            "error_message": "Unable to load concert information"
        })

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

class TicketItem(BaseModel):
    ticket_type_id: int
    quantity: int
    price_per_ticket_cents: int

class PaymentRequest(BaseModel):
    source_id: str
    amount: int
    currency: str = "USD"
    buyer_email: str
    recital_id: int
    ticket_items: list[TicketItem]

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
    try:
        # Fetch recital by slug
        recital = get_recital_by_slug(concert_slug)
        if not recital:
            raise HTTPException(status_code=404, detail="Concert not found")
        
        # Only allow access to on_sale recitals
        if recital['status'] != 'on_sale':
            raise HTTPException(status_code=404, detail="Tickets not yet available for this concert")
        
        # Get active ticket types for this recital
        ticket_types = get_ticket_types_for_recital(recital['id'])
        active_ticket_types = [t for t in ticket_types if t['active']]
        
        return templates.TemplateResponse("ticket-detail.html", {
            "request": request, 
            "current_page": "tickets",
            "recital": recital,
            "ticket_types": active_ticket_types,
            "artist_name": recital['artist_name']  # Keep for backwards compatibility
        })
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error loading ticket detail for {concert_slug}: {e}")
        raise HTTPException(status_code=500, detail="Unable to load concert details")

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
        # Get recital details for order description
        recital = get_recital_by_id(payment_request.recital_id)
        if not recital:
            return {"success": False, "message": "Recital not found"}
        
        # Create order in database first
        order_items = [
            {
                'ticket_type_id': item.ticket_type_id,
                'quantity': item.quantity,
                'price_per_ticket_cents': item.price_per_ticket_cents
            }
            for item in payment_request.ticket_items
        ]
        
        # Build order description for Square
        item_descriptions = []
        for item in payment_request.ticket_items:
            ticket_type = get_ticket_type_by_id(item.ticket_type_id)
            if ticket_type:
                item_descriptions.append(f"{item.quantity}x {ticket_type['name']}")
        
        order_description = f"SSWPA: {', '.join(item_descriptions)} for {recital['artist_name']} on {recital['event_date']}"
        
        order_data = {
            'recital_id': payment_request.recital_id,
            'buyer_email': payment_request.buyer_email,
            'total_amount_cents': payment_request.amount,
            'payment_status': 'processing',
            'notes': order_description
        }
        
        order_id = create_order(order_data, order_items)
        if not order_id:
            return {"success": False, "message": "Failed to create order"}
        
        client = get_square_client()
        
        # Create a unique idempotency key
        idempotency_key = str(uuid.uuid4())
        
        # Process the payment using Square API
        result = client.payments.create(
            source_id=payment_request.source_id,
            idempotency_key=idempotency_key,
            amount_money={
                'amount': payment_request.amount,  # Amount in cents
                'currency': payment_request.currency
            },
            buyer_email_address=payment_request.buyer_email,
            # Note: Removed order_id since Square expects a Square Order object, not our DB order ID
            note=order_description[:500]  # Square note field (limited length)
        )
        
        if result.errors:
            # Handle errors - update order status to failed
            logging.error(f"Payment failed: {result.errors}")
            update_order_payment_status(order_id, 'failed')
            return {
                "success": False,
                "errors": [error.detail for error in result.errors],
                "message": "Payment failed. Please try again.",
                "order_id": order_id
            }
        else:
            # Payment successful - update order status
            payment = result.payment
            logging.info(f"Payment successful: {payment.id}")
            update_order_payment_status(order_id, 'completed', payment.id)
            
            return {
                "success": True,
                "payment_id": payment.id,
                "order_id": order_id,
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
        
        # Handle recital operations
        elif action in ["create_recital", "update_recital", "delete_recital"] and authenticated:
            if action == "create_recital":
                # Handle image upload
                image_path = None
                try:
                    files = await request.form()
                    if 'image' in files and hasattr(files['image'], 'filename') and files['image'].filename:
                        image_path = await save_uploaded_image(files['image'])
                except Exception as e:
                    logging.error(f"Error handling image upload: {e}")
                
                recital_data = {
                    'title': form.get('title'),
                    'artist_name': form.get('artist_name'),
                    'description': form.get('description'),
                    'venue': form.get('venue'),
                    'venue_address': form.get('venue_address'),
                    'event_date': form.get('event_date'),
                    'event_time': form.get('event_time'),
                    'status': form.get('status', 'upcoming'),
                    'slug': form.get('slug'),
                    'image_url': image_path
                }
                result = create_recital(recital_data)
                message = "Recital created successfully with default Adult ($25) and Student ($10) tickets!" if result else "Failed to create recital"
            
            elif action == "update_recital":
                recital_id = int(form.get('recital_id'))
                
                # Handle image upload for updates too
                image_path = None
                try:
                    files = await request.form()
                    if 'image' in files and hasattr(files['image'], 'filename') and files['image'].filename:
                        image_path = await save_uploaded_image(files['image'])
                except Exception as e:
                    logging.error(f"Error handling image upload during update: {e}")
                
                # Get current recital to preserve existing image if no new one uploaded
                current_recital = get_recital_by_id(recital_id)
                final_image_url = image_path if image_path else current_recital.get('image_url')
                
                recital_data = {
                    'title': form.get('title'),
                    'artist_name': form.get('artist_name'),
                    'description': form.get('description'),
                    'venue': form.get('venue'),
                    'venue_address': form.get('venue_address'),
                    'event_date': form.get('event_date'),
                    'event_time': form.get('event_time'),
                    'status': form.get('status'),
                    'slug': form.get('slug'),
                    'image_url': final_image_url
                }
                result = update_recital(recital_id, recital_data)
                message = "Recital updated successfully!" if result else "Failed to update recital"
            
            elif action == "delete_recital":
                recital_id = int(form.get('recital_id'))
                result = delete_recital(recital_id)
                message = "Recital deleted successfully!" if result else "Failed to delete recital"
            
            # Redirect back to admin panel with message
            response = RedirectResponse(url="/admin/wm", status_code=302)
            # Note: In a real app, you'd use flash messages or session storage
            return response
        
        # Handle ticket type operations
        elif action in ["create_ticket_type", "update_ticket_type", "delete_ticket_type"] and authenticated:
            if action == "create_ticket_type":
                ticket_data = {
                    'recital_id': int(form.get('recital_id')),
                    'name': form.get('name'),
                    'price_cents': int(float(form.get('price', 0)) * 100),  # Convert dollars to cents
                    'description': form.get('description'),
                    'max_quantity': int(form.get('max_quantity', 10)),
                    'total_available': int(form.get('total_available')) if form.get('total_available') else None,
                    'sort_order': int(form.get('sort_order', 0)),
                    'active': 1 if form.get('active') else 0
                }
                result = create_ticket_type(ticket_data)
                message = "Ticket type created successfully!" if result else "Failed to create ticket type"
            
            elif action == "update_ticket_type":
                ticket_type_id = int(form.get('ticket_type_id'))
                ticket_data = {
                    'recital_id': int(form.get('recital_id')),
                    'name': form.get('name'),
                    'price_cents': int(float(form.get('price', 0)) * 100),
                    'description': form.get('description'),
                    'max_quantity': int(form.get('max_quantity', 10)),
                    'total_available': int(form.get('total_available')) if form.get('total_available') else None,
                    'sort_order': int(form.get('sort_order', 0)),
                    'active': 1 if form.get('active') else 0
                }
                result = update_ticket_type(ticket_type_id, ticket_data)
                message = "Ticket type updated successfully!" if result else "Failed to update ticket type"
            
            elif action == "delete_ticket_type":
                ticket_type_id = int(form.get('ticket_type_id'))
                result = delete_ticket_type(ticket_type_id)
                message = "Ticket type deleted successfully!" if result else "Failed to delete ticket type"
            
            # Redirect back to admin panel
            response = RedirectResponse(url="/admin/wm", status_code=302)
            return response
    
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
        
        # Get recital data for Edit Items tab
        include_past = request.query_params.get("include_past") == "true"
        recitals = get_recitals(include_past=include_past)
        
        # Get ticket types for all recitals
        all_ticket_types = []
        for recital in recitals:
            ticket_types = get_ticket_types_for_recital(recital['id'])
            all_ticket_types.extend(ticket_types)
        
        template_data = {
            "request": request,
            "authenticated": True,
            "tables": tables,
            "table_data": table_data,
            "recitals": recitals,
            "all_ticket_types": all_ticket_types,
            "include_past": include_past
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

@app.get("/api/recital/{recital_id}")
async def get_recital(recital_id: int, request: Request):
    """API endpoint to fetch recital data for editing"""
    # Check admin authentication using custom session system
    session_id = request.cookies.get("admin_session", "")
    if not is_admin_authenticated(session_id):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        recital = get_recital_by_id(recital_id)
        if not recital:
            raise HTTPException(status_code=404, detail="Recital not found")
        
        return JSONResponse(content=recital)
    except Exception as e:
        logging.error(f"Error fetching recital {recital_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/ticket-type/{ticket_type_id}")
async def get_ticket_type(ticket_type_id: int, request: Request):
    """API endpoint to fetch ticket type data for editing"""
    # Check admin authentication using custom session system
    session_id = request.cookies.get("admin_session", "")
    if not is_admin_authenticated(session_id):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        ticket_type = get_ticket_type_by_id(ticket_type_id)
        if not ticket_type:
            raise HTTPException(status_code=404, detail="Ticket type not found")
        
        return JSONResponse(content=ticket_type)
    except Exception as e:
        logging.error(f"Error fetching ticket type {ticket_type_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}