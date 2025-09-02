# SSWPA Database Schema

This document defines the complete database schema for the Steinway Society of Western Pennsylvania (SSWPA) ticketing and event management system.

## Overview

The database is designed to support:
- Classical music recital management
- Ticket sales with multiple pricing tiers
- Order tracking and payment processing
- Future donation functionality
- Event lifecycle management

## Core Tables

### 1. `recitals` - Main Events Table

Stores information about classical music recitals and performances.

```sql
CREATE TABLE recitals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,                    -- "John Novacek: Pianist and Composer"
    artist_name TEXT NOT NULL,              -- "John Novacek"
    description TEXT,                       -- Event description/bio
    venue TEXT NOT NULL,                    -- "Carnegie Music Hall"
    venue_address TEXT,                     -- Full venue address
    event_date DATE NOT NULL,               -- "2024-12-15"
    event_time TIME NOT NULL,               -- "19:30"
    status TEXT DEFAULT 'upcoming',         -- 'upcoming', 'on_sale', 'past', 'cancelled'
    slug TEXT UNIQUE NOT NULL,              -- "john-novacek-dec-2024" (for URLs)
    image_url TEXT,                         -- Artist photo URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Status Values:**
- `upcoming`: Show on website, tickets not yet available ("Coming Soon")
- `on_sale`: Show on website, tickets available for purchase ("Buy Tickets")
- `past`: Hidden from website, event completed
- `cancelled`: Hidden from website, event cancelled (future: refund handling)

### 2. `ticket_types` - Pricing Tiers Table

Defines different ticket categories and pricing for each recital.

```sql
CREATE TABLE ticket_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recital_id INTEGER NOT NULL,
    name TEXT NOT NULL,                     -- "General Admission", "Student", "Senior"
    price_cents INTEGER NOT NULL,          -- 2500 = $25.00 (stored in cents)
    description TEXT,                       -- "Students with valid ID"
    max_quantity INTEGER DEFAULT 10,       -- Maximum tickets per order
    total_available INTEGER,               -- NULL = unlimited availability
    sort_order INTEGER DEFAULT 0,         -- Display order on website
    active BOOLEAN DEFAULT 1,             -- Enable/disable ticket type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recital_id) REFERENCES recitals(id)
);
```

**Design Notes:**
- Prices stored in cents to avoid decimal precision issues
- `total_available = NULL` means unlimited tickets
- `sort_order` controls display sequence (lower = higher priority)

### 3. `orders` - Purchase Records Table

Tracks complete purchase transactions from customers.

```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recital_id INTEGER NOT NULL,
    buyer_email TEXT NOT NULL,
    buyer_name TEXT NOT NULL,
    phone TEXT,                            -- Optional phone number
    total_amount_cents INTEGER NOT NULL,   -- Total order amount in cents
    payment_status TEXT DEFAULT 'pending', -- 'pending', 'completed', 'failed', 'refunded'
    square_payment_id TEXT,                -- Square payment transaction ID
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,                            -- Internal notes
    FOREIGN KEY (recital_id) REFERENCES recitals(id)
);
```

**Payment Status Values:**
- `pending`: Payment initiated but not confirmed
- `completed`: Payment successfully processed
- `failed`: Payment failed or declined
- `refunded`: Payment refunded (future functionality)

### 4. `order_items` - Individual Ticket Records

Stores the specific tickets purchased in each order.

```sql
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    ticket_type_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,             -- Number of tickets of this type
    price_per_ticket_cents INTEGER NOT NULL, -- Price at time of purchase
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (ticket_type_id) REFERENCES ticket_types(id)
);
```

**Design Notes:**
- Stores price at time of purchase (price history preservation)
- Supports multiple ticket types per order
- Quantity-based (no individual seat assignments currently)

## Optional Enhancement Tables

### 5. `donations` - Donation Tracking (Future)

Supports NGO donation functionality.

```sql
CREATE TABLE donations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_email TEXT NOT NULL,
    donor_name TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,         -- Donation amount in cents
    donation_type TEXT DEFAULT 'general',  -- 'general', 'scholarship', 'program'
    payment_status TEXT DEFAULT 'pending', -- Same as orders table
    square_payment_id TEXT,                -- Square payment transaction ID
    donation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_anonymous BOOLEAN DEFAULT 0,        -- Hide donor name publicly
    message TEXT                           -- Optional donor message
);
```

## Relationships

```
recitals (1) ←→ (many) ticket_types
recitals (1) ←→ (many) orders
orders (1) ←→ (many) order_items
ticket_types (1) ←→ (many) order_items
```

## Website Display Logic

### Homepage/Tickets Listing
```sql
-- Show upcoming and on-sale recitals
SELECT * FROM recitals 
WHERE status IN ('upcoming', 'on_sale') 
ORDER BY event_date ASC;
```

### Ticket Purchase Page
```sql
-- Show ticket types for on-sale recitals only
SELECT tt.* FROM ticket_types tt
JOIN recitals r ON tt.recital_id = r.id
WHERE r.status = 'on_sale' AND r.slug = ? AND tt.active = 1
ORDER BY tt.sort_order ASC;
```

### Order Summary
```sql
-- Get complete order details
SELECT 
    o.*,
    r.title as recital_title,
    r.event_date,
    r.venue
FROM orders o
JOIN recitals r ON o.recital_id = r.id
WHERE o.id = ?;

-- Get order items
SELECT 
    oi.*,
    tt.name as ticket_type_name
FROM order_items oi
JOIN ticket_types tt ON oi.ticket_type_id = tt.id
WHERE oi.order_id = ?;
```

## Data Integrity Rules

1. **Money Values**: Always store in cents as INTEGER
2. **Email Validation**: Required for orders and donations
3. **Slug Uniqueness**: Each recital must have unique URL slug
4. **Status Transitions**: 
   - `upcoming` → `on_sale` → `past`
   - Any status → `cancelled`
5. **Price Consistency**: `order_items.price_per_ticket_cents` preserves historical pricing
6. **Foreign Keys**: Enforce referential integrity between related tables

## Example Data

```sql
-- Sample recital
INSERT INTO recitals (title, artist_name, venue, event_date, event_time, status, slug)
VALUES ('John Novacek: Pianist and Composer', 'John Novacek', 'Carnegie Music Hall', '2024-12-15', '19:30', 'on_sale', 'john-novacek-dec-2024');

-- Sample ticket types
INSERT INTO ticket_types (recital_id, name, price_cents, description, sort_order)
VALUES 
(1, 'General Admission', 2500, 'Standard seating', 1),
(1, 'Student', 1500, 'Valid student ID required', 2),
(1, 'Senior (65+)', 2000, 'Ages 65 and older', 3);
```

## Migration Strategy

1. Start with core tables: `recitals`, `ticket_types`, `orders`, `order_items`
2. Add test data for upcoming recitals
3. Implement order processing workflow
4. Add `donations` table when ready for donation functionality
5. Add indexes for performance as data grows

## Future Enhancements

- **Seat assignments**: Add seat numbers and venue layout
- **Member discounts**: Special pricing for SSWPA members
- **Season subscriptions**: Package deals for multiple events
- **Waiting lists**: Handle sold-out events
- **Email templates**: Automated confirmations and reminders
- **Analytics**: Sales reporting and attendance tracking