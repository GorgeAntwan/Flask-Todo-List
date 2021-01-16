from flask import Flask, render_template, request, redirect, url_for, abort
import sys
from flask.json import jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://Gorge@localhost:5432/todoapp"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


order_items = db.Table(
    "order_items",
    db.Column("order_id", db.Integer, db.ForeignKey("order.id"), primary_key=True),
    db.Column("product_id", db.Integer, db.ForeignKey("product.id"), primary_key=True),
)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(), nullable=False)
    products = db.relationship(
        "Product", secondary=order_items, backref=db.backref("orders", lazy=True)
    )


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)


class Todo(db.Model):
    __tablename__ = "todos"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    list_id = db.Column(db.Integer, db.ForeignKey("todolists.id"), nullable=True)

    def __repr__(self):
        return f"<Todo {self.id} {self.description}, list {self.list_id}>"


class TodoList(db.Model):
    __tablename__ = "todolists"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    todos = db.relationship("Todo", backref="list", lazy=True)

    def __repr__(self):
        return f"<Todo {self.id} {self.name}>"


db.create_all()


@app.route("/todos/create", methods=["POST"])
def create_todo():
    error = False
    body = {}
    try:

        description = request.get_json()["description"]
        list_id = request.get_json()["list_id"]
        todo = Todo(description=description, completed=False, list_id=list_id)
        db.session.add(todo)
        db.session.commit()
        body["description"] = todo.description
        body["completed"] = todo.completed
        body["list_id"] = todo.list_id

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(400)
    else:
        return jsonify(body)


@app.route("/todos/<todo_id>/set-completed", methods=["POST"])
def set_completed_todo(todo_id):
    try:
        completed = request.get_json()["completed"]
        print("completed", completed)
        todo = Todo.query.get(todo_id)
        todo.completed = completed
        db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    return redirect(url_for("index"))


@app.route("/lists/<list_id>")
def get_list_todos(list_id):
    lists = TodoList.query.all()
    active_list = TodoList.query.get(list_id)
    todos = Todo.query.filter_by(list_id=list_id).order_by("id").all()
    return render_template(
        "index.html", lists=lists, active_list=active_list, todos=todos
    )

@app.route("/api/list")
def get_list():
    body = {}
    alll =[]
    lists = TodoList.query.all()
    for list in lists:
         print(list)
         body['id']=list.id
         body['name'] =list.name
         alll.append(body)
         body={}
        
    print(alll)
    return jsonify(alll)

@app.route("/api/todo/<id>")
def get_list_api(id):
    body = {}
     
    todo = Todo.query.get(id)
    print(todo)
    if todo:
        print(todo)
        body['id']=todo.id
        body['description']=todo.description
        body['completed']=todo.completed
        print(body)
        return jsonify(body)
    else :
        return '[]'

@app.route("/lists/create", methods=["POST"])
def create_list():
    body = {}
    error = False
    try:
        name = request.get_json()["name"]
        todo_list = TodoList(name=name)
        db.session.add(todo_list)
        db.session.commit()
        body["id"] = todo_list.id
        body["name"] = todo_list.name
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info)
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return jsonify(body)


@app.route("/lists/<list_id>/delete", methods=["DELETE"])
def delete_list(list_id):
    error = False
    try:
        list = TodoList.query.get(list_id)
        for todo in list.todos:
            db.session.delete(todo)
        db.session.delete(list)
        db.session.commit()

    except ():
        db.session.rollback()
        error = True

    finally:
        db.session.close()
        if error:
            abort(500)
        else:
            return jsonify({"success": True})


@app.route("/todos/<todo_id>/delete", methods=["DELETE"])
def delete_todo(todo_id):
    error = False
    try:
        # Todo.query.filter_by(id=todo_id).delete()
        todo = Todo.query.get(todo_id)
        db.session.delete(todo)
        db.session.commit()
    except ():
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return jsonify({"success": True})


@app.route("/")
def index():
    return redirect(url_for("get_list_todos", list_id=1))


@app.route("/lists/<list_id>/set-completed", methods=["POST"])
def set_completed_list(list_id):
    error = False
    try:
        list = TodoList.query.get(list_id)
        for todo in list.todos:
            todo.completed = True
        db.session.commit()
    except:
        db.session.rollback()

        error = True
    finally:
        db.session.close()

        if error:
            abort(500)
        else:
            return "", 200


if __name__ == "__main__":
    app.run(debug=True)
