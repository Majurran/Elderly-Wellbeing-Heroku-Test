from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, current_app
from flask_login import login_required, current_user
from .models import InputOptions, Input, NursingHome,User
from . import db
from sqlalchemy import func
from werkzeug.utils import secure_filename
import json, os, uuid
import plotly
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime
views = Blueprint('views', __name__)

# Hyper ref for base.html
ADMIN_HOME_HREF = "/admin"
USER_HOME_HREF = "/user"
GUEST_HOME_HREF = "/user/inputs"


ROOMS = ["lounge", "news", "games", "coding"]

# ===============================================================================================================
# ==================================================== CHAT ====================================================
# ===============================================================================================================
from flask import session, redirect, render_template, request
#from .forms import LoginForm
from flask_socketio import SocketIO, join_room, leave_room, send
import os
import time
from . import socketio
# Handles the chating feature with other people in our nursing home which our app offers
# and returns those feature to the corresponding html page
@views.route("/chat", methods=['GET', 'POST'])
@login_required
def chat():


    #        <title>Chat Away - RChat</title>
    chat_rooms = ["lounge"] + list(set([element.name for element in Input.query.filter_by(category="activity").distinct(Input.name)]))
    if current_user.first_name is None:
        name = "Guest User"
    else:
        name = current_user.first_name
    print(type(current_user.first_name))
    return render_template("chat.html", user= current_user, username=name, rooms=chat_rooms)


# Error handling for our chatbox
@views.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404

# Allows sending messages between users 
@socketio.on('incoming-msg')
def on_message(data):
    """Broadcast messages"""

    msg = data["msg"]
    username = data["username"]
    room = data["room"]
    # Set timestamp
    time_stamp = time.strftime('%b-%d %I:%M%p', time.localtime())
    send({"username": username, "msg": msg, "time_stamp": time_stamp}, room=room)
   
@socketio.on('join')
def on_join(data):
    """User joins a room"""

    username = data["username"]
    room = data["room"]
    join_room(room)

    # Broadcast that new user has joined
    send({"msg": username + " has joined the " + room + " room."}, room=room)


@socketio.on('leave')
def on_leave(data):
    """User leaves a room"""

    username = data['username']
    room = data['room']
    leave_room(room)
    send({"msg": username + " has left the room"}, room=room)





# Returns Nursing Home name or Guest or User Name for base.html -> "Welcome back, <name>"
def get_name(user):
    if user == "admin" or user == "guest":
        row = NursingHome.query.filter_by(id=current_user.nursing_home_id).first()
        return row.name
    elif user == "resident":
        return current_user.first_name
    else:
        return ""

# ===============================================================================================================
# ==================================================== ADMIN ====================================================
# ===============================================================================================================
@views.route('/', methods=['GET'])
@views.route('/index', methods=['GET'])
def index():
    return redirect(url_for('auth.login'))


@views.route('/admin', methods=['GET'])
@login_required
def admin_home():
    return render_template("admin/home.html", user=current_user, name=get_name("admin"), home_href=ADMIN_HOME_HREF)


# Handles the features (various plots, number of residents and nursing) for the private dashboard features  
# and return them to its corresponding html page
@views.route('/admin/outputs', methods=['GET'])
@login_required
def admin_dashboard_page():
    # Nursing home data
    
    activity=[]
    activity_frequency = []
    activity_count_pairs = Input.query.filter_by(category="activity").with_entities(Input.name, func.count(Input.name)).group_by(Input.name).all()
    for actvity_count_pair in activity_count_pairs:
        activity.append(actvity_count_pair[0])
        activity_frequency.append(actvity_count_pair[1])

    activities_bar_chart = go.Figure(data=[go.Bar(x=activity, y=activity_frequency)])
    activities_bar_chart.update_layout(
                width=630,
                height=470,
                margin=go.layout.Margin(
                    l=1, #left margin
                    r=1, #right margin
                    b=1, #bottom margin
                    t=1  #top margin
                )
    )
    graphJSON_activities = json.dumps(activities_bar_chart, cls=plotly.utils.PlotlyJSONEncoder)

    num_elderly = 4
    emoji_name = "Happy"
    activity_name = "Drinking"
    percentage_happiness = 80

    moods = ['happy', 'sad', 'ok']
    percentage = [35, 15, 50]
    mood_pie_chart = go.Figure(data = [go.Pie(labels = moods, values = percentage)])
    mood_pie_chart.update_layout(
                width=375,
                height=470,
                title = "Overall Happy vs Sad Proportion"
    )
    mood_ratio = json.dumps(mood_pie_chart, cls=plotly.utils.PlotlyJSONEncoder)

    detailed_mood = ['happy', 'sad', 'ok']
    detailed_percentage = [35, 15, 50]
    detailed_mood_pie_chart = go.Figure(data = [go.Pie(labels = detailed_mood, values = detailed_percentage)])
    detailed_mood_pie_chart.update_layout(
                width=375,
                height=470,
                title = "Detailed Emotion Proportions"
    )
    detailed_mood_ratio = json.dumps(detailed_mood_pie_chart, cls=plotly.utils.PlotlyJSONEncoder)


    num_residents = len(User.query.all())
    num_nursing_home = len(NursingHome.query.all())


    return render_template("admin/new_outputs.html", user=current_user, graphJSON_mood=mood_ratio, graphJSON_mood_detail = detailed_mood_ratio,
    graphJSON_activities=graphJSON_activities,num_elderly=num_elderly, emoji_name = emoji_name, activity_name=activity_name, percentage_happiness=percentage_happiness, 
        name=get_name("admin"), home_href=ADMIN_HOME_HREF,  num_residents=num_residents, num_nursing_home=num_nursing_home,
        reload_time = datetime.now().strftime("%H:%M"))



@views.route('/admin/instructions', methods=['GET'])
@login_required
def admin_instruction():
    return render_template("admin/instruction.html", user=current_user, name=get_name("admin"), home_href=ADMIN_HOME_HREF)


@views.route('/admin/profile', methods=['GET'])
@login_required
def admin_profile():
    # return render_template("profile.html", user=current_user)
    return render_template("admin/profile_update.html", user=current_user, name=get_name("admin"), home_href=ADMIN_HOME_HREF)


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@views.route('/admin/edit-input-options', methods=['GET', 'POST'])
@login_required
def admin_edit_input_options():
    input_options_rows = InputOptions.query.filter_by(nursing_home_id=current_user.nursing_home_id).all()
    
    if request.method == 'POST':
        edit_type = request.form.get('edit-type')   # add, remove, reset
        # print(edit_type)
        
        # Plus Sign Option, adding new input options
        if edit_type == "add":
            # Empty strings returned if no options are selected
            icon_name = request.form.get('iconName')
            category_type = request.form.get('category_type_add')
            
            # check if the post request has the file part
            if 'image-icon' not in request.files:
                flash('No Image File Selected')
                return redirect(request.url)
            
            image = request.files['image-icon']
            
            # If the user does not select a file, the browser submits an empty file without a filename.
            if image.filename == '':
                flash('No selected file')
                return redirect(request.url)
            
            # If everything is successful add new input option to database
            if image and allowed_file(image.filename):
                random_characters = str(uuid.uuid1()) + "-" + str(uuid.uuid4()) + "." + str(image.filename.rsplit('.', 1)[1].lower())
                
                filename = secure_filename(random_characters)
                image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                
                # Add new Input Option to database
                db_file_path = "/static/input_option_img/" + filename
                new_input_option = InputOptions(category=category_type, name=icon_name, file_path=db_file_path, nursing_home_id=current_user.nursing_home_id)
                db.session.add(new_input_option)
                db.session.commit()
            else:
                flash("File extension not allowed, please use the following image format: png, jpg, jpeg, gif")
            return redirect(request.url)
                
        # Minus Sign Option, remove selected input options
        elif edit_type == 'remove':
            # activity or wellbeing, to make sure to only delete options from those categories in case someone manually changes the option-id number in inspect mode
            category_type = request.form.get('category_type_remove') 
            
            # Gets the highlighted options (using their ID) to delete from the database
            selected_input_options_id = request.form.get('remove_selected_input_options_id')            # E.g option-23,option-24,option-25,
            input_option_id_set = set(selected_input_options_id.replace("option-","").split(",")[:-1])  # E.g {'23', '24', '25'}

            # Filter the input_option_id_set to keep only valid input option ID based on nursing_home_id, and category
            existing_input_options_rows = InputOptions.query.filter_by(nursing_home_id=current_user.nursing_home_id, category=category_type).all()
            existing_input_options_id_set = {str(row.id) for row in existing_input_options_rows}
            valid_selected_input_options_id_set = input_option_id_set.intersection(existing_input_options_id_set) # Filter and keep valid input option ID
            
            # print("Category_type:", category_type)
            # print("Selected Input Options:", selected_input_options_id)
            # print("Input Set ID:", input_option_id_set)
            # print("Exist Set ID:", existing_input_options_id_set)
            # print("Valid Set ID:", valid_selected_input_options_id_set)
            
            for num_id in valid_selected_input_options_id_set:
                row = InputOptions.query.get(int(num_id))
                db.session.delete(row)
                db.session.commit()
            return redirect(request.url)
        
        # Reset Button, remove all the input options based on the category type and add the default ones back in like 
        #   we did in the sign_up_nursing_home() function in auth.py
        elif edit_type == 'reset':
            # print(edit_type)
            category_type = request.form.get('category_type_reset') 
            # print(category_type)
            
            # Delete existing rows 
            existing_input_options_rows = InputOptions.query.filter_by(nursing_home_id=current_user.nursing_home_id, category=category_type).all()
            for row in existing_input_options_rows:
                db.session.delete(row)
                db.session.commit()
                
            if category_type == "activity":
                
                # Add back the default input options
                # Default activity and wellbeing list from prototype design
                activity_list = ['Walking', 'Cycling', 'Reading', 'Play an Instrument', 'Sports', 'Gardening', 'Cooking', 'Puzzles', 'Socializing']
                
                activity_list_file_path = [
                    "/static/img/person_walking.png",
                    "/static/img/Go Cycling.png",
                    "/static/img/books_reading.png",
                    "/static/img/Play the Piano.png",
                    "/static/img/golf.png",
                    "/static/img/potted_plant.png",
                    "/static/img/cooking.png",
                    "/static/img/puzzle_piece.png",
                    "/static/img/talking.png"
                ]
                
                for i,activity in enumerate(activity_list):
                    new_activity = InputOptions(category="activity", name=activity, file_path=activity_list_file_path[i], nursing_home_id=current_user.nursing_home_id)
                    db.session.add(new_activity)
                    db.session.commit()
            
            elif category_type == "wellbeing":    
                wellbeing_list = ['Relaxed', 'At Ease', 'Cheerful', 'Enthusiastic', 'Tense', 'Frustrated', 'Down', 'Tired']
                wellbeing_list_file_path = [
                    "/static/img/relaxed.png",
                    "/static/img/at_ease.png",
                    "/static/img/cheerful.png",
                    "/static/img/Happy.png",
                    "/static/img/tense.png",
                    "/static/img/frustrated.png",
                    "/static/img/down.png",
                    "/static/img/tired.png"
                ]
                
                for i,wellbeing in enumerate(wellbeing_list):
                    new_wellbeing = InputOptions(category="wellbeing", name=wellbeing, file_path=wellbeing_list_file_path[i], nursing_home_id=current_user.nursing_home_id)
                    db.session.add(new_wellbeing)
                    db.session.commit()
                    
            return redirect(request.url)
            
    return render_template("admin/edit_input_ver2.html", user=current_user, name=get_name("admin"), rows=input_options_rows, home_href=ADMIN_HOME_HREF)

# ===============================================================================================================
# =============================================== Public Dashboard ==============================================
# ===============================================================================================================
# Handles the features (various plots, number of residents and nursing home) for the public dashboard features  
# and return them to its corresponding html page
@views.route('/public-dashboard', methods=['GET'])
def public_dashboard_page():

    # Bar Chart For Activities
    activity=[]
    activity_frequency = []
    activity_count_pairs = Input.query.filter_by(category="activity").with_entities(Input.name, func.count(Input.name)).group_by(Input.name).all()
    for actvity_count_pair in activity_count_pairs:
        activity.append(actvity_count_pair[0])
        activity_frequency.append(actvity_count_pair[1])

    activities_bar_chart = go.Figure(data=[go.Bar(x=activity, y=activity_frequency)])
    activities_bar_chart.update_layout(
                width=640,
                height=470,
                margin=go.layout.Margin(
                    l=1, #left margin
                    r=1, #right margin
                    b=1, #bottom margin
                    t=1  #top margin
                )
    )

    graph_activities = json.dumps(activities_bar_chart, cls=plotly.utils.PlotlyJSONEncoder)

    # Mood Plots
    moods = ['happy', 'sad', 'ok']
    percentage = [35, 15, 50]
    mood_pie_chart = go.Figure(data = [go.Pie(labels = moods, values = percentage)])
    mood_pie_chart.update_layout(
                width=319,
                height=425,
                title = "Overall Happy vs Sad Proportion"
    )
    mood_ratio = json.dumps(mood_pie_chart, cls=plotly.utils.PlotlyJSONEncoder)

    detailed_mood = ['happy', 'sad', 'ok']
    detailed_percentage = [35, 15, 50]
    detailed_mood_pie_chart = go.Figure(data = [go.Pie(labels = detailed_mood, values = detailed_percentage)])
    detailed_mood_pie_chart.update_layout(
                width=319,
                height=425,
                title = "Detailed Emotion Proportions"
    )
    detailed_mood_ratio = json.dumps(detailed_mood_pie_chart, cls=plotly.utils.PlotlyJSONEncoder)


    # Pie Chart for Proportion of responses from each state
    states = ['NSW', 'QLD', 'WA', 'SA', 'VIC', "Tas"]

    states_percentages = []
    # States from which there atleast 1 response
    valid_states = []
    # Get the response percentages for each state
    for state in states:
        users_by_state = User.query.filter_by(state=state).all()
        print(users_by_state)
        states_percentages.append(len(users_by_state))
        if len(users_by_state) != 0:
            valid_states.append(state)

    total_population = sum(states_percentages)
    if total_population != 0:
        for index, count in enumerate(states_percentages):
            states_percentages[index] = count/total_population * 100   

    
    state_pie = go.Figure(data = [go.Pie(labels = valid_states, values = states_percentages)])
    state_pie.update_layout(
                width=400,
                height=400,
    )
    state_pie_chart = json.dumps(state_pie, cls=plotly.utils.PlotlyJSONEncoder)

    # Monthly Overall Rating of Walking Difficulty
    print("The Mobility Proportion is")
    mobility_proportion = Input.query.filter_by(category="difficulty_walking").with_entities(Input.name,Input.date).all()
    #print(mobility_proportion)
    mobility_values = {}
    for mobility_input in mobility_proportion:
        if mobility_values.get((mobility_input[1].month,mobility_input[1].year)) is None:
            mobility_values[(mobility_input[1].month,mobility_input[1].year)] = [mobility_input[0]]
        else:
            mobility_values[(mobility_input[1].month,mobility_input[1].year)].append(mobility_input[0])

    dates = []
    for key in mobility_values.keys():
        dates.append("{}-{}-01".format(key[1],key[0]))

    averages = []
    for key, mobility_input_list in mobility_values.items():
        input_sum = 0
        for input_val in mobility_input_list:
            input_sum += int(input_val)
        averages.append(input_sum/len(mobility_input_list))
    df = pd.DataFrame(dict(
        date=dates,
        happiness=averages
    ))
    df.sort_values('date', inplace=True)
    line_one = go.Figure(layout_yaxis_range=[0,6])
    line_one.add_trace(go.Scatter(name="",x=df["date"], y=df["happiness"]))
    line_one.update_layout(
                width=630,
                height=260,
                yaxis={"tickvals" : [1,2,3,4,5]}
    )
    line_graph_one = json.dumps(line_one, cls=plotly.utils.PlotlyJSONEncoder)

    # Monthly Overall Rating of Walking Difficulty
    food_quality_proportion = Input.query.filter_by(category="food_quality").with_entities(Input.name,Input.date).all()#.group_by(Input.name).all()
    #print(mobility_proportion)
    food_quality_values = {}
    for food_quality_input in food_quality_proportion:
        if food_quality_values.get((food_quality_input[1].month,food_quality_input[1].year)) is None:
            food_quality_values[(food_quality_input[1].month,food_quality_input[1].year)] = [food_quality_input[0]]
        else:
            food_quality_values[(food_quality_input[1].month,food_quality_input[1].year)].append(food_quality_input[0])

    dates = []
    for key in food_quality_values.keys():
        dates.append("{}-{}-01".format(key[1],key[0]))

    averages = []
    for key, food_quality_input_list in food_quality_values.items():
        input_sum = 0
        for input_val in food_quality_input_list:
            input_sum += int(input_val)
        averages.append(input_sum/len(food_quality_input_list))
    print(averages)
    df = pd.DataFrame(dict(
        date=dates,
        food_quality_values=averages
    ))
    df.sort_values('date', inplace=True)

    line_two = go.Figure(layout_yaxis_range=[0,6])
    line_two.add_trace(go.Scatter(name="",x=df["date"], y=df["food_quality_values"]))
    line_two.update_layout(
                width=630,
                height=260,
                yaxis={"tickvals" : [1,2,3,4,5]}
    )
    line_graph_two = json.dumps(line_two, cls=plotly.utils.PlotlyJSONEncoder)

    # Medication
    medication_proportion = Input.query.filter_by(category="medication").with_entities(Input.name,Input.date).all()

    medication_values = {}
    for medication_input in medication_proportion:
        if medication_values.get((medication_input[1].month,medication_input[1].year)) is None:
            medication_values[(medication_input[1].month,medication_input[1].year)] = [medication_input[0]]
        else:
            medication_values[(medication_input[1].month,medication_input[1].year)].append(medication_input[0])

    dates = []
    for key in medication_values.keys():
        dates.append("{}-{}-01".format(key[1],key[0]))

    averages = []
    for key, medication_input_list in medication_values.items():
        input_sum = 0
        for input_val in medication_input_list:
            input_sum += 1 if input_val=="yes" else 0
        averages.append(input_sum/len(medication_input_list))
    print(averages)
    df = pd.DataFrame(dict(
        date=dates,
        medication_values=averages
    ))
    df.sort_values('date', inplace=True)

    line_three = go.Figure(layout_yaxis_range=[-0.1,1.1])
    line_three.add_trace(go.Scatter(name="",x=df["date"], y=df["medication_values"]))
    line_three.update_layout(
                width=630,
                height=260,
    )
    line_graph_three = json.dumps(line_three, cls=plotly.utils.PlotlyJSONEncoder)

    # Aches and Pains
    pain_proportion = Input.query.filter_by(category="regular_pain_ache").with_entities(Input.name,Input.date).all()

    pain_values = {}
    for pain_input in pain_proportion:
        if pain_values.get((pain_input[1].month,pain_input[1].year)) is None:
            pain_values[(pain_input[1].month,pain_input[1].year)] = [pain_input[0]]
        else:
            pain_values[(pain_input[1].month,pain_input[1].year)].append(pain_input[0])

    dates = []
    for key in pain_values.keys():
        dates.append("{}-{}-01".format(key[1],key[0]))

    averages = []
    for key, pain_input_list in pain_values.items():
        input_sum = 0
        for input_val in pain_input_list:
            input_sum += 1 if input_val=="yes" else 0
        averages.append(input_sum/len(pain_input_list))
    print(averages)
    df = pd.DataFrame(dict(
        date=dates,
        pain_values=averages
    ))
    df.sort_values('date', inplace=True)

    line_four = go.Figure(layout_yaxis_range=[-0.1,1.1])
    line_four.add_trace(go.Scatter(name="",x=df["date"], y=df["pain_values"]))
    line_four.update_layout(
                width=630,
                height=260,
    )
    line_graph_four = json.dumps(line_four, cls=plotly.utils.PlotlyJSONEncoder)


    message_list = Input.query.filter_by(category="nursing_home_life_experience").with_entities(Input.name).all()
    messages = [message[0] for message in message_list if message[0] != '']
    if len(messages) < 400:
        messages = messages * round(500/len(messages))



    

    num_residents = len(User.query.all())
    num_nursing_home = len(NursingHome.query.all())
    return render_template("public-dashboard.html",graph_activities=graph_activities, mood_ratio=mood_ratio,
                            detailed_mood_ratio=detailed_mood_ratio, state_pie_chart=state_pie_chart,
                            line_graph_one=line_graph_one, line_graph_two=line_graph_two,
                            line_graph_three=line_graph_three, line_graph_four=line_graph_four, 
                            num_residents=num_residents, num_nursing_home=num_nursing_home,sentences=messages,reload_time = datetime.now().strftime("%H:%M"))


# ===============================================================================================================
# =============================================== RESIDENT/GUEST ================================================
# ===============================================================================================================
@views.route('/user', methods=['GET', 'POST'])
@login_required
def user_home():
    return render_template("user/home_user.html", user=current_user, name=get_name("resident"), home_href=USER_HOME_HREF)


@views.route('/user/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    return render_template("user/profile_update_user.html", user=current_user, name=get_name("resident"), home_href=USER_HOME_HREF)


@views.route('/user/inputs', methods=['GET', 'POST'])
@login_required
def user_input():
    input_options_rows = InputOptions.query.filter_by(nursing_home_id=current_user.nursing_home_id).all()

    if request.method == 'POST': 
        # Empty strings returned if no options are selected
        input_category = request.form.get('input_category')     # activity, wellbeing, medication_reaction, difficulty_walking, food_quality
        activity_csv = request.form.get('input_activity')
        wellbeing_csv = request.form.get('input_wellbeing')
        medication_reaction_csv = request.form.get('input_medication_reaction') # negative_reaction_yes, negative_reaction_no
        difficulty_walking_csv = request.form.get('input_difficulty_walking')   # walk_difficult_1, walk_difficult_2, ..., walk_difficult_5
        food_quality_csv = request.form.get('input_food_quality')               # food_quality_1, food_quality_2, ..., food_quality_5
        text_area_msg_board = request.form.get('input_message_board')
        regular_pain_ache_csv = request.form.get('input_regular_pain_ache')
        
        # print()
        # print(input_category)
        # print()
        
        # print("CSV-activity:", activity_csv)
        # print("CSV-wellbeing:", wellbeing_csv)
        # print("CSV-medication:", medication_reaction_csv)
        # print("CSV-walk:", difficulty_walking_csv)
        # print("CSV-food:", food_quality_csv)
        # print("CSV-pain:", regular_pain_ache_csv)
        
        # print()

        activity_list = activity_csv.split(',')[:-1]
        wellbeing_list = wellbeing_csv.split(',')[:-1]
        medication_reaction_list = medication_reaction_csv.split(',')[:-1]
        difficulty_walking_list = difficulty_walking_csv.split(',')[:-1]
        food_quality_list = food_quality_csv.split(',')[:-1]
        regular_pain_ache_list = regular_pain_ache_csv.split(',')[:-1]
        
        input_activity_set = set(activity_list)
        input_wellbeing_set = set(wellbeing_list)
        
        # print("LIST-activity:", activity_list)
        # print("LIST-wellbeing:", wellbeing_list)
        # print("LIST-medication:", medication_reaction_list)
        # print("LIST-walk:", difficulty_walking_list)
        # print("LIST-food:", food_quality_list)
        
        # print()
        
        # Filter and keep valid inputs, in case someone changes the input names to something else using inspect mode
        existing_input_options_activity_rows = InputOptions.query.filter_by(category="activity", 
                                                                            nursing_home_id=current_user.nursing_home_id).all()
        existing_input_options_wellbeing_rows = InputOptions.query.filter_by(category="wellbeing", 
                                                                            nursing_home_id=current_user.nursing_home_id).all()
        valid_input_option_activity_name_set = {str(row.name) for row in existing_input_options_activity_rows}
        valid_input_option_wellbeing_name_set = {str(row.name) for row in existing_input_options_wellbeing_rows}
        
        valid_selected_input_options_activity = input_activity_set.intersection(valid_input_option_activity_name_set)
        valid_selected_input_options_wellbeing = input_wellbeing_set.intersection(valid_input_option_wellbeing_name_set)

        if input_category == 'activity':
            if len(valid_selected_input_options_activity) == 0:
                flash("No inputs submitted for activity")
                return redirect(request.url)
            for activity in valid_selected_input_options_activity:          
            # user_id=0 means Guest account for the nursing home
                if current_user.admin:
                    activity_input = Input(category="activity", name=activity, user_id=0, 
                                            nursing_home_id=current_user.nursing_home_id)
                # Else use resident user_id
                else:
                    activity_input = Input(category="activity", name=activity, user_id=current_user.id,
                                            nursing_home_id=current_user.nursing_home_id)
                db.session.add(activity_input)
                db.session.commit()
                # print(activity)
            return redirect(request.url)
        
        elif input_category == 'wellbeing':
            if len(valid_selected_input_options_wellbeing) == 0:
                flash("No inputs submitted for wellbeing")
                return redirect(request.url)
            for wellbeing in valid_selected_input_options_wellbeing:          
                # user_id=0 means Guest account for the nursing home
                if current_user.admin:
                    wellbeing_input = Input(category="wellbeing", name=wellbeing, user_id=0,
                                            nursing_home_id=current_user.nursing_home_id)
                # Else use resident user_id
                else:
                    wellbeing_input = Input(category="wellbeing", name=wellbeing, user_id=current_user.id,
                                            nursing_home_id=current_user.nursing_home_id)
                db.session.add(wellbeing_input)
                db.session.commit()
                # print(wellbeing)
            return redirect(request.url)

        # Convert the yes/no, 1-5 rating questions into right value
        elif input_category == 'medication_reaction':
            if len(medication_reaction_list) == 1:
                if medication_reaction_list[0] == "negative_reaction_no":
                    medication_input_value = "no"
                elif medication_reaction_list[0] == "negative_reaction_yes":
                    medication_input_value = "yes"
                else:
                    flash("Please don't change the id values for medication")
                    return redirect(request.url)
            elif len(medication_reaction_list) == 0:
                flash("No inputs submitted for medication")
                return redirect(request.url)
            else:
                flash("Please don't change the id values for medication")
                return redirect(request.url)
            
            # Insert Medication Y/N data to Database
            if current_user.admin:
                medication_input = Input(category="medication", name=medication_input_value, user_id=0, 
                                            nursing_home_id=current_user.nursing_home_id)
            else:
                medication_input = Input(category="medication", name=medication_input_value, user_id=current_user.id, 
                                            nursing_home_id=current_user.nursing_home_id)
            db.session.add(medication_input)
            db.session.commit()
            return redirect(request.url)
            
        elif input_category == 'difficulty_walking':
            if len(difficulty_walking_list) == 1:
                if difficulty_walking_list[0] == "walk_difficult_1":
                    difficulty_walking_input_value = 1
                elif difficulty_walking_list[0] == "walk_difficult_2":
                    difficulty_walking_input_value = 2
                elif difficulty_walking_list[0] == "walk_difficult_3":
                    difficulty_walking_input_value = 3
                elif difficulty_walking_list[0] == "walk_difficult_4":
                    difficulty_walking_input_value = 4
                elif difficulty_walking_list[0] == "walk_difficult_5":
                    difficulty_walking_input_value = 5
                else:
                    flash("Please don't change the id values for difficulty walking")
                    return redirect(request.url)
            elif len(difficulty_walking_list) == 0:
                flash("No inputs submitted for difficulty walking")
                return redirect(request.url)
            else:
                flash("Please don't change the id values for difficulty walking")
                return redirect(request.url)
            
            # Insert difficulty walking rating 1-5 data to Database
            if current_user.admin:
                difficulty_walking_input = Input(category="difficulty_walking", name=difficulty_walking_input_value,
                                                user_id=0, nursing_home_id=current_user.nursing_home_id)
            else:
                difficulty_walking_input = Input(category="difficulty_walking", name=difficulty_walking_input_value,
                                                user_id=current_user.id, nursing_home_id=current_user.nursing_home_id)
            db.session.add(difficulty_walking_input)
            db.session.commit()
            return redirect(request.url)
            
        elif input_category == 'food_quality':
            if len(food_quality_list) == 1:
                if food_quality_list[0] == "food_quality_1":
                    food_quality_input_value = 1
                elif food_quality_list[0] == "food_quality_2":
                    food_quality_input_value = 2
                elif food_quality_list[0] == "food_quality_3":
                    food_quality_input_value = 3
                elif food_quality_list[0] == "food_quality_4":
                    food_quality_input_value = 4
                elif food_quality_list[0] == "food_quality_5":
                    food_quality_input_value = 5
                else:
                    flash("Please don't change the id values for food quality")
                    return redirect(request.url)
            elif len(food_quality_list) == 0:
                flash("No inputs submitted for food quality")
                return redirect(request.url)
            else:
                flash("Please don't change the id values for food quality")
                return redirect(request.url)
            
            # Insert difficulty walking rating 1-5 data to Database
            if current_user.admin:
                food_quality_input = Input(category="food_quality", name=food_quality_input_value, user_id=0,
                                            nursing_home_id=current_user.nursing_home_id)
            else:
                food_quality_input = Input(category="food_quality", name=food_quality_input_value, user_id=current_user.id,
                                            nursing_home_id=current_user.nursing_home_id)
            db.session.add(food_quality_input)
            db.session.commit()
            return redirect(request.url)
        
        elif input_category == 'message_text_area':
            if len(text_area_msg_board) == 0:
                flash("No inputs submitted")
                return redirect(request.url)
            
            if current_user.admin:
                text_area_msg_board_input = Input(category="nursing_home_life_experience", name=text_area_msg_board,
                                                user_id=0, nursing_home_id=current_user.nursing_home_id)
            else:
                text_area_msg_board_input = Input(category="nursing_home_life_experience", name=text_area_msg_board, 
                                                user_id=current_user.id, nursing_home_id=current_user.nursing_home_id)
            db.session.add(text_area_msg_board_input)
            db.session.commit()
            return redirect(request.url)
    
        # Convert the yes/no, 1-5 rating questions into right value
        elif input_category == 'regular_pain_ache':
            if len(regular_pain_ache_list) == 1:
                if regular_pain_ache_list[0] == "regular_pain_ache_no":
                    regular_pain_ache_input_value = "no"
                elif regular_pain_ache_list[0] == "regular_pain_ache_yes":
                    regular_pain_ache_input_value = "yes"
                else:
                    flash("Please don't change the id values for regular pain/ache")
                    return redirect(request.url)
            elif len(regular_pain_ache_list) == 0:
                flash("No inputs submitted for regular pain/ache")
                return redirect(request.url)
            else:
                flash("Please don't change the id values for regular pain/ache")
                return redirect(request.url)
            
            # Insert Medication Y/N data to Database
            if current_user.admin:
                regular_pain_ache_input = Input(category="regular_pain_ache", name=regular_pain_ache_input_value, user_id=0, 
                                            nursing_home_id=current_user.nursing_home_id)
            else:
                regular_pain_ache_input = Input(category="regular_pain_ache", name=regular_pain_ache_input_value, user_id=current_user.id, 
                                            nursing_home_id=current_user.nursing_home_id)
            db.session.add(regular_pain_ache_input)
            db.session.commit()
            return redirect(request.url)
        
        return redirect(request.url)
    
    # If Guest account
    if current_user.admin:
        return render_template("inputs_ver2.html", user=current_user, rows=input_options_rows, name=get_name("guest"), home_href=GUEST_HOME_HREF)
    else:
        return render_template("inputs_ver2.html", user=current_user, rows=input_options_rows, name=get_name("resident"), home_href=USER_HOME_HREF)