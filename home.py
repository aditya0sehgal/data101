from flask import Flask, render_template, request
import pandas as pd
import random, numpy, csv, io, os, json

app = Flask(__name__)
column_cat = {}
current_dataset_columns = []
file_name = ""
categorical_columns = []
numerical_columns = []
current_dataset = []
Questions = pd.DataFrame(columns=["Type of question", "Question", "Answer", "Template code"])

# Home landing page
@app.route("/" , methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/upload', methods=['POST'])
def upload():
    global file_name
    file = request.files['datasetFile']
    if file:
        destination_path = os.getcwd()  # Get the current working directory
        file.save(os.path.join(destination_path+'\datasets', file.filename))
        file_name = file.filename
        print(file_name)
        column_names = extract_column_names(file_name)
        temparr = []
        for col in column_names:
            print(col)
            temparr.append(col)
        return {'column_names': temparr}
    else:
        return {'column_names': []}
    

def extract_column_names(file):
    global current_dataset_columns
    col_names = pd.read_csv(os.path.join(os.getcwd() +'\datasets', file)).columns
    current_dataset_columns = col_names
    print(col_names)
    return col_names

# Post call based on no of questions input
@app.route('/column-selection', methods=['POST'])
def selectCatNumIgnore():
    try:
        global current_dataset_columns, column_cat, categorical_columns, numerical_columns, Questions

        data = {}
        for col in current_dataset_columns:
            data[col] = request.form.get(col)

        column_cat = json.dumps(data)
        print(column_cat, data)
        
        for key, value in data.items():
            if value == "numerical": 
                numerical_columns.append(key)
            elif value == "categorical": 
                categorical_columns.append(key)
        print(column_cat)
        print(categorical_columns)
        print(numerical_columns)
        return render_template('generate.html')

    except Exception as e:
        return render_template('error.html')
        

# Post call based on no of questions input
@app.route('/generate', methods=['POST'])
def generate():
    global current_dataset, file_name
    try:
        no_of_questions = int(request.form['no_questions'])
        print("Questions : ", str(no_of_questions))
        current_dataset = pd.read_csv(os.path.join(os.getcwd() +'\datasets', file_name))
        current_dataset = current_dataset.fillna(0)
        
        aggregate_ops = ['min', 'max', 'count', 'avg', 'sum']
        categorical_attr = ['name', 'host_name', 'neighbourhood_group',	'neighbourhood', 'room_type']
        numerical_attr = airbnb.describe().columns[1:]
        question_list = []
        duplicate_question_check = {}
        count = 0
        while(count < no_of_questions):
            base_question_str = "What is the "+random.choice(aggregate_ops)+" price when";
            for attribute_no in range(random.choice(range(1, 5))):
                random_column = random.choice(categorical_attr) 
                base_question_str += " and "+ random_column +" = '"+random.choice(list(set(airbnb[random_column].values)))+"'"

            if base_question_str not in duplicate_question_check:
                question_list.append(base_question_str)
                duplicate_question_check[base_question_str] = 1
                count += 1
            else:
                print("Duplicate question at ", str(count))

        questionsDF = pd.DataFrame(question_list, columns=['Questions'])
        questionsDF.to_csv("GeneratedQuestions.csv")
        questions_html = questionsDF.to_html()
        return render_template('successful_csv_generation.html', data=questions_html)
    
    except Exception as e:
        return render_template('error.html')
        

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')