from flask import render_template, url_for, request, redirect, flash, Blueprint
from secrets_app.notes.forms import AddNoteForm
from secrets_app import db
from secrets_app.model import User, Note, Receiver
from flask_login import current_user, login_required


notes_bp = Blueprint("notes", __name__)

@notes_bp.route("/notes", methods=["GET", "POST"])
@login_required
def notes():
    if not current_user.is_authenticated:
        return redirect(url_for('accounts.login'))
    
    userId = current_user.get_id()
    user = User.query.get(int(userId))
    form = AddNoteForm()

    notes_data = []
    
    if request.method == "POST":
        if form.validate_on_submit():
            for receiver in form.receivers:
                print(receiver)
            print("hello")
            note_title = form.title.data
            note_content = form.content.data
            to_self = form.to_self.data
            date = form.date.data
            receivers = []
            print("Form data:", form.data)
            for receiver in form.receivers.data:
                receiver_obj = Receiver(name=receiver["name"], email_id=receiver["email_id"])
                receivers.append(receiver_obj)

            note = Note(title=note_title, content=note_content, to_self=to_self, send_date=date, receivers=receivers, user_id=int(userId))
            db.session.add(note)
            db.session.commit()
            flash("New Note Added", "success")
            return redirect(url_for('notes.notes'))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Error in {field}: {error}', "danger")
            return redirect(url_for('notes.notes'))
    
    # Fetch user's notes
    print("Fetching notes for user:", userId)
    notes = Note.query.filter_by(user_id=int(userId)).all()
    notes_dict = [note.to_dict() for note in notes]
    
    return render_template('notes.html', notes=notes_dict, form=form, title="Notes List")


@notes_bp.route("/edit_note/<int:noteId>", methods=["GET", "POST"])
@login_required
def edit_note(noteId):
    if not current_user.is_authenticated:
        return redirect(url_for('accounts.login'))
    
    userId = current_user.get_id()
    user = User.query.get(int(userId))
    note = Note.query.get_or_404(noteId)
    if note.user_id != user.id:
        flash("You do not have permission to edit this secret", "danger")
        return redirect(url_for('notes.notes'))
    form = AddNoteForm()
    if form.validate_on_submit():
        print("hello")
        note.title = form.title.data
        note.content = form.content.data
        note.to_self = form.to_self.data
        note.send_date = form.date.data
        for i in note.receivers:
            db.session.delete(i)

        for receiver_form in form.receivers.data:
            new_receiver = Receiver(
                name=receiver_form["name"],
                email_id=receiver_form["email_id"]
            )
            db.session.add(new_receiver)
            note.receivers.append(new_receiver)
        print("\n\n\n\n\n")

        db.session.add(note)
        db.session.commit()
        flash("Note updated successfully", "success")
        return redirect(url_for("notes.notes"))
    if request.method == "GET":
        form.title.data = note.title
        form.content.data = note.content
        form.to_self.data = note.to_self
        form.date.data = note.send_date

        for receiver in note.receivers:
            form.receivers.append_entry({
                'name': receiver.name,
                'email_id': receiver.email_id
            })
        
    print("Form data:", form.data)
    return render_template('edit_note.html', form=form, note=note, title="Edit Note")




@notes_bp.route("/delete_note/<int:noteId>")
@login_required
def delete_note(noteId):
    if not current_user.is_authenticated:
        return redirect(url_for('accounts.login'))

    userId = current_user.get_id()
    user = User.query.get(int(userId))

    note = Note.query.get_or_404(noteId)
    if note.user_id == user.id:
        db.session.delete(note)
        db.session.commit()
        flash(f"Deleted the note {note.title}", "success")
        return redirect(url_for('notes.notes'))
    flash("Invalid note selected", "danger")
    return redirect(url_for('notes.notes'))
