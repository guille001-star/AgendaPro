from flask import Blueprint, redirect, url_for

public = Blueprint('public', __name__)

@public.route('/')
def home():
    return redirect(url_for('auth.login'))
