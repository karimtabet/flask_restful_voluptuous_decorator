import json
import functools
from voluptuous import Schema, Required, MultipleInvalid
from logging import getLogger

from flask import Flask, request
from flask.ext import restful
from flask.ext.restful import abort
from flask.ext.testing import TestCase

app = Flask(__name__)
api = restful.Api(app)

logger = getLogger(__name__)


def validate(schema):
    def decorator(view):
        @functools.wraps(view)
        def inner(*args, **kwargs):
            try:
                schema(request.get_json())
            except MultipleInvalid as e:
                logger.warn(
                    'validation error (UA: {user_agent}): {message}'
                    .format(
                        message=e,
                        user_agent=request.headers.get(
                            'User-Agent', 'not set')
                    )
                )
                return abort(400, message=str(e))
            return view(*args, **kwargs)
        return inner
    return decorator


register_schema = Schema({
    Required('email'): str,
    Required('password'): str
})


class Register(restful.Resource):
    @validate(register_schema)
    def post(self):
        return {}

api.add_resource(Register, '/register')


class TestRegister(TestCase):
    json_headers = {'Content-Type': 'application/json'}

    def create_app(self):
        return app

    def test_valid_body(self):
        response = self.client.post(
            api.url_for(Register),
            data=json.dumps({
                'email': 'test@test.com',
                'password': 'xyz'
            }),
            headers=self.json_headers
        )
        self.assert200(response)

    def test_no_password_in_body(self):
        response = self.client.post(
            api.url_for(Register),
            data=json.dumps({
                'email': 'test@test.com'
            }),
            headers=self.json_headers
        )
        self.assert400(response)

    def test_no_email_in_body(self):
        response = self.client.post(
            api.url_for(Register),
            data=json.dumps({
                'password': 'xyz'
            }),
            headers=self.json_headers
        )
        self.assert400(response)

    def test_extra_keys_in_body(self):
        response = self.client.post(
            api.url_for(Register),
            data=json.dumps({
                'email': 'test@test.com',
                'extra': 'extra',
                'password': 'xyz'
            }),
            headers=self.json_headers
        )
        self.assert400(response)

    def test_invalid_body(self):
        response = self.client.post(
            api.url_for(Register),
            data=json.dumps({
                'something': 'test@test.com',
                'or_other': 'xyz'
            }),
            headers=self.json_headers
        )
        self.assert400(response)
