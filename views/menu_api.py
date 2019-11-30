from flask import Blueprint, jsonify, request

from lib.auth import admin_required

from models import menu


menu_api = Blueprint("menu_api", __name__)


@menu_api.route("/", methods=["GET"])
def get_menu():
    return jsonify(menu.get_all())


@menu_api.route("/item", methods=["POST"])
def get_item():
    data = request.get_json()
    return jsonify(menu.get_item_by_id(data))


@menu_api.route("/item/delete", methods=["POST"])
@admin_required
def delete_item():
    id = request.get_json()["id"]
    menu.delete_item(id)
    return "", 200


@menu_api.route("/combo", methods=["POST"])
def get_combo():
    data = request.get_json()
    return jsonify(menu.get_combo_by_id(data))


@menu_api.route("/combo/delete", methods=["POST"])
@admin_required
def delete_combo():
    id = request.get_json()["id"]
    menu.delete_combo(id)
    return "", 200
