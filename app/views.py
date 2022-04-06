from datetime import datetime, timedelta
import os
import qrcode
import requests
from flask import Blueprint, render_template, flash, url_for, redirect, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os.path
import pandas as pd
from . import con
from .forms import EventForm, SearchForm, UploadForm, StudentForm, EditForm
from .models import Event, Student
from sqlalchemy import desc
import json
import plotly
import plotly.express as px
from sqlalchemy.sql import select

view = Blueprint('view', __name__)

@view.route('/', methods=['GET','POST']) #url to get to here
@login_required
def home():
    #display all the events on one page
    events = Event.query.order_by(desc(Event.timestamp))
    return render_template("home.html", user=current_user, events=events)

def generate_code(s, k):
    #make qr code and save it to directory
    url = qrcode.make(s) # Create code
    url.save(f'app/static/qrCode' + str(k) + '.png')

@view.route('/events', methods=['GET','POST']) #url to get to event page
@login_required
def add_events():
    #create new event and add to database
    form = EventForm()
    if form.validate_on_submit():
        date_str = request.form.get('event-date')
        date_processing = date_str.replace('T', '-').replace(':', '-').split('-')
        date_processing = [int(v) for v in date_processing]
        new_date = datetime(*date_processing)
        code_link = form.link.data
        event = Event(title= form.title.data, note= form.content.data,link=code_link, date= new_date,
                      user_id= current_user.id, timestamp=datetime.utcnow() - timedelta(hours=4))
        if len(form.title.data) < 1 or len(form.content.data) < 2:
            flash('Event name is too short or there is little to no description', category='error')
        else:
            con.session.add(event)
            con.session.commit()
            evn = Event.query.filter_by(title=form.title.data).first() # change id
            k = evn.id
            print(k)
            generate_code(code_link,k)
            flash('New event has been added!', category='success')
            return redirect(url_for('view.home'))
    return render_template("events.html", user=current_user, title='New Event',
                           form=form, legend='Add New Events')

@view.route('/event/open/<int:id>', methods=['GET','POST'])
@login_required
def open_event(id): #display each single event and when they were created
    item = Event.query.get_or_404(id)
    return render_template("affair.html", item =item, user=current_user)

@view.route('/code-page/<int:id>')
@login_required
def display_code(id):
    #display qrcode to each event on the click of button
    k = Event.query.get_or_404(id) #holds the id
    return render_template("code-page.html", user=current_user, code= k )

@view.route('/event/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit_event(id):
    #prepopulate with data that was already there
    edit = Event.query.get_or_404(id)
    form = EditForm(obj=current_user)
    if edit.user_id == current_user.id:
        if request.method == 'GET':
            form.title.data = edit.title
            form.content.data = edit.note
        if  form.validate_on_submit() and request.method == 'POST':
            if len(form.title.data) < 1 or len(form.content.data) < 2:
                flash('Event name is too short or there is little to no description', category='error')
            else:
                edit.title = form.title.data
                edit.note = form.content.data
                con.session.add(edit)
                con.session.commit()
                flash("Event has successfully been edited!", category='success') #change message
                return redirect(url_for('view.open_event', id=edit.id))
        return render_template('edit_event.html', form=form, user=current_user, legend='Update Event')


def delete_pic(n): # n is the path
    # delete code picture when event gets deleted
    if os.path.exists(n):
        os.remove(n)
    else:
        flash("The qr-code does not exist", category='error')

def delete_sheet(p):
    #delete sheet if an event is deleted, so Id's are not mixed up
    if os.path.exists(p):
        os.remove(p)
    # else:
    #     flash("Student data was never uploaded", category='warning')

def delete_excel(file):
    if os.path.exists(file):
        os.remove(file)

@view.route('/delete/<int:id>')
@login_required
def delete_event(id):
    item_delete = Event.query.get_or_404(id)
    n = 'app/static/qrCode' + str(id) + '.png'
    path = 'app/uploads/Sheet1' + str(id) + '.txt'
    #file= 'app/uploads/' + filename + '.xlsx'
    nid =  current_user.id
    if nid == item_delete.user_id:
        try:
            con.session.delete(item_delete)
            con.session.commit()
            delete_pic(n)
            delete_sheet(path)
            # should delete the excel file when event is deleted
            #delete_excel(file)
            flash("Event has been deleted")
            events = Event.query.order_by(Event.timestamp)
            return render_template("home.html",events=events, user=current_user)
        except requests.exceptions.RequestException as e:
            flash("Not able to delete event try again")
            print(e)
            events = Event.query.order_by(Event.timestamp)
            return render_template("home.html",events=events, user=current_user)
    else:
        flash("Can't delete this")
        items = Event.query.order_by(Event.timestamp)
        return render_template("home.html", events=items, user=current_user)

@view.context_processor
def base():
    form = SearchForm()
    return dict(form=form)

@view.route('/event/search', methods=['GET','POST'])
@login_required
def search_events():
    form = SearchForm()
    events = Event.query
    if form.validate_on_submit():
        events = events.filter(Event.title.like('%' + form.searched.data + '%'))
        events = events.order_by(Event.title).all()
    return render_template("search.html", form=form,searched =form.searched.data, events=events, user=current_user)

# in progress
@view.route('/find/', methods=['GET','POST'])
@login_required
def search_students():
    form = SearchForm()
    student = Student.query
    event = Event.query
    if form.validate_on_submit():
        # student = student.filter(Student.name.like('%' + form.searched.data + '%'))
        # student = student.order_by(Student.name).all()
        for c, i in con.session.query(Event, Student).filter(Event.id == Student.att_ls).all():
            student = student.filter(Student.name.like('%' + form.searched.data + '%'))
            # print("Event: {} Student Name: {} Year: {}".format(c.id, c.title, i.name, i.classYear))
        return render_template("search_students.html", user=current_user,event=event, searched=form.searched.data, form=form)
    return render_template("find_form.html", user=current_user, form=form)

@view.route('/loadfile/<int:id>', methods=['POST','GET'])
@login_required
def upload_file(id): #upload file excel file and
    form = UploadForm()
    k = id
    if form.validate_on_submit():
        uploaded_file = form.name.data
        filename = secure_filename(form.name.data.filename)
        if filename != '':
            uploaded_file.save(f'app/uploads/' + filename)
            sv(k,uploaded_file,filename)
            flash("File was uploaded", category='success')
        return redirect(url_for('view.open_event', id=k))
    return render_template("upload-file.html",form=form, user=current_user, id=k)

def sv(id, uploaded_file,filename):
    #convert to text csv for each event
    xl = pd.ExcelFile(uploaded_file)
    for sheet in xl.sheet_names:
        data = pd.read_excel(r'app/uploads/' + filename, sheet_name=sheet)
        df = pd.DataFrame(data, columns=['ID', 'Full Name:', 'Email2', 'Class Year:'])
        df.rename(columns={'Class Year:': 'classYear', 'Full Name:': 'name', 'Email2': 'email', 'ID': 'id'},
                  inplace=True, errors='raise')
        file = pd.DataFrame(df, columns=['id', 'classYear', 'name', 'email'])
        path = f'app/uploads/'
        file.to_csv(path + sheet + str(id) + '.txt', header=False, index=False, sep=',')
    track(id)

def track(id):
    try:
        f_name = 'app/uploads/Sheet1' + str(id) + '.txt'
        file = get_file(f_name)
        ids, names, emails, years = get_info(file)
        for i in range(len(ids)):
            new = Student(name=names[i], email=emails[i], classYear=years[i], att_ls=id)
            con.session.add(new)
            con.session.commit()
        return redirect(url_for('view.track_att', id=id))
    except requests.exceptions.RequestException as e:
        flash("Invalid data", category='error')
        return redirect(url_for('view.open_event', id=id))

@view.route('/attendance/<int:id>', methods=['GET','POST'])
@login_required
def track_att(id):
    f_name = 'app/uploads/Sheet1' + str(id) + '.txt'
    if os.path.exists(f_name):
        attendance = Student.query.filter_by(att_ls=id)
        item = Event.query.get_or_404(id)
    else:
        flash("This event does not have any student data, please upload.", category='error')
        return redirect(url_for('view.open_event', id=id))
    return render_template("attendance.html", user=current_user, attendance=attendance,item=item)


def get_file(f):
    filename = f
    ## open file
    file = open(filename)
    ## start at first byte [thing] in file
    file.seek(0)
    ## break up and store by '\n' characters
    file = file.readlines()
    ## removes the column titles from file
    return file


def get_info(file):
    ## initializes local function variables
    ids, emails, names, years = [], [], [], []
    ls = []
    for x in file:
         ## split by the comma and add to new list
        x = x.split(",")
        ls.append(x)
    for i in ls:
        ## initialize local for loop variables
        event = ""
        email = ""
        first = ""
        year = ""
        ## indexes based on where in file
        event = i[0]
        email = i[-1]
        first = i[-2]
        #last = i[-3]
        year = i[-3]
        ## add emails, names, years and id's
        emails.append(email)
        names.append(first)
        years.append(year)
        ids.append(event)
    return ids, names,emails, years


@view.route('/event/recent', methods=['GET','POST'])
@login_required
def filter_event():
    form = SearchForm()
    if request.method == 'POST':
        start_range = request.form.get("start")
        end_range = request.form.get("end")
        search_query = Event.query.filter(Event.date.between(start_range,end_range))
        refined_query = search_query.order_by(Event.date).all()
        return render_template("search.html", user=current_user, form = form, events= refined_query)
    return render_template("filter.html", user=current_user, form= form)

# in progress
@view.route('/delete_students/<int:id>', methods=['POST', 'GET'])
@login_required
def delete_students(id):
    item = Event.query.get_or_404(id)
    attendance = Student.query.filter_by(att_ls=id)
    if request.method == 'POST':
        student = request.form.get("delete_id")
        item_delete = con.session.query(Event, Student).filter(Event.id == Student.att_ls).all()
        for c, i in item_delete:
            print("Event: {} Student Name: {} Year: {}".format(c.id, c.title, i.name, i.classYear))
            con.session.delete(student== i.id)
            con.session.commit()
            # flash("success")
            # else:
            #     flash("Failed", category='error')
        flash('Successfully Deleted!')
        return redirect(url_for('view.open_event', id=id))
    return render_template("delete_students.html", user=current_user,attendance=attendance, item=item)

#in progress
@view.route('/add_students/<int:id>', methods=['GET','POST'])
@login_required
def add_students(id):
    form = StudentForm()
    if form.validate_on_submit():
        pass
    return render_template("delete_students.html", user=current_user, form=form)

def create_figure(id):
    data = pd.read_csv(r'app/uploads/Sheet1' + str(id)  + '.txt', names=['id', 'classYear', 'name', 'email'])
    df = pd.DataFrame(data)
    fig = px.bar(df, x='classYear',barmode='group',labels={"classYear": "Year"})
    return fig

def generate_chart(id):
    data = pd.read_csv(r'app/uploads/Sheet1' + str(id) + '.txt', names=['id', 'classYear', 'name', 'email'])
    df = pd.DataFrame(data)
    pie = px.pie(df,names='name')
    return pie

@view.route("/plot/<int:id>", methods=['GET', 'POST'])
@login_required
def visualize(id):
    fig = create_figure(id)
    fig2 = generate_chart(id)
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    graph_json2 = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)
    header = "Student Attendance Data"
    description = """ 
    Chart shows you the amount of students that attended by each class year
        """
    return render_template("figures.html", user=current_user, graphJSON=graph_json,header=header,description=description,
                           item=id, pie= graph_json2)

@view.route('/calendar', methods=['GET','POST'])
@login_required
def calendar():
    events = Event.query.all()
    return render_template('calendar.html', user=current_user, data=events)

