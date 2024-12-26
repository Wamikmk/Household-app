import os
from flask import Flask, render_template, request, redirect, flash, url_for, session, abort
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64

current_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///householdServices.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "mysecretkey"
app.config['PASSWORD_HASH'] = 'sha256'

app.config['UPLOAD_EXTENSIONS'] = ['.pdf']
app.config['UPLOAD_PATH'] = os.path.join(current_dir, 'static', 'pdfs')
db = SQLAlchemy()

db.init_app(app)
app.app_context().push()


class User(db.Model):
    __tablename__ = 'user'  # Name of the table

    id = db.Column(db.Integer, primary_key=True)  # Primary key, unique for each brand
    user_name = db.Column(db.String(100), unique=True, nullable=False)  # username of the user, unique and required
    password = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(100), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)  # Column for pincode
    is_admin = db.Column(db.Boolean, default=False)  # Column for admin status
    is_serviceProvider = db.Column(db.Boolean, default=False)  # Column for service provider status
    is_homeOwner = db.Column(db.Boolean, default=False)  # Column for home owner status
    is_approved = db.Column(db.Boolean, default=False)  # Column to track if service provider is approved
    average_rating = db.Column(db.Float, default=0.0)  # New column for average rating
    ratings_count = db.Column(db.Integer, default=0)  # New column for number of ratings
    serviceProvider_file = db.Column(db.String(255), nullable=True)  # New column for service provider file
    serviceProvider_experience = db.Column(db.Integer, nullable=True)  # New column for service provider experience
    age = db.Column(db.Integer, nullable = True)
    service_id= db.Column(db.Integer, db.ForeignKey('HouseholdServices.id', ondelete="SET NULL"), nullable = True)
    #relationship between service provider and services
    service = db.relationship('HouseholdServices', back_populates = 'service_providers',)
    homeowner_requests = db.relationship('HouseholdServiceRequest', back_populates='homeowner', 
        foreign_keys='HouseholdServiceRequest.homeowner_id')
    service_provider_requests = db.relationship('HouseholdServiceRequest', back_populates='service_provider', 
        foreign_keys='HouseholdServiceRequest.serviceProvider_id')



class HouseholdServices(db.Model):
    __tablename__ = 'HouseholdServices'  # Name of the table
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(100), unique = True, nullable = False)
    service_description = db.Column(db.String(100), nullable = True)
    base_price = db.Column(db.Float, nullable = True)
    time_required = db.Column(db.String(100), nullable = True)
    service_providers = db.relationship('User', back_populates='service', cascade="all, delete")
    request = db.relationship('HouseholdServiceRequest', back_populates = 'service', cascade="all, delete")


   



class HouseholdServiceRequest(db.Model):
    __tablename__ = 'HouseholdServiceRequest'
    id = db.Column(db.Integer, primary_key = True)
    service_id = db.Column(db.Integer, db.ForeignKey('HouseholdServices.id'), nullable = True)
    homeowner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    serviceProvider_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    request_type = db.Column(db.String(50), nullable = False) #Private or Public request
    description = db.Column(db.Text, nullable = True)
    status = db.Column(db.String(50), nullable = True) #pending, accepted, rejected, completed
    date_created = db.Column(db.Date, nullable = False, default = datetime.now().date())
    date_closed = db.Column(db.Date, nullable = True)
    ratings_by_homeowner = db.Column(db.Float, default = 0.0)
    review_by_homeowner = db.Column(db.String(100), nullable = True)
    homeowner = db.relationship('User', back_populates='homeowner_requests', foreign_keys=[homeowner_id])
    service_provider = db.relationship('User', back_populates='service_provider_requests', foreign_keys=[serviceProvider_id])
    service = db.relationship('HouseholdServices', back_populates='request')


#define a function to create an admin

def create_admin():
    with app.app_context():
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user:
            admin_user = User(
                user_name="admin", 
                password=generate_password_hash("admin123"), 
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print('Admin Created Successfully')

#call the function to create an admin

with app.app_context():
    db.create_all()
    create_admin()


@app.route('/', methods = ['GET'])
def home():
    return render_template('index.html')



# User login for homewoners and service_providers
@app.route('/user_login', methods = ['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(user_name = username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['is_serviceProvider'] = user.is_serviceProvider
            session['is_homeOwner'] = user.is_homeOwner
            session['username'] = user.user_name
            if user.is_serviceProvider:
                if not user.is_approved:
                    flash('You are not approved yet, Please wait for the admin to approve you', 'danger')
                    return redirect('/user_login')
                if user.service_id is None:
                    flash("Your Service has been deleted, Please create a new account with another service", "danger")
                    return redirect(url_for('user_login'))
                return redirect(url_for('service_provider_dashboard', provider_id = user.id))
            if user.is_homeOwner:
                flash('Login Successful', 'success')
                return redirect(url_for('home_owner_dashboard', homeowner_id = user.id))
        flash("Login unsuccessful. Please check your username and password.", "danger")
    return render_template('user_login.html')



#admin login
@app.route('/admin_login', methods = ['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = User.query.filter_by(is_admin=True, user_name=username).first()

        if admin and check_password_hash(admin.password, password):
            session['username'] = username
            session['is_admin'] = True
            flash("Login Successful", "success")
            return redirect('/admin_dashboard')
        flash("Invalid credentials", "danger")
    return render_template('admin_login.html')

#admin dashboard

@app.route('/admin_dashboard', methods = ['GET', 'POST'])
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Please login first', 'danger')
        return redirect(url_for('admin_login'))
    
    services = HouseholdServices.query.all()
    service_requests = HouseholdServiceRequest.query.all()
    unapproved_service_providers = User.query.filter_by(is_serviceProvider=True, is_approved=False).all()

    return render_template("admin_dashboard.html", 
                         services=services, 
                         service_requests=service_requests, 
                         unapproved_service_providers=unapproved_service_providers, 
                         admin_name=session.get('username'))




#Home Owner Registration

@app.route('/home_owner_register', methods = ['GET', 'POST'])
def home_owner_register():

    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        address = request.form['address']
        pincode = request.form['pincode']

        # Check if username already exists
        user_exists = User.query.filter_by(user_name=username).first()
        if user_exists:
            flash('Username already exists. Please choose a different username.', 'danger')
            return redirect('/home_owner_register')

        # Create new home owner user
        new_user = User(
            user_name=username,
            password=generate_password_hash(password),
            address=address,
            pincode=pincode,
            is_homeOwner=True
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect('/user_login')
        except:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
            return redirect('/home_owner_register')
    return render_template('home_owner_register.html')



# Service Provider Registration 

@app.route('/service_provider_register', methods = ['GET', 'POST'])
def service_provider_register():
   if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        address = request.form['address']
        pincode = request.form['pincode']
        experience = request.form['experience']
        service = request.form['service']
        service_id = HouseholdServices.query.filter_by(service_name = service).first().id

        # Check if username already exists
        user_exists = User.query.filter_by(user_name=username).first()
        if user_exists:
            flash('Username already exists. Please choose a different username.', 'danger')
            return redirect('/service_provider_register')

        # Handle file upload
        file = request.files['service_file']
        if file:
            filename = secure_filename(file.filename)
            if filename != '':
                file_ext = os.path.splitext(filename)[1]
                renamed_filename = username + file_ext
                if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                    abort(400)

                # Ensure the upload directory exists
                upload_path = app.config['UPLOAD_PATH']
                if not os.path.exists(upload_path):
                    os.makedirs(upload_path)  # Create the directory if it doesn't exist

                file.save(os.path.join(upload_path, renamed_filename))
        else:
            filename = None


        # Create new service provider user
        new_user = User(
            user_name=username,
            password=generate_password_hash(password),
            address=address,
            pincode=pincode,
            is_serviceProvider=True,
            serviceProvider_file=renamed_filename,
            serviceProvider_experience=experience,
            service_id=service_id,
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration submitted! Please wait for admin approval.', 'success')
            return redirect('/user_login')
        except:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
            return redirect('/service_provider_register')
   services = HouseholdServices.query.all()
   return render_template('service_provider_register.html', services = services)

#service provider dashboard

@app.route('/service_provider_dashboard/<int:provider_id>')
def service_provider_dashboard(provider_id):
    if not session.get('is_serviceProvider'):
        flash('You are not logged in, please login', 'danger')
        return redirect(url_for('user_login'))
    
    provider = User.query.filter_by(id = provider_id).first()
    pending_requests = HouseholdServiceRequest.query.filter_by(serviceProvider_id = provider_id, status = 'Pending', request_type = 'Private').all()
    accepted_requests = HouseholdServiceRequest.query.filter_by(serviceProvider_id = provider_id, status = 'Accepted').all()
    completed_requests = HouseholdServiceRequest.query.filter_by(serviceProvider_id = provider_id, status = 'Completed').all()
    return render_template('service_provider_dashboard.html',
                            provider = provider,
                            pending_requests = pending_requests,
                            accepted_requests = accepted_requests,
                            completed_requests = completed_requests)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('user_login'))


@app.route('/admin/analytics')
def admin_analytics():
    if not session.get('is_admin'):
        flash('Please login first', 'danger')
        return redirect(url_for('admin_login'))

    # Get all completed requests
    completed_requests = HouseholdServiceRequest.query.filter_by(status='Completed').all()
    
    # Calculate total revenue from all completed services across all providers
    total_revenue = sum(req.service.base_price for req in completed_requests if req.service)
    
    # Get request counts by status for all requests
    pending_count = HouseholdServiceRequest.query.filter_by(status='Pending').count()
    accepted_count = HouseholdServiceRequest.query.filter_by(status='Accepted').count()
    completed_count = HouseholdServiceRequest.query.filter_by(status='Completed').count()
    rejected_count = HouseholdServiceRequest.query.filter_by(status='Rejected').count()
    
    # Get count of active homeowners and service providers
    homeowner_count = User.query.filter_by(is_homeOwner=True).count()
    service_provider_count = User.query.filter_by(is_serviceProvider=True, is_approved=True).count()
    
    # Calculate total requests
    total_requests = pending_count + accepted_count + completed_count + rejected_count
    
    # Generate graphs
    graphs = {}
    
    # Request Status Distribution Graph
    plt.figure(figsize=(10, 6))
    statuses = ['Pending', 'Accepted', 'Completed', 'Rejected']
    counts = [pending_count, accepted_count, completed_count, rejected_count]
    plt.bar(statuses, counts, color=['orange', 'green', 'blue', 'red'])
    plt.title('Overall Request Status Distribution')
    plt.xlabel('Status')
    plt.ylabel('Number of Requests')
    plt.grid(True, alpha=0.3)
    
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    graphs['status'] = base64.b64encode(img.getvalue()).decode()
    plt.close()
    
    return render_template('admin_analytics.html',
                         graphs=graphs,
                         total_revenue=total_revenue,
                         total_requests=total_requests,
                         homeowner_count=homeowner_count,
                         service_provider_count=service_provider_count)

@app.route('/admin/search', methods=['GET', 'POST'])
def admin_search():
    if not session.get('is_admin'):
        flash('Please login first', 'danger')
        return redirect(url_for('admin_login'))
    
    search_query = request.args.get('q', '').strip().lower()
    search_results = {
        'services': [],
        'homeowners': [],
        'service_providers': [],
        'requests': []
    }
    
    if search_query:
        # Search services
        search_results['services'] = HouseholdServices.query.filter(
            HouseholdServices.service_name.ilike(f'%{search_query}%')
        ).all()
        
        # Search homeowners
        search_results['homeowners'] = User.query.filter(
            User.is_homeOwner == True,
            (User.user_name.ilike(f'%{search_query}%')) |
            (User.address.ilike(f'%{search_query}%')) |
            (User.pincode.ilike(f'%{search_query}%'))
        ).all()
        
        # Search service providers
        search_results['service_providers'] = User.query.filter(
            User.is_serviceProvider == True,
            (User.user_name.ilike(f'%{search_query}%')) |
            (User.address.ilike(f'%{search_query}%')) |
            (User.pincode.ilike(f'%{search_query}%'))
        ).all()
        
        # Search service requests
        search_results['requests'] = HouseholdServiceRequest.query.filter(
            (HouseholdServiceRequest.status.ilike(f'%{search_query}%')) |
            (HouseholdServiceRequest.request_type.ilike(f'%{search_query}%'))
        ).all()
    
    return render_template('admin_search.html', 
                         search_query=search_query, 
                         search_results=search_results)




@app.route('/admin_dashboard/add_service', methods=['GET', 'POST'])
def add_service():
    if request.method == 'POST':
        if not session.get('is_admin'):
            flash('Please login first', 'danger')
            return redirect(url_for('admin_login'))
        
        service_name = request.form['service_name']
        service_description = request.form['service_description']
        base_price = request.form['base_price']
        time_required = request.form['time_required']
        
        new_service = HouseholdServices(
            service_name=service_name,
            service_description=service_description,
            base_price=base_price,
            time_required=time_required
        )
        
        try:
            db.session.add(new_service)
            db.session.commit()
            flash('Service added successfully', 'success')
        except:
            db.session.rollback()
            flash('Error adding service', 'danger')
        
        return redirect(url_for('admin_dashboard'))
    return render_template('add_service.html')


# edit a service 

@app.route('/admin_dashboard/edit_service/<int:service_id>', methods=['GET', 'POST'])
def edit_service(service_id):
    if not session.get('is_admin'):
        flash('Please login first', 'danger')
        return redirect(url_for('admin_login'))
    
    service = HouseholdServices.query.get_or_404(service_id)
    if request.method == 'POST':
        service.service_name = request.form['service_name']
        service.service_description = request.form['service_description']
        service.base_price = request.form['base_price']
        service.time_required = request.form['time_required']
        
        try:
            db.session.commit()
            flash('Service updated successfully', 'success')
        except:
            db.session.rollback()
            flash('Error updating service', 'danger')
        
        return redirect(url_for('admin_dashboard'))
    return render_template('edit_service.html', service = service)

#delete a service

@app.route('/admin_dashboard/delete_service/<int:service_id>', methods=['GET','POST'])
def delete_service(service_id):
    if not session.get('is_admin'):
        flash('Please login first', 'danger')
        return redirect(url_for('admin_login'))
    
    service = HouseholdServices.query.get_or_404(service_id)
    approved_ServiceProviders = User.query.filter_by(is_serviceProvider =True, is_approved = True, service_id = service_id )
    
    try:
        for service_provider in approved_ServiceProviders:
            service_provider.is_approved = False
        db.session.delete(service)
        db.session.commit()
        flash('Service deleted successfully', 'success')
    except:
        db.session.rollback()
        flash('Error deleting service', 'danger')
    
    return redirect(url_for('admin_dashboard'))

#approve a service provider

@app.route('/admin_dashboard/approve_service_provider/<int:provider_id>', methods=['GET','POST'])
def approve_service_provider(provider_id):
    if not session.get('is_admin'):
        flash('Please login first', 'danger')
        return redirect(url_for('admin_login'))
    
    provider = User.query.get_or_404(provider_id)
    provider.is_approved = True
    
    try:
        db.session.commit()
        flash('Service provider approved successfully', 'success')
    except:
        db.session.rollback()
        flash('Error approving service provider', 'danger')
    
    return redirect(url_for('admin_dashboard'))

#reject a service provider

@app.route('/admin_dashboard/reject_provider/<int:provider_id>', methods=['GET','POST'])
def reject_service_provider(provider_id):
    if not session.get('is_admin'):
        flash('Please login first', 'danger')
        return redirect(url_for('admin_login'))
    
    provider = User.query.get_or_404(provider_id)
    
    # Check if the service provider file exists and remove it
    if provider.serviceProvider_file:
        file_path = os.path.join(app.config['UPLOAD_PATH'], provider.serviceProvider_file)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)  # Remove the file
            except Exception as e:
                flash(f'Error removing file: {str(e)}', 'danger')

    try:
        db.session.delete(provider)
        db.session.commit()
        flash('Service provider rejected and removed', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting service provider: {str(e)}', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/service_provider_dashboard/accept_request/<int:request_id>', methods=['GET','POST'])
def accept_request(request_id):
    if not session.get('is_serviceProvider'):
        flash('Please login first', 'danger')
        return redirect(url_for('user_login'))
    
    request_to_accept = HouseholdServiceRequest.query.get_or_404(request_id)
    request_to_accept.status = 'Accepted'
    
    try:
        db.session.commit()
        flash('Request accepted successfully', 'success')
    except:
        db.session.rollback()
        flash('Error accepting request', 'danger')
    
    return redirect(url_for('service_provider_dashboard', provider_id=session['user_id']))

@app.route('/service_provider_dashboard/reject_request/<int:request_id>', methods=['GET','POST'])
def reject_request(request_id):
    if not session.get('is_serviceProvider'):
        flash('Please login first', 'danger')
        return redirect(url_for('user_login'))
    
    request_to_reject = HouseholdServiceRequest.query.get_or_404(request_id)
    
    try:
        db.session.delete(request_to_reject)
        db.session.commit()
        flash('Request rejected successfully', 'success')
    except:
        db.session.rollback()
        flash('Error rejecting request', 'danger')
    
    return redirect(url_for('service_provider_dashboard', provider_id=session['user_id']))


#homewoner dashboard

@app.route('/home_owner_dashboard/<int:homeowner_id>')
def home_owner_dashboard(homeowner_id):
    if not session.get('is_homeOwner'):
        flash('You are not Logged In, Please Log In', 'danger')
        return redirect('/user_login')
    
    home_owner = User.query.filter_by(id=homeowner_id).first()
    
    # Query services that have at least one approved service provider
    services_with_providers = HouseholdServices.query\
        .join(User, HouseholdServices.id == User.service_id)\
        .filter(User.is_serviceProvider == True)\
        .filter(User.is_approved == True)\
        .distinct()\
        .all()
    
    # Modified query to exclude pending public requests
    my_service_history = HouseholdServiceRequest.query.filter(
        HouseholdServiceRequest.homeowner_id == homeowner_id,
        (HouseholdServiceRequest.request_type == 'Private') |  # Show all private requests
        (HouseholdServiceRequest.request_type == 'Public' and  # Show only accepted public requests
         HouseholdServiceRequest.status != 'Pending')
    ).all()
    
    return render_template('home_owner_dashboard.html', 
                         home_owner=home_owner, 
                         services=services_with_providers,
                         my_service_history=my_service_history)


# Request routes in app.py
@app.route('/request_service/<int:service_id>/<int:homeowner_id>', methods=['POST'])
def request_service(service_id, homeowner_id):
    if not session.get('is_homeOwner'):
        flash('Please login first', 'danger')
        return redirect(url_for('user_login'))
    
    request_type = request.form.get('request_type')
    description = request.form.get('description')
    
    if request_type == 'Private':
        service_provider_id = request.form.get('service_provider_id')
        if not service_provider_id:
            flash('Please select a service provider for private requests', 'danger')
            return redirect(url_for('home_owner_dashboard', homeowner_id=homeowner_id))
        
        # Create single request for selected provider
        new_request = HouseholdServiceRequest(
            service_id=service_id,
            homeowner_id=homeowner_id,
            serviceProvider_id=service_provider_id,
            request_type='Private',
            status='Pending',
            description=description,
            date_created=datetime.now().date()
        )
        
        try:
            db.session.add(new_request)
            db.session.commit()
            flash('Service request submitted successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting service request: {str(e)}', 'danger')
    
    else:  # Public request
        # Find all approved service providers for this service
        service_providers = User.query.filter_by(
            service_id=service_id,
            is_serviceProvider=True,
            is_approved=True
        ).all()
        
        if not service_providers:
            flash('No approved service providers available for this service', 'danger')
            return redirect(url_for('home_owner_dashboard', homeowner_id=homeowner_id))
        
        # Create request for each service provider
        try:
            for provider in service_providers:
                new_request = HouseholdServiceRequest(
                    service_id=service_id,
                    homeowner_id=homeowner_id,
                    serviceProvider_id=provider.id,
                    request_type='Public',
                    status='Pending',
                    description=description,
                    date_created=datetime.now().date()
                )
                db.session.add(new_request)
            
            db.session.commit()
            flash('Public service request submitted successfully to all providers', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting public service request: {str(e)}', 'danger')
    
    return redirect(url_for('home_owner_dashboard', homeowner_id=homeowner_id))

@app.route('/rate_service/<int:request_id>', methods=['GET', 'POST'])
def rate_service(request_id):
    if not session.get('is_homeOwner'):
        flash('Please login first', 'danger')
        return redirect(url_for('user_login'))
    
    service_request = HouseholdServiceRequest.query.get_or_404(request_id)
    
    if request.method == 'POST':
        rating = float(request.form.get('rating'))
        review = request.form.get('review')
        
        # Update the service request with rating and review
        service_request.ratings_by_homeowner = rating
        service_request.review_by_homeowner = review
        
        # Update the service provider's average rating
        provider = service_request.service_provider
        provider.ratings_count += 1
        provider.average_rating = ((provider.average_rating * (provider.ratings_count - 1)) + rating) / provider.ratings_count
        
        try:
            db.session.commit()
            flash('Thank you for your rating!', 'success')
            return redirect(url_for('home_owner_dashboard', homeowner_id=session['user_id']))
        except:
            db.session.rollback()
            flash('Error submitting rating', 'danger')
    
    return render_template('rate_service.html', service_request=service_request)

@app.route('/home_owner_dashboard/close_request/<int:request_id>', methods=['POST'])
def close_request(request_id):
    if not session.get('is_homeOwner'):
        flash('Please login first', 'danger')
        return redirect(url_for('user_login'))
    
    request_to_close = HouseholdServiceRequest.query.get_or_404(request_id)

    # Check if the request status is 'Accepted'
    if request_to_close.status != 'Accepted':
        flash('You can only close requests that have been accepted.', 'danger')
        return redirect(url_for('home_owner_dashboard', homeowner_id=session['user_id']))

    # Update the status to 'Completed' and add rating
    request_to_close.status = 'Completed'
    request_to_close.date_closed = datetime.now().date()
    
    try:
        db.session.commit()
        # Redirect to rating form instead of dashboard
        return redirect(url_for('rate_service', request_id=request_id))
    except:
        db.session.rollback()
        flash('Error closing request', 'danger')
    
    return redirect(url_for('home_owner_dashboard', homeowner_id=session['user_id']))

# homeowner edit request
@app.route('/home_owner_dashboard/edit_request/<int:request_id>', methods=['GET', 'POST'])
def edit_request(request_id):
    if not session.get('is_homeOwner'):
        flash('Please login first', 'danger')
        return redirect(url_for('user_login'))
    
    request_to_edit = HouseholdServiceRequest.query.get_or_404(request_id)

    # Check if the request status is 'Accepted'
    if request_to_edit.status == 'Accepted':
        flash('You cannot edit this request as it has already been accepted.', 'danger')
        return redirect(url_for('home_owner_dashboard', homeowner_id=session['user_id']))

    if request.method == 'POST':
        # Update the description
        request_to_edit.description = request.form['description']
        
        try:
            db.session.commit()
            flash('Request updated successfully', 'success')
            return redirect(url_for('home_owner_dashboard', homeowner_id=session['user_id']))
        except:
            db.session.rollback()
            flash('Error updating request', 'danger')

    return render_template('edit_request.html', request=request_to_edit)

@app.route('/home_owner_dashboard/delete_request/<int:request_id>', methods=['POST'])
def delete_request(request_id):
    if not session.get('is_homeOwner'):
        flash('Please login first', 'danger')
        return redirect(url_for('user_login'))
    
    request_to_delete = HouseholdServiceRequest.query.get_or_404(request_id)

    # Check if the request status is 'Accepted'
    if request_to_delete.status == 'Accepted':
        flash('Cannot delete an accepted request', 'danger')
        return redirect(url_for('home_owner_dashboard', homeowner_id=session['user_id']))

    try:
        db.session.delete(request_to_delete)
        db.session.commit()
        flash('Service request deleted successfully', 'success')
    except:
        db.session.rollback()
        flash('Error deleting service request', 'danger')
    
    return redirect(url_for('home_owner_dashboard', homeowner_id=session['user_id']))

@app.route('/home_owner_dashboard/search/<int:homeowner_id>', methods=['GET', 'POST'])
def search_services(homeowner_id):
    if not session.get('is_homeOwner'):
        flash('Please login first', 'danger')
        return redirect(url_for('user_login'))

    home_owner = User.query.get_or_404(homeowner_id)
    services = []
    
    if request.method == 'POST':
        service_name = request.form.get('service_name', '').strip().lower()
        pincode = request.form.get('pincode', '').strip().lower()
        address = request.form.get('address', '').strip().lower()

        # Start with a base query for services with approved providers
        query = HouseholdServices.query\
            .join(User, HouseholdServices.id == User.service_id)\
            .filter(User.is_serviceProvider == True)\
            .filter(User.is_approved == True)

        if service_name:
            query = query.filter(HouseholdServices.service_name.ilike(f'%{service_name}%'))
        if pincode:
            query = query.filter(User.pincode.ilike(f'%{pincode}%'))
        if address:
            query = query.filter(User.address.ilike(f'%{address}%'))

        # Get distinct services
        services = query.distinct().all()

    return render_template('homeowner_search.html', 
                         services=services, 
                         home_owner=home_owner)

# Route for service providers to view public requests
@app.route('/service_provider/public_requests/<int:provider_id>')
def public_requests(provider_id):
    if not session.get('is_serviceProvider'):
        flash('Please login first', 'danger')
        return redirect(url_for('user_login'))
    
    provider = User.query.get_or_404(provider_id)
    # Get unique public requests for the provider's service
    public_requests = HouseholdServiceRequest.query.filter_by(
        service_id=provider.service_id,
        request_type='Public',
        status='Pending',
        serviceProvider_id=provider_id  # Add this to get only requests for this provider
    ).distinct().all()
    
    return render_template('public_requests.html', 
                         provider=provider, 
                         public_requests=public_requests)

# Route for service providers to submit bid
@app.route('/service_provider/submit_bid/<int:request_id>', methods=['POST'])
def submit_bid(request_id):
    if not session.get('is_serviceProvider'):
        flash('Please login first', 'danger')
        return redirect(url_for('user_login'))
    
    service_request = HouseholdServiceRequest.query.get_or_404(request_id)
    service_request.status = 'Bid_Submitted'
    
    try:
        db.session.commit()
        flash('Bid submitted successfully', 'success')
    except:
        db.session.rollback()
        flash('Error submitting bid', 'danger')
    
    return redirect(url_for('public_requests', provider_id=session['user_id']))

# Route for service providers to decline request
@app.route('/service_provider/decline_request/<int:request_id>', methods=['POST'])
def decline_request(request_id):
    if not session.get('is_serviceProvider'):
        flash('Please login first', 'danger')
        return redirect(url_for('user_login'))
    
    service_request = HouseholdServiceRequest.query.get_or_404(request_id)
    service_request.status = 'Declined'
    
    try:
        db.session.commit()
        flash('Request declined', 'success')
    except:
        db.session.rollback()
        flash('Error declining request', 'danger')
    
    return redirect(url_for('public_requests', provider_id=session['user_id']))

# Route for homeowners to view their public requests and bids
@app.route('/home_owner/public_requests/<int:homeowner_id>')
def view_public_requests(homeowner_id):
    if not session.get('is_homeOwner'):
        flash('Please login first', 'danger')
        return redirect(url_for('user_login'))
    
    # Get unique public requests
    public_requests = db.session.query(HouseholdServiceRequest).filter(
        HouseholdServiceRequest.homeowner_id == homeowner_id,
        HouseholdServiceRequest.request_type == 'Public'
    ).distinct(HouseholdServiceRequest.service_id).all()
    
    return render_template('view_public_requests.html', 
                         public_requests=public_requests,
                         homeowner_id=homeowner_id)

# Route for homeowners to accept a bid
@app.route('/home_owner/accept_bid/<int:request_id>/<int:provider_id>', methods=['POST'])
def accept_bid(request_id, provider_id):
    if not session.get('is_homeOwner'):
        flash('Please login first', 'danger')
        return redirect(url_for('user_login'))
    
    # Get the original request
    original_request = HouseholdServiceRequest.query.get_or_404(request_id)
    
    # Update status of all related public requests
    related_requests = HouseholdServiceRequest.query.filter_by(
        service_id=original_request.service_id,
        homeowner_id=original_request.homeowner_id,
        request_type='Public'
    ).all()
    
    try:
        for req in related_requests:
            if req.serviceProvider_id == provider_id:
                req.status = 'Accepted'
            else:
                req.status = 'Rejected'
        
        db.session.commit()
        flash('Bid accepted successfully', 'success')
    except:
        db.session.rollback()
        flash('Error accepting bid', 'danger')
    
    return redirect(url_for('home_owner_dashboard', homeowner_id=session['user_id']))

@app.route('/admin_dashboard/delete_service_request/<int:request_id>', methods=['POST'])
def delete_service_request(request_id):
    if not session.get('is_admin'):
        flash('Please login first', 'danger')
        return redirect(url_for('admin_login'))
    
    request_to_delete = HouseholdServiceRequest.query.get_or_404(request_id)
    
    try:
        db.session.delete(request_to_delete)
        db.session.commit()
        flash('Service request deleted successfully', 'success')
    except:
        db.session.rollback()
        flash('Error deleting service request', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/service_provider/search/<int:provider_id>', methods=['GET', 'POST'])
def service_provider_search(provider_id):
    if not session.get('is_serviceProvider'):
        flash('Please login first', 'danger')
        return redirect(url_for('user_login'))
    
    provider = User.query.get_or_404(provider_id)
    completed_requests = []

    if request.method == 'POST':
        date_str = request.form.get('date', '').strip()
        address = request.form.get('address', '').strip().lower()
        pincode = request.form.get('pincode', '').strip()

        # Start with base query
        query = HouseholdServiceRequest.query.filter_by(
            serviceProvider_id=provider_id,
            status='Completed'
        )

        # Apply filters
        if date_str:
            try:
                search_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                query = query.filter(HouseholdServiceRequest.date_closed == search_date)
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD', 'danger')

        if address:
            query = query.join(User, HouseholdServiceRequest.homeowner_id == User.id)\
                        .filter(User.address.ilike(f'%{address}%'))

        if pincode:
            query = query.join(User, HouseholdServiceRequest.homeowner_id == User.id)\
                        .filter(User.pincode.ilike(f'%{pincode}%'))

        completed_requests = query.all()

    return render_template('service_provider_search.html', 
                         provider=provider,
                         completed_requests=completed_requests)

@app.route('/service_provider/analytics/<int:provider_id>')
def service_provider_analytics(provider_id):
    if not session.get('is_serviceProvider'):
        flash('Please login first', 'danger')
        return redirect(url_for('user_login'))
    
    provider = User.query.get_or_404(provider_id)
    
    # Get all completed requests with ratings
    rated_requests = HouseholdServiceRequest.query.filter_by(
        serviceProvider_id=provider_id,
        status='Completed'
    ).filter(HouseholdServiceRequest.ratings_by_homeowner > 0).all()
    
    # Get request counts by status
    pending_count = HouseholdServiceRequest.query.filter_by(
        serviceProvider_id=provider_id,
        status='Pending'
    ).count()
    
    accepted_count = HouseholdServiceRequest.query.filter_by(
        serviceProvider_id=provider_id,
        status='Accepted'
    ).count()
    
    completed_count = HouseholdServiceRequest.query.filter_by(
        serviceProvider_id=provider_id,
        status='Completed'
    ).count()
    
    # Calculate total revenue from completed services
    completed_requests = HouseholdServiceRequest.query.filter_by(
        serviceProvider_id=provider_id,
        status='Completed'
    ).all()
    
    # Generate graphs
    graphs = {}
    
    # Ratings Distribution Graph
    plt.figure(figsize=(8, 6))
    ratings = [req.ratings_by_homeowner for req in rated_requests]
    plt.hist(ratings, bins=5, range=(0.5, 5.5), color='skyblue', edgecolor='black')
    plt.title('Distribution of Ratings')
    plt.xlabel('Rating')
    plt.ylabel('Number of Ratings')
    plt.grid(True, alpha=0.3)
    
    # Save to base64 string
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    graphs['ratings'] = base64.b64encode(img.getvalue()).decode()
    plt.close()
    
    # Request Status Graph
    plt.figure(figsize=(8, 6))
    statuses = ['Pending', 'Accepted', 'Completed']
    counts = [pending_count, accepted_count, completed_count]
    plt.bar(statuses, counts, color=['orange', 'green', 'blue'])
    plt.title('Request Status Distribution')
    plt.xlabel('Status')
    plt.ylabel('Number of Requests')
    plt.grid(True, alpha=0.3)
    
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    graphs['status'] = base64.b64encode(img.getvalue()).decode()
    plt.close()
    
    total_revenue = sum(req.service.base_price for req in completed_requests)
    
    return render_template('service_provider_analytics.html',
                         provider=provider,
                         graphs=graphs,
                         total_revenue=total_revenue,
                         ratings_count=provider.ratings_count,
                         average_rating=provider.average_rating)

if __name__ == "__main__":
    app.run(debug = True)