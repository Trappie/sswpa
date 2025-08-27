from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.cloud import secretmanager
import logging

app = FastAPI(title="Steinway Society of Western Pennsylvania")

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

def get_gmail_password():
    """Fetch Gmail app password from Secret Manager"""
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = "tech-bridge-initiative"
        secret_id = "gmail-app-password"
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logging.error(f"Failed to retrieve Gmail password: {e}")
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
        "artist_name": "John Novacek"  # This would come from database
    })


@app.get("/health")
async def health_check():
    return {"status": "healthy"}