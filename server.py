from flask import (Flask, Response, request, render_template, make_response,
                   redirect)
from flask_restful import Api, Resource, reqparse, abort

import json
import random
import string
from datetime import datetime
from functools import wraps


with open('data.jsonld') as data:
    data = json.load(data)

def generate_id(size=6, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def error_if_review_not_found(review_id):
    if review_id not in data['reviews']:
        message = "No help ticket with ID: {}".format(review_id)
        abort(404, message=message)

def filter_and_sort_review_list(query='', sort_by='time'):
    # Returns True if the query string appears in the help ticket's
    # title or description.
    def matches_query(item):
        (review_id, review) = item
        text = review['title'] + review['author']
        return query.lower() in text

    # Returns the help ticket's value for the sort property (which by
    # default is the "time" property).
    def get_sort_value(item):
        (helpticket_id, helpticket) = item
        return helpticket[sort_by]

    filtered_helptickets = filter(matches_query, data['helptickets'].items())

    return sorted(filtered_helptickets, key=get_sort_value, reverse=True)

def nonempty_string(x):
    s = str(x)
    if len(x) == 0:
        raise ValueError('string is empty')
    return s


new_review_parser = reqparse.RequestParser()
for arg in ['name', 'review', 'author']:
    new_review_parser.add_argument(
        arg, type=nonempty_string, required=True,
        help="'{}' is a required value".format(arg))



query_parser = reqparse.RequestParser()
query_parser.add_argument(
    'query', type=str, default='')
query_parser.add_argument(
    'sort_by', type=str, choices=('priority', 'time'), default='time')


def render_review_list_as_html(reviews):
    return render_template(
        'helpticket+microdata+rdfa.html',
        reviews=reviews)

def render_review_as_html(review):
    return render_template(
        'review',
        review = review)



class ReviewList(Resource):

    def get(self):
        query = query_parser.parse_args()
        return make_response(
            render_review_list_as_html(
                filter_and_sort_review_list(**query)), 200)

    def post(self):
        review = new_review_parser.parse_args()
        review_id = generate_id()
        review['@id'] = 'request/' + review_id
        data['reviews'][review_id] = review
        return make_response(
            render_review_list_as_html(
                filter_and_sort_review_list()), 201)

class Review(Resource):

    def get(self,review_id):
        error_if_review_not_found(review_id)
        return make_response(
            render_review_as_html(
                data['reviews'][review_id],200))


app = Flask(__name__)
api = Api(app)
api.add_resource(ReviewList, '/reviews')
api.add_resource(Review, '/reviews/<string:review_id>')


@app.route('/')
def index():
    return redirect(api.url_for(ReviewList), code=303)

@app.after_request
def after_request(response):
    response.headers.add(
        'Access-Control-Allow-Origin', '*')
    response.headers.add(
        'Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add(
        'Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5555,
        debug=True,
        use_debugger=False,
        use_reloader=False)
