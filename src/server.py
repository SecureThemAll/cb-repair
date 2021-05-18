#!/usr/bin/env python3

from flask import Flask, render_template_string
from flask_restful import Api, Resource, reqparse, abort
from flask_sqlalchemy import SQLAlchemy

from config import configuration
from core.kernel import Kernel

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
db = SQLAlchemy(app)
db.create_all()

api = Api(app)
kernel = Kernel(configs=configuration, name='kernel')

req_parser = reqparse.RequestParser()


def abort_if_challenge_doesnt_exist(name: str):
    if not kernel.has_challenge(challenge_name=name, fail=False):
        abort(404, message=f"No challenge with the name {name}")


class ChallengeInfo(Resource):
    def get(self, name: str):
        abort_if_challenge_doesnt_exist(name)
        challenge = kernel.get_challenge(challenge_name=name)
        return challenge.info(), 200


class CBRepairModel(db.Model):
    id = db.column(db.Integer, primary_key=True)
    name = db.column(db.String(100), nullable=False)


class CBRepair(Resource):
    def get(self):
        return kernel.challenges, 200


class Index(Resource):
    def get(self):
        return render_template_string("""<form action='http://127.0.0.1:5000/benchmark'><input type='submit' value='Benchmark'/></form>"""), 200


api.add_resource(ChallengeInfo, '/challenge/<string:name>')
api.add_resource(CBRepair, '/benchmark')
api.add_resource(Index, '/')

if __name__ == '__main__':
    app.run(debug=True)
