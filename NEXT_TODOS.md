# Next TODOs for SSWPA Ticketing System

## High Priority (Core Functionality)

### 1. Error Handling for Failed Payments
- [ ] Better error messages for different failure types (card declined, insufficient funds, etc.)
- [ ] Handle partial failures (order created but payment failed)
- [ ] Graceful degradation when Square API is down

### 2. Email Notifications
- [ ] Send confirmation email to customer after successful payment
- [ ] Send notification email to webmaster/admin for each order
- [ ] Create HTML email templates (not just plain text)
- [ ] Include order details, ticket info, and event details in emails

### 3. Order Confirmation & Receipt
- [ ] Redirect to confirmation page after successful payment (instead of just showing success message)
- [ ] Customer order lookup page (enter email to see orders)
- [ ] Generate printable/downloadable tickets or receipts
- [ ] Order confirmation page with all purchase details

### 4. Retry Logic & Duplicate Prevention
- [ ] Prevent duplicate order creation when user clicks "Pay" multiple times
- [ ] Add payment processing spinner/loading state
- [ ] Implement idempotency keys properly to avoid duplicate charges

### 5. Failed Order Cleanup
- [ ] Automatic cleanup of failed/abandoned orders after timeout (e.g., 1 hour)
- [ ] Background job or scheduled task for cleanup
- [ ] Mark expired orders as "expired" instead of deleting

## Medium Priority (Admin & Management)

### 6. Admin Order Management
- [ ] Admin interface to view all orders
- [ ] Filter orders by status, date, recital, etc.
- [ ] Export orders to CSV for reporting
- [ ] Mark orders as refunded/cancelled

### 7. Inventory Management
- [ ] Track remaining tickets for each ticket type
- [ ] Prevent overselling (check availability before payment)
- [ ] Show "Sold Out" status when tickets unavailable
- [ ] Warning when tickets are running low

### 8. Order Status Tracking
- [ ] Order status updates (pending → processing → completed → fulfilled)
- [ ] Customer order status lookup
- [ ] Email notifications for status changes

### 9. Webhooks (Future Consideration)
- [ ] Square webhook endpoint for payment status updates
- [ ] Handle delayed payment confirmations
- [ ] Reconciliation between Square and database
- [ ] Note: Starting simple without webhooks is correct for now

## Lower Priority (Enhancements)

### 10. Security & Validation
- [ ] CSRF protection for payment forms
- [ ] Rate limiting on payment endpoints
- [ ] Input validation and sanitization
- [ ] Audit logging for admin actions

### 11. User Experience
- [ ] Better mobile responsive design for payment flow
- [ ] Accessibility improvements (ARIA labels, keyboard navigation)
- [ ] Payment form validation (client-side)
- [ ] Progress indicator for checkout process

### 12. Business Logic
- [ ] Refund functionality through admin interface
- [ ] Partial refunds support
- [ ] Order modification (change ticket quantities)
- [ ] Group discounts or promo codes

### 13. Technical Improvements
- [ ] Unit tests for payment processing
- [ ] Integration tests for full checkout flow
- [ ] Database migrations for schema changes
- [ ] Error monitoring and alerting
- [ ] Performance optimization for high traffic

### 14. Operational
- [ ] Database backup strategy
- [ ] Order data export/import tools
- [ ] Customer service tools for order lookup
- [ ] Reporting dashboard for sales analytics

## Technical Debt

### 15. Code Organization
- [ ] Move payment logic to separate service class
- [ ] Extract email sending to separate module
- [ ] Add proper error handling middleware
- [ ] Improve logging structure

### 16. Configuration
- [ ] Environment-specific email templates
- [ ] Configurable timeout values
- [ ] Feature flags for new functionality

## Nice to Have

### 17. Advanced Features
- [ ] Multi-event cart (buy tickets for multiple recitals)
- [ ] Saved payment methods (with proper PCI compliance)
- [ ] Guest checkout vs. account creation
- [ ] Order history for returning customers
- [ ] Automated reminder emails before events

---

## Notes:
- Start with items 1-5 for a robust basic system
- Items 6-9 for better management and operations  
- Items 10+ for long-term improvements
- Webhooks can be added later when needed for more complex scenarios
- Focus on reliability and user experience first, then add advanced features