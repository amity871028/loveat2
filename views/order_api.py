import json
from datetime import datetime

from firebase_admin import messaging

from flask import Blueprint, jsonify, request, url_for

from flask_login import current_user, login_required


from lib import push
from lib.auth import admin_required

from models import order, user


order_api = Blueprint("order_api", __name__)
push.init()


@order_api.route("/history", methods=["GET"])
@admin_required
def history():
    args = request.args
    start = datetime.strptime(args.get("start"), "%Y-%m-%dT%H:%M")
    end = datetime.strptime(args.get("end"), "%Y-%m-%dT%H:%M")
    return jsonify(list(order.get_raw_history(start, end)))


@order_api.route("/analysis-data", methods=["GET"])
@admin_required
def analysis_data():
    args = request.args
    start = datetime.strptime(args.get("start"), "%Y-%m-%dT%H:%M")
    end = datetime.strptime(args.get("end"), "%Y-%m-%dT%H:%M")
    return jsonify(order.get_analysis_data(start, end))


@order_api.route("/new", methods=["POST"])
@login_required
def add_order():
    data = request.get_json()
    data["userName"] = current_user.name
    try:
        cur_order = order.add_order(data)
        if cur_order:
            push.send_to_topic(
                {
                    "title": "新訂單",
                    "content": "您有新訂單",
                    "url": url_for("order_web.pending", _externale=True),
                    "detail": json.dumps(cur_order),
                    "type": "admin-order-new",
                },
                push.TOPIC_ADMIN,
            )
            return "", 200
        else:
            return "", 422
    except KeyError:
        return "", 422


@order_api.route("/update", methods=["POST"])
@admin_required
def update_order_state():
    data = request.get_json()
    result = order.update_state(data)
    message = {
        "doing": {"title": "訂單已接受", "content": "老闆已接受您的訂單"},
        "cancel": {"title": "訂單被拒絕", "content": "抱歉，老闆拒絕了您的訂單"},
        "finish": {"title": "訂單已完成", "content": "餐點已製作完成，請儘速來取餐"},
    }
    if result:
        try:
            token = user.get_token_by_username(result["userName"])["token"]
            # push to customer
            if data["state"] in message:
                message[data["state"]].update(
                    {
                        "url": url_for("order_web.state", _external=True),
                        "detail": json.dumps(result),
                    }
                )
                push.send_to_customer(token, message[data["state"]])
        except (ValueError, messaging.UnregisteredError):
            pass
        finally:
            # push to admin
            if data["state"] == "doing":
                push.send_to_topic(
                    {
                        "type": "admin-order-update",
                        "detail": json.dumps(
                            list(order.get_todo_order(id=result["_id"]))[0]
                        ),
                    },
                    push.TOPIC_ADMIN,
                )
            return "", 200
    else:
        return "", 404


@order_api.route("/todo", methods=["GET"])
@admin_required
def todo():
    return jsonify(list(order.get_todo_order()))
