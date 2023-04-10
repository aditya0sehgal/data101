from flask import Flask, render_template, request
import pandas as pd
import random, numpy, csv

app = Flask(__name__)

# Home landing page
@app.route("/")
def home():
    return render_template('home.html')

# Post call based on no of questions input
@app.route('/generate', methods=['POST'])
def generate():
    try:
        no_of_questions = int(request.form['no_questions'])
        print("Questions : ", str(no_of_questions))
        airbnb = pd.read_csv("https://raw.githubusercontent.com/dev7796/data101_tutorial/main/files/dataset/airbnb.csv")

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
        return render_template('generated.html', data=questions_html)
    
    except Exception as e:
        return render_template('error.html')
    
    
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')