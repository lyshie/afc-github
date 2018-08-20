# -*- coding: utf-8 -*-

import os
from app import app, db
from app.models.user import User
from app.models.course import Course
from app.models.selection import Selection
from app.models.history import History
from app.tools.import_course import import_course
from app.tools.import_user import import_user
from app.tools.log import logging
from flask_login import login_required
from flask import render_template, url_for, redirect, request, flash, abort, g
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, BooleanField, TextField
from wtforms.validators import DataRequired
from wtforms.fields.html5 import IntegerField, TelField
from flask_wtf.file import FileField,  FileAllowed,  FileRequired
from flask_babel import gettext as _, lazy_gettext
from sqlalchemy import func
from sqlalchemy.sql import label
from werkzeug.utils import secure_filename
from functools import wraps
from flask_login import login_user

'''
    Admin constraint decorator
'''


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.uid != 0:
            return abort(403)
        else:
            return f(*args, **kwargs)

    return decorated_function


class CourseSelectForm(FlaskForm):
    cid = SelectField(
        lazy_gettext("Course"), choices=[])


class CourseEditForm(FlaskForm):
    cid = TextField(
        lazy_gettext("Course"), validators=[DataRequired()], render_kw={'readonly': 'readonly'})
    name = TextField(
        lazy_gettext("Name"), validators=[DataRequired()])
    description = TextAreaField(
        lazy_gettext("Description"), validators=[DataRequired()], render_kw={'rows': '4'})
    classroom = StringField(
        lazy_gettext("Classroom"), validators=[DataRequired()])
    price = IntegerField(
        lazy_gettext("Price"), validators=[DataRequired()])
    teacher = StringField(
        lazy_gettext("Teacher"), validators=[DataRequired()])
    teacher_tag = TextAreaField(
        lazy_gettext("Tag"), validators=[DataRequired()], render_kw={'rows': '4'})
    teacher_phone = StringField(
        lazy_gettext("Teacher phone"), validators=[DataRequired()])
    grades = StringField(
        lazy_gettext("Grades"), validators=[DataRequired()], render_kw={'readonly': 'readonly'})
    upbound = IntegerField(
        lazy_gettext("Upper limit"), validators=[DataRequired()])
    lowbound = IntegerField(
        lazy_gettext("Lower limit"), validators=[DataRequired()])
    datetime = StringField(
        lazy_gettext("Date time"), validators=[DataRequired()])
    state = SelectField(
        lazy_gettext("State"), choices=[('0', lazy_gettext('Normal')), ('1', lazy_gettext('Suspended')), ('2', lazy_gettext('Test'))], validators=[DataRequired()])
    submit = SubmitField(lazy_gettext("Update"))


class CourseUploadForm(FlaskForm):
    csv = FileField(lazy_gettext('CSV file'), validators=[
                    FileRequired(), FileAllowed(['csv'], _('CSV only!'))])
    replace = BooleanField(lazy_gettext("Replace"))
    submit = SubmitField(lazy_gettext("Upload"))


class UserUploadForm(FlaskForm):
    csv = FileField(lazy_gettext('CSV file'), validators=[
                    FileRequired(), FileAllowed(['csv'], _('CSV only!'))])
    replace = BooleanField(lazy_gettext("Replace"))
    submit = SubmitField(lazy_gettext("Upload"))


@app.route("/admin/course/list", methods=["GET"])
@app.route("/admin/course/list/<int:cid>", methods=["GET"])
@login_required
@admin_required
def admin_course_list(cid=None):

    # must be admin
    '''
    if g.user.uid != 0:
        abort(403)
    '''

    if cid is None:
        cid = Course.query.first().cid

    choices = []
    courses = Course.query.all()
    for c in courses:
        count = len(Selection.query.filter(Selection.course_id == c.cid).all())
        choices.append(
            [str(c.cid), u"{} - {} ({})".format(c.cid, c.name, count)])

    csform = CourseSelectForm()
    csform.cid.choices = choices
    csform.cid.default = cid
    csform.process()

    selections = Selection.query.filter(
        Selection.course_id == cid).order_by(Selection.course_id).all()
    course = Course.query.filter(Course.cid == cid).first()

    return render_template("admin_course_list.html", csform=csform, selections=selections, course=course)


@app.route("/admin/course/view", methods=["GET"])
@app.route("/admin/course/view/<int:cid>", methods=["GET"])
@login_required
@admin_required
def admin_course_view(cid=None):

    # must be admin
    '''
    if g.user.uid != 0:
        abort(403)
    '''

    if cid is None:
        cid = Course.query.first().cid

    choices = []
    courses = Course.query.all()
    for c in courses:
        count = len(Selection.query.filter(Selection.course_id == c.cid).all())
        choices.append(
            [str(c.cid), u"{} - {} ({})".format(c.cid, c.name, count)])

    csform = CourseSelectForm()
    csform.cid.choices = choices
    csform.cid.default = cid
    csform.process()

    course = Course.query.filter(Course.cid == cid).first()
    ceform = CourseEditForm(obj=course)

    return render_template("admin_course_view.html", csform=csform, ceform=ceform)


@app.route("/admin/course/edit", methods=["POST"])
@login_required
@admin_required
def admin_course_edit():

    # must be admin
    '''
    if g.user.uid != 0:
        abort(403)
    '''

    ceform = CourseEditForm()

    if ceform.validate_on_submit():
        cid = request.form['cid']
        course = Course.query.filter(Course.cid == cid).first()
        if course is not None:
            ceform.populate_obj(course)
            db.session.commit()
            flash(_('Course information has been updated!'))

        return redirect(url_for("admin_course_view", cid=cid))
    else:
        abort(401)


@app.route("/admin/task", methods=["GET"])
@login_required
@admin_required
def admin_task():

    # must be admin
    '''
    if g.user.uid != 0:
        abort(403)
    '''

    stats = {
        _('User'): User.query.count(),
        _('Course'): Course.query.count(),
        _('Selection'): Selection.query.count(),
    }

    users = db.session.query(User.student_grade,
                             label('numbers', func.count(User.uid))
                             ).group_by(User.student_grade).order_by(User.student_grade).all()

    return render_template("admin_task.html", stats=stats, users=users)


@app.route("/admin/task/upload/course", methods=["GET", "POST"])
@login_required
@admin_required
def admin_task_upload_course():

    # must be admin
    '''
    if g.user.uid != 0:
        abort(403)
    '''

    form = CourseUploadForm()

    if form.validate_on_submit():

        filename = secure_filename(form.csv.data.filename)
        replace = form.replace.data

        csv_filename = os.path.join('uploads', filename)
        form.csv.data.save(csv_filename)
        result = import_course(filename=csv_filename, replace=replace)

        if result:
            flash(_('Course has been uploaded!'))
            logging(user_id=g.user.uid, message="Upload course. (filename={}, replace={})".format(
                filename, replace), ip=request.remote_addr)
        else:
            flash(_('ERROR: Failed to upload!'))
            logging(user_id=g.user.uid, message="Failed to upload course. (filename={}, replace={})".format(
                filename, replace), ip=request.remote_addr)
    else:
        filename = None

    return render_template("admin_task_upload_course.html", form=form, filename=filename)


@app.route("/admin/task/upload/user", methods=["GET", "POST"])
@login_required
@admin_required
def admin_task_upload_user():

    # must be admin
    '''
    if g.user.uid != 0:
        abort(403)
    '''

    form = UserUploadForm()

    if form.validate_on_submit():

        filename = secure_filename(form.csv.data.filename)
        replace = form.replace.data

        csv_filename = os.path.join('uploads', filename)
        form.csv.data.save(csv_filename)
        result = import_user(filename=csv_filename, replace=replace)

        if result:
            flash(_('User has been uploaded!'))
            logging(user_id=g.user.uid, message="Upload user. (filename={}, replace={})".format(
                filename, replace), ip=request.remote_addr)
        else:
            flash(_('ERROR: Failed to upload!'))
            logging(user_id=g.user.uid, message="Failed to upload user. (filename={}, replace={})".format(
                filename, replace), ip=request.remote_addr)
    else:
        filename = None

    return render_template("admin_task_upload_user.html", form=form, filename=filename)


@app.route("/admin/task/history/list", methods=["GET"])
@login_required
@admin_required
def admin_task_history_list():

    # must be admin
    '''
    if g.user.uid != 0:
        abort(403)
    '''

    history = History.query.order_by(History.hid.desc()).all()

    return render_template("admin_task_history_list.html", history=history)


@app.route("/admin/task/payment", methods=["GET"])
@app.route("/admin/task/payment/<int:uid>", methods=["GET"])
@app.route("/admin/task/payment/<int:student_grade>/<int:student_class>/<int:student_number>", methods=["GET"])
@login_required
@admin_required
def admin_task_payment(uid=None, student_grade=None, student_class=None, student_number=None):

    # must be admin
    '''
    if g.user.uid != 0:
        abort(403)
    '''

    payments = []

    uids = []
    if uid is None:
        if (student_grade is not None) and (student_class is not None) and (student_number is not None):
            u = User.query.filter_by(student_grade=student_grade).filter_by(
                student_class=student_class).filter_by(student_number=student_number).first()
            if u:
                uids = Selection.query.group_by(
                    Selection.user_id).filter_by(user_id=u.uid).all()
            else:
                abort(404)
        else:
            uids = Selection.query.group_by(
                Selection.user_id).order_by(Selection.user_id).all()
    else:
        uids = Selection.query.group_by(
            Selection.user_id).filter_by(user_id=uid).all()

    for uid in uids:
        payment = dict()
        selections = Selection.query.filter(
            Selection.user_id == uid.user_id).order_by(Selection.course_id).all()

        weeks = {}
        ranks = {}
        counts = {}
        for i in xrange(1, 8):
            weeks[i] = []

        sels = []
        for s in selections:
            ranks[s.course_id] = Selection.query.filter(Selection.course_id == s.course_id).filter(
                Selection.sid <= s.sid).count()
            counts[s.course_id] = Selection.query.filter(
                Selection.course_id == s.course_id).count()

            # lowbound <= counts, ranks <= upbound
            if counts[s.course_id] >= s.course.lowbound and ranks[s.course_id] <= s.course.upbound:
                sels.append(s)
                # may contain multiple datetimes
                for dt in s.course.datetime.split(","):
                    weeks[int(dt[0])].append(dt)

        for i in xrange(1, 8):
            weeks[i].sort()

        payment['user'] = uid.user
        payment['selections'] = sels
        payment['ranks'] = ranks
        payment['weeks'] = weeks
        payment['counts'] = counts

        # not empty selections
        if payment['selections']:
            payments.append(payment)

    return render_template("admin_task_payment.html", payments=payments)


@app.route("/admin/task/user/change/<int:student_grade>/<int:student_class>/<int:student_number>", methods=["GET"])
@login_required
@admin_required
def admin_task_user_change(student_grade, student_class, student_number):
    user = User.query.filter(User.student_grade == student_grade).filter(
        User.student_class == student_class).filter(User.student_number == student_number).first()

    if user:
        logging(user_id=g.user.uid, message=u"Change user. (uid={}, student_name={})".format(
            user.uid, user.student_name), ip=request.remote_addr)
        login_user(user)
        return redirect(url_for("user"))
    else:
        abort(404)
