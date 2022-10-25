from flask import Blueprint, render_template, request, json, flash, url_for, redirect
from .utils.check_token import CHECK_TOKEN
from .utils.env_var import jwt_secret_key
from dotenv import load_dotenv
from .utils.env_var import database_pwd
import bcrypt
import jwt
import pymysql

load_dotenv('../env')

bp = Blueprint('flask_user', __name__, url_prefix='/')

@bp.route('/user', methods=['GET','POST'])
@CHECK_TOKEN.check_for_token
def user() :
    user_token = request.cookies.get('access_token')
    decode_user_token_email = jwt.decode(user_token, jwt_secret_key, algorithms='HS256')['user_email']

    # connect mysql database
    register_db = pymysql.connect(
        host=   "localhost",
        user=   "root", 
        passwd= database_pwd, 
        db=     "register_db", 
        charset="utf8"
    )
    cursor = register_db.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT name FROM users WHERE email=%s", decode_user_token_email)
    user_name = cursor.fetchone()['name']
    cursor.execute("SELECT profile FROM users WHERE email=%s", decode_user_token_email)
    user_profile = cursor.fetchone()['profile']
    cursor.execute("SELECT created_at FROM users WHERE email=%s", decode_user_token_email)
    user_created_at = cursor.fetchone()['created_at']

    user_data = {'user_name' : user_name, 'user_profile' : user_profile, 'user_created_at' : user_created_at}

    if request.method == 'POST' and 'password' in request.form or 'change_password' in request.form :
        if request.method == 'POST' and 'password' in request.form :
            password = str(request.form['password'])

            cursor.execute("SELECT password FROM users WHERE email=%s", decode_user_token_email)
            match_pwd = cursor.fetchone()
            check_password = bcrypt.checkpw(password.encode('utf-8'), match_pwd['password'])
            if(check_password == True) :
                register_db.close()
                return render_template('user.html', pwd_check = True, user_data = user_data)
            else :
                flash('Unmatch password!')
                return redirect(url_for('flask_user.user'))

        if request.method == 'POST' and 'change_password' in request.form :
            change_password = str(request.form['change_password'])

            cursor.execute("SELECT password FROM users WHERE email=%s", decode_user_token_email)
            match_pwd = cursor.fetchone()
            check_password = bcrypt.checkpw(change_password.encode('utf-8'), match_pwd['password'])
            if(check_password == True) :
                flash('Already using password!')
                return redirect(url_for('flask_user.user'))
            else :
                endcode_change_password = (bcrypt.hashpw(change_password.encode('UTF-8'), bcrypt.gensalt())).decode('utf-8')
                cursor.execute("UPDATE users SET password=%s WHERE email=%s", (endcode_change_password, decode_user_token_email))
                register_db.commit()
                register_db.close()

                flash('Password Change Completed!')
                return redirect(url_for('flask_user.user'))
    else :
        return render_template('user.html', user_data = user_data)
