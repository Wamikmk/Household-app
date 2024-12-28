# Household Services Management System

## Project Overview
This is my Flask-based web application developed as part of my web development coursework. The project aims to demonstrate a practical solution for connecting homeowners with service providers, while implementing core concepts of web development, database management, and user authentication.

## Project Objectives
- Implement a full-stack web application using Flask framework
- Design and manage relational databases using SQLAlchemy
- Create a role-based authentication system
- Develop interactive user interfaces for multiple user types
- Implement data visualization using Matplotlib

## Core Features

### User Management
- Multi-role user system (Homeowners, Service Providers, Administrators)
- Secure authentication and authorization
- Profile management for different user types

### Service Management
- Service provider registration and verification system
- Public and private service request handling
- Rating and review system for completed services

### Administrative Controls
- Service provider approval workflow
- Service category management
- Platform monitoring and analytics

### Analytics and Reporting
- Service provider performance metrics
- User engagement statistics
- Request tracking and status monitoring

## Technical Implementation

### Technologies Used
- **Backend Framework**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML, CSS, JavaScript
- **Data Visualization**: Matplotlib
- **File Handling**: Werkzeug

### Database Schema
The application uses three main models:
- User (handles all user types)
- HouseholdServices (manages service categories)
- HouseholdServiceRequest (handles service requests)

## Setup and Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python main/app.py
   ```

## Learning Outcomes
Through this project, I gained practical experience in:
- Implementing MVC architecture in Flask
- Managing database relationships and migrations
- Handling user authentication and session management
- Creating dynamic web interfaces
- Processing and visualizing data
- Implementing file upload functionality
- Error handling and input validation

## Future Improvements
- Implement email verification system
- Add payment integration
- Enhance search functionality with filters
- Develop a mobile-responsive design
- Add real-time notifications
- Implement chat functionality between users

## Acknowledgments
Special thanks to the App dev-I team at IIT Madras for guidance throughout this project development.

---

This project was developed as part of Application development-I coursework at IIT Madras.
