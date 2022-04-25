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
    url.save(f'myapp/static/qrCode' + str(k) + '.png')

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
            generate_code(code_link,k)
            flash('New event has been added!', category='success')
            return redirect(url_for('view.home'))
    return render_template("events.html", user=current_user, title='New Event',
                           form=form, legend='Add New Events')

@view.route('/event/open/<int:value>', methods=['GET','POST'])
@login_required
def open_event(value): #display each single event and when they were created
    item = Event.query.get_or_404(value)
    return render_template("affair.html", item =item, user=current_user)

@view.route('/code-page/<int:n>')
@login_required
def display_code(n):
    #display qrcode to each event on the click of button
    code_id = Event.query.get_or_404(n) #holds the id
    return render_template("code-page.html", user=current_user, code=code_id )

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
                return redirect(url_for('view.open_event', value=edit.id))
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


@view.route('/delete/<int:num>')
@login_required
def delete_event(num):
    item_delete = Event.query.get_or_404(num)
    n = 'app/static/qrCode' + str(num) + '.png'
    path = 'app/uploads/Sheet1' + str(num) + '.txt'
    #file= 'app/uploads/' + filename + '.xlsx'
    nid =  current_user
    if nid:
        try:
            title = item_delete.title
            con.session.delete(item_delete)
            con.session.commit()
            delete_pic(n)
            delete_sheet(path)
            # should delete the excel file when event is deleted#delete_excel(file)
            flash("The "+ title + " event has been deleted")
            events = Event.query.order_by(Event.timestamp)
            return redirect(url_for('view.home'))
        except requests.exceptions.RequestException as e:
            flash("Not able to delete event try again",category='error')
            print(e)
            events = Event.query.order_by(Event.timestamp)
            return render_template("home.html",events=events, user=current_user)
    else:
        flash("Can't delete this event", category='error')
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
@view.route('/find/student', methods=['GET','POST'])
@login_required
def search_students():
    form = SearchForm()
    event = Event.query
    student = Student.query
    if form.validate_on_submit():
        student = student.filter(Student.name.like('%' + form.searched.data + '%'))
        student = student.order_by(Student.name).all()
        event = event.filter(Student.name)
        return render_template("search_students.html", user=current_user,student=student, searched=form.searched.data, form=form)
    return render_template("find_form.html", user=current_user, form=form)

@view.route('/loadfile/<int:uniq>', methods=['POST','GET'])
@login_required
def upload_file(uniq): #upload file excel file and
    form = UploadForm()
    k = uniq
    if form.validate_on_submit():
        uploaded_file = form.name.data
        filename = secure_filename(form.name.data.filename)
        #check if file is an excel file
        if filename.endswith(('.xlsx', '.xls')):
            uploaded_file.save(f'myapp/uploads/' + filename)
            sv(k,uploaded_file,filename)
            flash("File was uploaded", category='success')
        else:
            flash("File type is not supported", category='error')
        return redirect(url_for('view.open_event', value=k))
    return render_template("upload-file.html",form=form, user=current_user, uniq=k)

def sv(id, uploaded_file,filename):
    #convert to text csv for each event
    xl = pd.ExcelFile(uploaded_file)
    for sheet in xl.sheet_names:
        new_cols = ['n0','email','name','classYear']
        #df = pd.read_excel(r'app/uploads/' + filename, names=new_cols, sheet_name=sheet)
        data = pd.read_excel(r'myapp/uploads/' + filename, sheet_name=sheet, header=None,
                             names=["n0","email","name",'classYear'],skiprows=1)
        file = pd.DataFrame(data, columns=['n0','email','name','classYear'])
        path = f'myapp/uploads/'
        file.to_csv(path + sheet + str(id) + '.txt', header=False, index=False, sep=',')
    track(id)

def track(id):
    try:
        f_name = 'myapp/uploads/Sheet1' + str(id) + '.txt'
        file = get_file(f_name)
        ids, names, emails, years = get_info(file)
        for i in range(len(names)):
            entry = Student(name=names[i], email=emails[i], classYear=years[i], att_ls=id)
            con.session.add(entry)
            con.session.commit()
        return redirect(url_for('view.track_att', id=id))
    except requests.exceptions.RequestException as e:
        print(e)
        flash("Invalid data", category='error')
        return redirect(url_for('view.open_event', value=id))

@view.route('/attendance/<int:id>', methods=['GET','POST'])
@login_required
def track_att(id):
    f_name = 'myapp/uploads/Sheet1' + str(id) + '.txt'
    if os.path.exists(f_name):
        attendance = Student.query.filter_by(att_ls=id).all()
        item = Event.query.get_or_404(id)
    else:
        flash("This event does not have any student data, please upload.", category='error')
        return redirect(url_for('view.open_event', value=id))
    return render_template("attendance.html", user=current_user, attendance=attendance,item=item)


def get_file(f):
    filename = f
    ## open file
    file = open(filename)
    ## start at first byte [thing] in file
    file.seek(0)
    ## break up and store by '\n' characters
    file = file.readlines()
    return file

def get_info(file):
    ## initializes local function variables
    ids, names, emails, years = [], [], [],[]
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
        email = i[-2]
        first = i[-3]
        year = i[-1]
        ## add emails, names, years and id's
        emails.append(email)
        names.append(first)
        years.append(year)
        ids.append(event)
    return ids,names,emails, years


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

def remove_sheet(filename, student):
    with open(filename, 'r') as fr:
        lines = fr.readlines()
    with open(filename, "w") as f:
        for line in lines:
            if line.find(student) != -1:
                pass
            else:
                f.write(line)

@view.route('/event_number/<int:e_num>/delete_students', methods=['GET','POST'])
@login_required
def delete_students(e_num):
    event_num = Event.query.get_or_404(e_num)
    filename = 'myapp/uploads/Sheet1' + str(e_num) + '.txt'
    attendance = Student.query.filter_by(att_ls=e_num).all()
    if request.method == 'POST':
        student_num = request.form.get("delete_id")
        if len(attendance) > 1:
            item_delete = Student.query.get_or_404(student_num)
            student = item_delete.name
            con.session.delete(item_delete)
            con.session.commit()
            remove_sheet(filename,student)
            flash('The student was successfully removed from the list.', category='success')
            return redirect(url_for('view.track_att', id=e_num))
        else:
            flash("There must be at least 1 person on the attendance list",category='error')
    return render_template("delete_student_page.html", user=current_user, attendance=attendance, item=event_num)


def add_sheet(filename,student_info):
    num = student_info.id
    name = student_info.name
    email = student_info.email
    year = student_info.classYear
    with open(filename, "a+") as f:
        f.seek(0)
        data_len = f.read(100)
        if len(data_len) >0:
            f.write("\n")
        f.write(str(num)+','+email+','+name+','+year) #change if sheet gets fixed

@view.route('/attendance/add_students/<int:num>', methods=['GET','POST'])
@login_required
def add_students(num):
    item = Event.query.get_or_404(num)
    form= StudentForm()
    filename = 'myapp/uploads/Sheet1' + str(num) + '.txt'
    #add name to sheet as well
    if request.method == 'POST' and form.validate_on_submit():
        s_name = request.form.get("name")
        s_email = request.form.get("email")
        s_year = request.form.get("year")
        new_student = Student(name=form.name.data, email=form.email.data, classYear=form.year.data,att_ls=num)
        con.session.add(new_student)
        con.session.commit()
        # add_entry= Student.query.get_or_404()
        add_sheet(filename, new_student)
        flash('New student was added', category='success')
        return redirect(url_for('view.track_att', id=num))
    return render_template("attendance.html", user=current_user, form=form, item=item)

def create_figure(id):
    data = pd.read_csv(r'myapp/uploads/Sheet1' + str(id)  + '.txt', names=['n0','email','name','classYear'])
    df = pd.DataFrame(data)
    fig = px.bar(df, x='classYear',barmode='group',labels={"classYear": "Year"})
    return fig


@view.route("/plot/<int:number>", methods=['GET', 'POST'])
@login_required
def visualize(number):
    fig = create_figure(number)
    # fig2 = generate_chart(id)
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    # graph_json2 = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)
    header = "Student Attendance Data"
    description = """ 
    Chart shows you the amount of students that attended by each class year
        """
    return render_template("figures.html", user=current_user, graphJSON=graph_json,header=header,description=description,
                           item=number)

@view.route('/calendar', methods=['GET','POST'])
@login_required
def calendar():
    events = Event.query.all()
    return render_template('calendar.html', user=current_user, data=events)

