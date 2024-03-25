from flask import Flask, render_template, request, send_file, Response, url_for, redirect,  jsonify, session
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import random, numpy as np, csv, io, os, json
from datetime import datetime
import bcrypt
import math

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret'  # Needed for session management
db = SQLAlchemy(app)

rounding_data = {}
current_dataset_columns = []
file_name = ""
categorical_columns = []
numerical_columns = []
current_dataset = []
df = None
negation_dictionary = {"<" : ">=", ">" : "<=", "<=" : ">", ">=" : "<", "==" : "!=", "!=" : "=="}
symbol_text_dictionary = {"<" : "is less than", ">" : "is greater than", "<=" : "is less than or equal to", ">=" : "is greater than or equal to", "==" : "is equal to", "!=" : "is not equal to"}
pre_symbol_text_dictionary = {"<" : "less than", ">" : "greater than", "<=" : "less than or equal to", ">=" : "greater than or equal to", "==" : "equal to", "!=" : "not equal to"}
Questions = pd.DataFrame(columns=["Type of question", "Question", "Answer", "Template code"])

# Home landing page
@app.route("/" , methods=['GET'])
def home():
    return render_template('auth.html')

@app.route('/checkpassword', methods=['POST'])
def checkpassword():
    userinput = request.form['password']
    
    if bcrypt.checkpw(userinput.encode('utf-8'), b'$2b$12$2Wxh7W4WmbGyZLC1GhJCZ.Bkuh3Ty0sanqiL67S67i7MqKs4PAFw2'):
        return render_template('home.html')
    else:
        return render_template('unauthorized.html')
    
@app.route('/upload', methods=['POST'])
def upload():
    global file_name
    file = request.files['datasetFile']
    if file:
        destination_path = os.getcwd()  # Get the current working directory
        # for hosting
        # file.save(os.path.join(destination_path+'/mysite/datasets', file.filename))
        file.save(os.path.join(destination_path+'/datasets', file.filename))
        file_name = file.filename
        column_names = extract_column_names(file_name)
        temparr = []
        for col in column_names:
            temparr.append(col)
        return {'column_names': temparr}
    else:
        return {'column_names': []}

@app.route('/roulette/<template>', methods=['GET'])
def roulette_template(template):
    try:
        # for hosting
        # df = pd.read_csv(os.path.join(os.getcwd() +'/mysite/datasets/', 'Questions.csv'))
        df = pd.read_csv(os.path.join(os.getcwd() +'/datasets', 'Questions.csv'))

        val = template.split('-')
        if (val[0]+" "+val[1]).upper() not in df['Dataset_Name'].values:
            return render_template('nodataset.html')

        df = df[df['Dataset_Name'] == (val[0]+" "+val[1]).upper()]
        # Iterate over the DataFrame and get each row's values
        rows = []
        for index, row in df.iterrows():
            values = row.values
            rows.append([values[1], values[2], values[3], values[4], values[0]])
        roulette_template = {0: rows}
        return render_template('rouletteQA.html', data=roulette_template)
    
    except Exception as e:
        return render_template('error.html')

def extract_column_names(file):
    global current_dataset_columns
    # col_names = pd.read_csv(os.path.join(os.getcwd() +'/mysite/datasets', file)).columns
    col_names = pd.read_csv(os.path.join(os.getcwd() +'/datasets', file)).columns
    current_dataset_columns = col_names
    return col_names

@app.route('/column-selection', methods=['POST'])
def selectCatNumIgnore():
    try:
        global current_dataset_columns, categorical_columns, numerical_columns, Questions, rounding_data
        categorical_columns, numerical_columns = [], []
        data = {}
        
        print(request.form)
        for col in current_dataset_columns:
            data[col] = request.form.get(col)
            rounding_data[col] = request.form.get(col+"-rounding")
        
        print(rounding_data)

        for key, value in data.items():
            if value == "numerical": 
                numerical_columns.append(key)

            elif value == "categorical": 
                categorical_columns.append(key)

            if value != "numerical": 
                del rounding_data[key]
        
        print(rounding_data)
        return render_template('generate.html')

    except Exception as e:
        return render_template('error.html')
        
def Evaluate_py_code(py_code):
  global df
  evaluated_code = eval(py_code)
  return round(evaluated_code, 2)

def checkEmptyRow(py_code):
  global df
  if eval(py_code) == 0:
      return True
  return False

def General_template(Dataset_name, L, Cat_name_1, Cat_name_2, Cat_name_3, Cat_Values_1, Cat_Values_2, Cat_Values_3,
                     Cat_Operator_1, Cat_Operator_2, Num_name_1, Num_name_2, Num_name_3, Num_val_1, Num_val_2, Num_val_3,
                     Num_Operator_1, Num_Operator_2, onenumcol):
    
    Aggregate_selection = random.choice(["max", "min", "mean"])
    aggregate_text_dictionary = {"max" : "maximum", "min" : "minimum", "mean" : "mean"}

    Question = ""
    Answer_Code = ""
    global symbol_text_dictionary
    if L == 1:
        Question = f"What is the {aggregate_text_dictionary[Aggregate_selection]} {Num_name_1.upper()}?"
        Answer_Code = General_template_code(L, Aggregate_selection, Num_name_1, "0", "0", "0", "0", "0", "0")
        # if Answer_Code[1] == -1:
        #     return ["", ""]
    elif L == 2:
        choice = random.choice([1, 2])
        if choice == 1 and Num_name_1!=Num_name_2:
            Question = f"What is the {aggregate_text_dictionary[Aggregate_selection]} {Num_name_1.upper()}, where {Num_name_2.upper()} {symbol_text_dictionary[Num_Operator_2]} {Num_val_2}?"
            Answer_Code = General_template_code(L, Aggregate_selection, Num_name_1, Num_name_2, Num_Operator_2, Num_val_2, "0", "0", "0")
            # if Answer_Code[1] == -1:
            #     return ["", ""]
        else:
            Question = f"What is the {aggregate_text_dictionary[Aggregate_selection]} {Num_name_1.upper()}, where {Cat_name_2.upper()} {symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_2}'?"
            Answer_Code = General_template_code(L, Aggregate_selection, Num_name_1, Cat_name_2, Cat_Operator_1, Cat_Values_2, "0", "0", "0")
            # if Answer_Code[1] == -1:
            #     return ["", ""]
    elif L == 3:
        choice = random.choice([1, 2, 3])
        if choice == 1 and Cat_name_1!=Cat_name_2:
            Question = f"What is the {aggregate_text_dictionary[Aggregate_selection]} {Num_name_1.upper()}, where {Cat_name_1.upper()} {symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}' and {Cat_name_2.upper()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_2}'?"
            Answer_Code = General_template_code(L, Aggregate_selection, Num_name_1, Cat_name_1, Cat_Operator_1, Cat_Values_1, Cat_name_2, Cat_Operator_2, Cat_Values_2)
            # if Answer_Code[1] == -1:
            #     return ["", ""]
        elif choice == 2 and Num_name_1!=Num_name_2:
            Question = f"What is the {aggregate_text_dictionary[Aggregate_selection]} {Num_name_1.upper()}, where {Num_name_2.upper()} {symbol_text_dictionary[Num_Operator_2]} {Num_val_2} and {Cat_name_3.upper()} {symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_3}'?"
            Answer_Code = General_template_code(L, Aggregate_selection, Num_name_1, Num_name_2, Num_Operator_2, Num_val_2, Cat_name_3, Cat_Operator_1, Cat_Values_3)
            # if Answer_Code[1] == -1:
            #     return ["", ""]
        else:
            if Num_name_1!=Num_name_2 and Num_name_3!=Num_name_2:
              return ["", ""]
            
    Question_code = [Question, Answer_Code]
    return Question_code

# Template 2: General Min, Max, and Mean
def General_template_code(L, Aggregate_selection, Num_name_1, condition_1, operator_1, condition_value_1, condition_2, operator_2, condition_value_2):
    if L == 1:
        Answer_code_R = f"round({Aggregate_selection}(df${Num_name_1}), 2);"
        Answer_code_py = f"df['{Num_name_1}'].{Aggregate_selection}()"
    elif L == 2:
        if isinstance(condition_value_1, str):
          Answer_code_R = f"temp <- df[df${condition_1} {operator_1} '{condition_value_1}', ]; round({Aggregate_selection}(temp${Num_name_1}), 2);"
          Answer_code_py = f"df.loc[df['{condition_1}'] {operator_1} '{condition_value_1}', '{Num_name_1}'].{Aggregate_selection}()"
        else:
          Answer_code_R = f"temp <- df[df${condition_1} {operator_1} {condition_value_1}, ]; round({Aggregate_selection}(temp${Num_name_1}), 2);"
          Answer_code_py = f"df.loc[df['{condition_1}'] {operator_1} {condition_value_1}, '{Num_name_1}'].{Aggregate_selection}()" 
    elif L == 3:        
        if isinstance(condition_value_1, str):
          Answer_code_R = f"temp <- df[df${condition_1} {operator_1} '{condition_value_1}' & df${condition_2} {operator_2} '{condition_value_2}', ]; round({Aggregate_selection}(temp${Num_name_1}), 2);"
          Answer_code_py = f"df.loc[(df['{condition_1}'] {operator_1} '{condition_value_1}') & (df['{condition_2}'] {operator_2} '{condition_value_2}'), '{Num_name_1}'].{Aggregate_selection}()"
        else:
          Answer_code_R = f"temp <- df[df${condition_1} {operator_1} {condition_value_1} & df${condition_2} {operator_2} '{condition_value_2}', ]; round({Aggregate_selection}(temp${Num_name_1}), 2);"
          Answer_code_py = f"df.loc[(df['{condition_1}'] {operator_1} {condition_value_1}) & (df['{condition_2}'] {operator_2} '{condition_value_2}'), '{Num_name_1}'].{Aggregate_selection}()"
        
    Answer_py = Evaluate_py_code(Answer_code_py)
    return [Answer_code_R, Answer_py]

def getGeneralQuestions(question_no_split, df, Categorical_Columns, Numerical_Columns, dataset_name, onenumcol):
    Num_Operator = ["<", "<=", ">=", ">"]
    numops_below_25 = ["<", "<="]
    numops_25_75 = Num_Operator
    numops_above_75 = [">=", ">"]
    Cat_Operator = ["==", "!="]
    Ques_Ans = []
    duplicate_question_check = set()
    count = 0
    while(count < question_no_split):
        Cat_name_1 = random.choice(Categorical_Columns)
        Unique_Cat_Values_1 = df[Cat_name_1].unique()
        Cat_Values_1 = random.choice(Unique_Cat_Values_1)

        Cat_name_2 = random.choice(Categorical_Columns)
        Unique_Cat_Values_2 = df[Cat_name_2].unique()
        Cat_Values_2 = random.choice(Unique_Cat_Values_2)

        Cat_name_3 = random.choice(Categorical_Columns)
        Unique_Cat_Values_3 = df[Cat_name_3].unique()
        Cat_Values_3 = random.choice(Unique_Cat_Values_3)

        Cat_Operator_1 = random.choice(Cat_Operator)
        Cat_Operator_2 = random.choice(Cat_Operator)
        
        if "'" in Cat_Values_1 or "'" in Cat_Values_2 or "'" in Cat_Values_3:
            continue

        # here check if selected numval1 and 2 are at extremes then dont send invalid operators.
        Num_name_1 = random.choice(Numerical_Columns)
        value1 = min(df[Num_name_1])
        value2 = max(df[Num_name_1])
        Num_val_1 = round(random.uniform(1.1*value1, 0.9*value2), 2)

        intval_1 = int(Num_val_1)
        Num_val_1 = intval_1
        if intval_1 < value1:
            Num_val_1 = math.ceil(intval_1) 
        if Num_val_1 > value2:
            Num_val_1 = math.floor(intval_1) 

        diff = value2 - value1
        if Num_val_1 < (0.25 * diff):
            Num_Operator_1  = random.choice(numops_below_25) 
        elif Num_val_1 <= (0.75  * diff):
            Num_Operator_1 = random.choice(numops_25_75)
        elif Num_val_1 > (0.75 * diff):
            Num_Operator_1 = random.choice(numops_above_75)


        Num_name_2 = random.choice(Numerical_Columns)
        value1 = min(df[Num_name_2])
        value2 = max(df[Num_name_2])
        Num_val_2 = round(random.uniform(1.1*value1, 0.9*value2), 2)

        intval_2 = int(Num_val_2)
        Num_val_2 = intval_2
        if intval_2 < value1:
            Num_val_2 = math.ceil(intval_2) 
        if Num_val_2 > value2:
            Num_val_2 = math.floor(intval_2) 

        diff = value2 - value1
        if Num_val_2 < (0.25 * diff):
            Num_Operator_2  = random.choice(numops_below_25) 
        elif Num_val_2 <= (0.75  * diff):
            Num_Operator_2 = random.choice(numops_25_75)
        elif Num_val_2 > (0.75 * diff):
            Num_Operator_2 = random.choice(numops_above_75)

        Num_name_3 = random.choice(Numerical_Columns)
        value1 = int(min(df[Num_name_3]))
        value2 = int(max(df[Num_name_3]))
        Num_val_3 = random.randint(value1, value2)
        
        Type = "General Question"

        L = random.choice(range(1, 4))

        Generated_Question = General_template(dataset_name, L, Cat_name_1, Cat_name_2, Cat_name_3, Cat_Values_1,
                                            Cat_Values_2, Cat_Values_3, Cat_Operator_1, Cat_Operator_2, Num_name_1,
                                            Num_name_2, Num_name_3, Num_val_1, Num_val_2, Num_val_3, Num_Operator_1,
                                            Num_Operator_2, onenumcol)
        
        if Generated_Question[0] == "" or  Generated_Question[0] in duplicate_question_check :
            continue
        duplicate_question_check.add(Generated_Question[0])
        count += 1

        Generated_Answer =  "Empty result" if np.isnan(Generated_Question[1][1]) else Generated_Question[1][1]
        Ques_Ans.append([Type, Generated_Question[0], Generated_Answer, Generated_Question[1][0], dataset_name.upper(), str(datetime.now().date())])
    return Ques_Ans

# Template 1 Bayesian
def Bayesian_template(Dataset_name, L, Cat_name_1, Cat_name_2, Cat_name_3, Cat_Values_1, Cat_Values_2, Cat_Values_3, Cat_Operator_1, Cat_Operator_2, Num_name_1, Num_name_2, Num_name_3, Num_val_1, Num_val_2, Num_val_3, Num_Operator_1, Num_Operator_2, onenumcol, variant_row):
    global symbol_text_dictionary
    Question = ""
    Answer_Code = ""
    if L == 2:
        choice = random.randint(1, 4)
        if choice == 1 and Cat_name_1 != Cat_name_2:
            if variant_row[1] == 0:
               Question = f"{variant_row[0][0].strip()} {Cat_name_1.upper()} being {pre_symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}', {variant_row[0][1].strip()}  {Cat_name_2.upper()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_2}'?"
            else:
               Question = f"{variant_row[0][0].strip()} {Cat_name_2.upper()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_2}', {variant_row[0][1].strip()} {Cat_name_1.upper()} is {pre_symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}'?"
            Answer_Code = Bayesian_template_code(L, Cat_name_1, Cat_Operator_1, Cat_Values_1, Cat_name_2, Cat_Operator_2, Cat_Values_2, "0", "0", "0")
        
        elif choice == 2:
            if variant_row[1] == 0:
                Question = f"{variant_row[0][0].strip()} {Cat_name_1.upper()} being {pre_symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}', {variant_row[0][1].strip()} the {Num_name_1.upper()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_1}?"
            else:
                Question = f"{variant_row[0][0].strip()} the {Num_name_1.upper()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_1}, {variant_row[0][1].strip()} {Cat_name_1.upper()} is {pre_symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}'?"
            Answer_Code = Bayesian_template_code(L, Cat_name_1, Cat_Operator_1, Cat_Values_1, Num_name_1, Num_Operator_1, Num_val_1, "0", "0", "0")
        
        elif choice == 3:
            if variant_row[1] == 0:
                Question = f"{variant_row[0][0].strip()} the {Num_name_1.upper()} being {pre_symbol_text_dictionary[Num_Operator_1]} {Num_val_1}, {variant_row[0][1].strip()}  {Cat_name_1.upper()} {symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}'?"
            else:
                Question = f"{variant_row[0][0].strip()} {Cat_name_1.upper()} {symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}', {variant_row[0][1].strip()} the {Num_name_1.upper()} is {pre_symbol_text_dictionary[Num_Operator_1]} {Num_val_1}?"
            Answer_Code = Bayesian_template_code(L, Num_name_1, Num_Operator_1, Num_val_1, Cat_name_1, Cat_Operator_1, Cat_Values_1, "0", "0", "0")
        
        elif choice > 3:
            if onenumcol:
              return ["", ""]
            elif Num_name_1!=Num_name_2 :
                if variant_row[1] == 0:
                    Question = f"{variant_row[0][0].strip()} the {Num_name_1.upper()} being {pre_symbol_text_dictionary[Num_Operator_1]} {Num_val_1}, {variant_row[0][1].strip()} the {Num_name_2.upper()} {symbol_text_dictionary[Num_Operator_2]} {Num_val_2}?"
                else:
                    Question = f"{variant_row[0][0].strip()} the {Num_name_2.upper()} {symbol_text_dictionary[Num_Operator_2]} {Num_val_2}, {variant_row[0][1].strip()} the {Num_name_1.upper()} is {pre_symbol_text_dictionary[Num_Operator_1]} {Num_val_1}?"
                Answer_Code = Bayesian_template_code(L, Num_name_1, Num_Operator_1, Num_val_1, Num_name_2, Num_Operator_2, Num_val_2, "0", "0", "0")

    else:
        choice = random.randint(1, 6)
        if choice == 1:
          if (Cat_name_1 == Cat_name_2 or Cat_name_3 == Cat_name_2 or Cat_name_1 == Cat_name_3):
            # not valid question because of overlaps in nums and cat choices.
            return ["", ""]
          else:
            if variant_row[1] == 0:
                Question = f"{variant_row[0][0].strip()} {Cat_name_1.upper()} being {pre_symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}', {variant_row[0][1].strip()} {Cat_name_2.upper()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_2}' and {Cat_name_3.upper()} {symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_3}'?"
            else:
                Question = f"{variant_row[0][0].strip()} {Cat_name_2.upper()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_2}' and {Cat_name_3.upper()} {symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_3}', {variant_row[0][1].strip()} {Cat_name_1.upper()} is {pre_symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}'?"
            Answer_Code = Bayesian_template_code(L, Cat_name_1, Cat_Operator_1, Cat_Values_1, Cat_name_2, Cat_Operator_2, Cat_Values_2, Cat_name_3, Cat_Operator_1, Cat_Values_3)
       
        elif choice == 2:
          if (Cat_name_1 == Cat_name_3):
            # not valid question because of overlaps in nums and cat choices.
            return ["", ""]
          else:
            if variant_row[1] == 0:
                Question = f"{variant_row[0][0].strip()} {Cat_name_1.upper()} being {pre_symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}', {variant_row[0][1].strip()} the {Num_name_1.upper()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_1} and {Cat_name_3.upper()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_3}'?"
            else:
                Question = f"{variant_row[0][0].strip()} the {Num_name_1.upper()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_1} and {Cat_name_3.upper()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_3}', {variant_row[0][1].strip()} {Cat_name_1.upper()} is {pre_symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}'?"
            Answer_Code = Bayesian_template_code(L, Cat_name_1, Cat_Operator_1, Cat_Values_1, Num_name_1, Num_Operator_1, Num_val_1, Cat_name_3, Cat_Operator_2, Cat_Values_3)

        elif choice == 3:
          if (Cat_name_1 == Cat_name_2):
            # not valid question because of overlaps in nums and cat choices.
            return ["", ""]
          else:
            if variant_row[1] == 0:
                Question = f"{variant_row[0][0].strip()} the {Num_name_1.upper()} being {pre_symbol_text_dictionary[Num_Operator_1]} {Num_val_1}, {variant_row[0][1].strip()} {Cat_name_1.upper()} {symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}' and {Cat_name_2.upper()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_2}'?"
            else:
                Question = f"{variant_row[0][0].strip()} {Cat_name_1.upper()} {symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}' and {Cat_name_2.upper()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_2}', {variant_row[0][1].strip()} the {Num_name_1.upper()} is {pre_symbol_text_dictionary[Num_Operator_1]} {Num_val_1}?"
            Answer_Code = Bayesian_template_code(L, Num_name_1, Num_Operator_1, Num_val_1, Cat_name_1, Cat_Operator_1, Cat_Values_1, Cat_name_2, Cat_Operator_2, Cat_Values_2)
        
        elif choice == 4 and Num_name_1!=Num_name_2:
            if variant_row[1] == 0:
                Question = f"{variant_row[0][0].strip()} the {Num_name_1.upper()} being {pre_symbol_text_dictionary[Num_Operator_1]} {Num_val_1}, {variant_row[0][1].strip()} the {Num_name_2.upper()} {symbol_text_dictionary[Num_Operator_2]} {Num_val_2} and {Cat_name_3.upper()} {symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_3}'?"
            else:
                Question = f"{variant_row[0][0].strip()} the {Num_name_2.upper()} {symbol_text_dictionary[Num_Operator_2]} {Num_val_2} and {Cat_name_3.upper()} {symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_3}', {variant_row[0][1].strip()} the {Num_name_1.upper()} is {pre_symbol_text_dictionary[Num_Operator_1]} {Num_val_1}?"
            Answer_Code = Bayesian_template_code(L, Num_name_1, Num_Operator_1, Num_val_1, Num_name_2, Num_Operator_2, Num_val_2, Cat_name_3, Cat_Operator_1, Cat_Values_3)
        
        elif choice == 5 and not onenumcol and Num_name_1!=Num_name_2 and Num_name_3!=Num_name_2 and Num_name_1!=Num_name_3:
            if variant_row[1] == 0:
                Question = f"{variant_row[0][0].strip()} the {Num_name_1.upper()} being {pre_symbol_text_dictionary[Num_Operator_1]} {Num_val_1}, {variant_row[0][1].strip()} the {Num_name_2.upper()} {symbol_text_dictionary[Num_Operator_2]} {Num_val_2} and the {Num_name_3.upper()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_3}?"
            else:
                Question = f"{variant_row[0][0].strip()} the {Num_name_2.upper()} {symbol_text_dictionary[Num_Operator_2]} {Num_val_2} and the {Num_name_3.upper()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_3}, {variant_row[0][1].strip()} the {Num_name_1.upper()} is {pre_symbol_text_dictionary[Num_Operator_1]} {Num_val_1}?"
            Answer_Code = Bayesian_template_code(L, Num_name_1, Num_Operator_1, Num_val_1, Num_name_2, Num_Operator_2, Num_val_2, Num_name_3, Num_Operator_1, Num_val_3)
        
        else:
          if Num_name_2!=Num_name_3:
                if variant_row[1] == 0:
                    Question = f"{variant_row[0][0].strip()} {Cat_name_1.upper()} being {pre_symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}', {variant_row[0][1].strip()} the {Num_name_2.upper()} {symbol_text_dictionary[Num_Operator_2]} {Num_val_2} and the {Num_name_3.upper()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_3}?"
                else:
                    Question = f"{variant_row[0][0].strip()} the {Num_name_2.upper()} {symbol_text_dictionary[Num_Operator_2]} {Num_val_2} and the {Num_name_3.upper()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_3}, {variant_row[0][1].strip()} {Cat_name_1.upper()} is {pre_symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}'?"
                Answer_Code = Bayesian_template_code(L, Cat_name_1, Cat_Operator_1, Cat_Values_1, Num_name_2, Num_Operator_2, Num_val_2, Num_name_3, Num_Operator_1, Num_val_3)
          else:
              Question = ""
              Answer_Code = ""

    Question_code = [Question, Answer_Code]
    return Question_code

# Template 1: Bayesian
def Bayesian_template_code(L, condition_1, operator_1, condition_value_1, condition_2, operator_2, condition_value_2, condition_3, operator_3, condition_value_3):
    condition_value_1 = "'"+condition_value_1+"'" if isinstance(condition_value_1, str) else condition_value_1
    condition_value_2 = "'"+condition_value_2+"'" if isinstance(condition_value_2, str) else condition_value_2
    condition_value_3 = "'"+condition_value_3+"'" if isinstance(condition_value_3, str) else condition_value_3
    Answer_code_py = ""
    if L == 2:
        Prior = eval(f"df[df['{condition_1}'] {operator_1} {condition_value_1}].shape[0] / len(df)")
        if Prior == 1:
          return "zero ans"
        PriorOdds = eval(f"round({Prior} / (1 - {Prior}), 2)")
        if eval(f"len(df[df['{condition_1}'] {operator_1} {condition_value_1}])") == 0:
          return "zero ans"
        TruePositive = eval(f"round(len(df[(df['{condition_2}'] {operator_2} {condition_value_2}) & (df['{condition_1}'] {operator_1} {condition_value_1})]) / len(df[(df['{condition_1}'] {operator_1} {condition_value_1})]), 2)")
        FalsePositive = eval(f"round(len(df[(df['{condition_2}'] {operator_2} {condition_value_2}) & (df['{condition_1}'] {negation_dictionary[operator_1]} {condition_value_1})]) / len(df[(df['{condition_1}'] {negation_dictionary[operator_1]} {condition_value_1})]), 2)")
        if TruePositive == 0 or FalsePositive == 0:
          return "zero ans"
        LikelihoodRatio = eval(f"round({TruePositive} / {FalsePositive}, 2)")
        PosteriorOdds = eval(f"{LikelihoodRatio} * {PriorOdds}")
        Posterior = eval(f"{PosteriorOdds} / (1 + {PosteriorOdds})")
        Answer_code_py = round(Posterior, 2)

        Answer_code_R = f"# belief : {condition_1} {operator_1} {condition_value_1}; # observation : {condition_2} {operator_2} {condition_value_2};"
        Answer_code_R += f"Prior<-nrow(df[df${condition_1} {operator_1} {condition_value_1}, ])/nrow(df); cat('Prior is equal to:', Prior);"
        Answer_code_R += f"PriorOdds<-round(Prior/(1-Prior), 2); cat('Prior Odds are equal to:', PriorOdds);"
        Answer_code_R += f"TruePositive<-round(nrow(df[df${condition_2} {operator_2} {condition_value_2} & df${condition_1} {operator_1} {condition_value_1}, ])/nrow(df[df${condition_1} {operator_1} {condition_value_1}, ]), 2); cat('TruePositive is equal to:', TruePositive);"
        Answer_code_R += f"FalsePositive<-round(nrow(df[df${condition_2} {operator_2} {condition_value_2} & df${condition_1} {negation_dictionary[operator_1]} {condition_value_1}, ])/nrow(df[df${condition_1} {negation_dictionary[operator_1]} {condition_value_1}, ]), 2); cat('FalsePositive is equal to:', FalsePositive);"
        Answer_code_R += f"LikelihoodRatio<-round(TruePositive/FalsePositive,2); cat('LikelihoodRatio is equal to:', LikelihoodRatio);"
        Answer_code_R += f"PosteriorOdds <-LikelihoodRatio * PriorOdds; cat('Posterior Odds are equal to:', PosteriorOdds);"
        Answer_code_R += f"Posterior <- round(PosteriorOdds/(1+PosteriorOdds), 2); cat('Posterior is equal to:', Posterior); "

    elif L == 3:
        Prior = eval(f"df[df['{condition_1}'] {operator_1} {condition_value_1}].shape[0] / len(df)")
        if Prior == 1:
          return "zero ans"
        PriorOdds = eval(f"round({Prior} / (1 - {Prior}), 2)")
        if eval(f"len(df[df['{condition_1}'] {operator_1} {condition_value_1}])") == 0:
          return "zero ans"
        TruePositive = eval(f"round(len(df[(df['{condition_2}'] {operator_2} {condition_value_2}) & (df['{condition_1}'] {operator_1} {condition_value_1}) & (df['{condition_3}'] {operator_3} {condition_value_3})]) / len(df[(df['{condition_1}'] {operator_1} {condition_value_1})]), 2)")
        FalsePositive = eval(f"round(len(df[(df['{condition_2}'] {operator_2} {condition_value_2}) & (df['{condition_1}'] {negation_dictionary[operator_1]} {condition_value_1}) & (df['{condition_3}'] {operator_3} {condition_value_3})]) / len(df[(df['{condition_1}'] {negation_dictionary[operator_1]} {condition_value_1})]), 2)")
        if TruePositive == 0 or FalsePositive == 0:
          return "zero ans"
        LikelihoodRatio = eval(f"round({TruePositive} / {FalsePositive}, 2)")
        PosteriorOdds = eval(f"{LikelihoodRatio} * {PriorOdds}")
        Posterior = eval(f"{PosteriorOdds} / (1 + {PosteriorOdds})")
        Answer_code_py = round(Posterior, 2)

        Answer_code_R = f"# belief : {condition_1} {operator_1} {condition_value_1}; # observation : {condition_2} {operator_2} {condition_value_2} , {condition_3} {operator_3} {condition_value_3};"
        Answer_code_R += f"Prior<-nrow(df[df${condition_1} {operator_1} {condition_value_1}, ])/nrow(df); cat('Prior is equal to:', Prior);"
        Answer_code_R += f"PriorOdds<-round(Prior/(1-Prior), 2); cat('Prior Odds are equal to:', PriorOdds);"
        Answer_code_R += f"TruePositive<-round(nrow(df[df${condition_2} {operator_2} {condition_value_2} & df${condition_1} {operator_1} {condition_value_1} & df${condition_3} {operator_3} {condition_value_3}, ])/nrow(df[df${condition_1} {operator_1} {condition_value_1}, ]), 2); cat('TruePositive is equal to:', TruePositive);"
        Answer_code_R += f"FalsePositive<-round(nrow(df[df${condition_2} {operator_2} {condition_value_2} & df${condition_1} {negation_dictionary[operator_1]} {condition_value_1}  & df${condition_3} {operator_3} {condition_value_3}, ])/nrow(df[df${condition_1} {negation_dictionary[operator_1]} {condition_value_1}, ]), 2); cat('FalsePositive is equal to:', FalsePositive);"
        Answer_code_R += f"LikelihoodRatio<-round(TruePositive/FalsePositive,2); cat('LikelihoodRatio is equal to:', LikelihoodRatio);"
        Answer_code_R += f"PosteriorOdds <-LikelihoodRatio * PriorOdds; cat('Posterior Odds are equal to:', PosteriorOdds);"
        Answer_code_R += f"Posterior <- round(PosteriorOdds/(1+PosteriorOdds), 2); cat('Posterior is equal to:', Posterior);"

    Answer_py = Answer_code_py
    return [Answer_code_R, Answer_py]


def getBayesianQuestions(question_no_split, df, Categorical_Columns, Numerical_Columns, dataset_name, onenumcol, Bayesian_Variants):
    Num_Operator = ["<", "<=", ">=", ">"]
    numops_below_25 = ["<", "<="]
    numops_25_75 = Num_Operator
    numops_above_75 = [">=", ">"]
    Cat_Operator = ["==", "!="]
    Ques_Ans = []
    duplicate_question_check = set()
    count = 0
    while(count < question_no_split):

        Cat_name_1 = random.choice(Categorical_Columns)
        Unique_Cat_Values_1 = df[Cat_name_1].unique()
        Cat_Values_1 = random.choice(Unique_Cat_Values_1)

        Cat_name_2 = random.choice(Categorical_Columns)
        Unique_Cat_Values_2 = df[Cat_name_2].unique()
        Cat_Values_2 = random.choice(Unique_Cat_Values_2)

        Cat_name_3 = random.choice(Categorical_Columns)
        Unique_Cat_Values_3 = df[Cat_name_3].unique()
        Cat_Values_3 = random.choice(Unique_Cat_Values_3)

        Cat_Operator_1 = random.choice(Cat_Operator)
        Cat_Operator_2 = random.choice(Cat_Operator)

        if "'" in Cat_Values_1 or "'" in Cat_Values_2 or "'" in Cat_Values_3:
            continue

        # here check if selected numval1 and 2 are at extremes then dont send invalid operators.
        Num_name_1 = random.choice(Numerical_Columns)
        value1 = min(df[Num_name_1])
        value2 = max(df[Num_name_1])
        Num_val_1 = round(random.uniform(1.1*value1, 0.9*value2), 2)

        intval_1 = int(Num_val_1)
        Num_val_1 = intval_1
        if intval_1 < value1:
            Num_val_1 = math.ceil(intval_1) 
        if Num_val_1 > value2:
            Num_val_1 = math.floor(intval_1) 

        diff = value2 - value1
        if Num_val_1 < (0.25 * diff):
            Num_Operator_1  = random.choice(numops_below_25) 
        elif Num_val_1 <= (0.75  * diff):
            Num_Operator_1 = random.choice(numops_25_75)
        elif Num_val_1 > (0.75 * diff):
            Num_Operator_1 = random.choice(numops_above_75)


        Num_name_2 = random.choice(Numerical_Columns)
        value1 = min(df[Num_name_2])
        value2 = max(df[Num_name_2])
        Num_val_2 = round(random.uniform(1.1*value1, 0.9*value2), 2)

        intval_2 = int(Num_val_2)
        Num_val_2 = intval_2
        if intval_2 < value1:
            Num_val_2 = math.ceil(intval_2) 
        if Num_val_2 > value2:
            Num_val_2 = math.floor(intval_2) 

        diff = value2 - value1
        if Num_val_2 < (0.25 * diff):
            Num_Operator_2  = random.choice(numops_below_25) 
        elif Num_val_2 <= (0.75  * diff):
            Num_Operator_2 = random.choice(numops_25_75)
        elif Num_val_2 > (0.75 * diff):
            Num_Operator_2 = random.choice(numops_above_75)


        Num_name_3 = random.choice(Numerical_Columns)
        value1 = int(min(df[Num_name_3]))
        value2 = int(max(df[Num_name_3]))
        Num_val_3 = random.randint(value1, value2)

        Type = "Bayesian Question"

        L = random.choice(range(2, 4))

        variant_row = random.choice(Bayesian_Variants)
        Generated_Question = Bayesian_template(dataset_name, L, Cat_name_1, Cat_name_2, Cat_name_3, Cat_Values_1,
                                            Cat_Values_2, Cat_Values_3, Cat_Operator_1, Cat_Operator_2, Num_name_1,
                                            Num_name_2, Num_name_3, Num_val_1, Num_val_2, Num_val_3, Num_Operator_1,
                                            Num_Operator_2, onenumcol, variant_row)

        if Generated_Question[0] == "" or  Generated_Question[1] == "zero ans" or Generated_Question[0] in duplicate_question_check :
            continue
        if Generated_Question[1][1] == 0:
            continue
        else:
            Generated_Answer =  Generated_Question[1][1]
            duplicate_question_check.add(Generated_Question[0])
            count += 1

        Ques_Ans.append([Type, Generated_Question[0], Generated_Answer, Generated_Question[1][0], dataset_name.upper(), str(datetime.now().date())])
    return Ques_Ans


def Probability_template_code(L, condition_1, operator_1, condition_value_1, condition_2, operator_2, condition_value_2, condition_3, operator_3, condition_value_3):
    condition_value_1 = "'"+condition_value_1+"'" if isinstance(condition_value_1, str) else condition_value_1
    condition_value_2 = "'"+condition_value_2+"'" if isinstance(condition_value_2, str) else condition_value_2
    condition_value_3 = "'"+condition_value_3+"'" if isinstance(condition_value_3, str) else condition_value_3
    Answer_code_py = ""

    if L == 1:
        Answer_code_py = round(eval(f"df[(df['{condition_1}'] {operator_1} {condition_value_1})].shape[0] / len(df)"), 2)
        if Answer_code_py == 0:
          return "zero ans"
        Answer_code_R = f"prob <-nrow(df[df${condition_1} {operator_1} {condition_value_1} , ]) / nrow(df); round(prob, 2);"

    if L == 2:
        if checkEmptyRow(f"len(df[(df['{condition_2}'] {operator_2} {condition_value_2})])"):
            return "zero ans"
        Answer_code_py = round(eval(f"df[(df['{condition_1}'] {operator_1} {condition_value_1}) & (df['{condition_2}'] {operator_2} {condition_value_2})].shape[0] / len(df[(df['{condition_2}'] {operator_2} {condition_value_2})])"), 2)
        if Answer_code_py == 0:
          return "zero ans"
        Answer_code_R = f"prob <-nrow(df[df${condition_1} {operator_1} {condition_value_1} & df${condition_2} {operator_2} {condition_value_2}, ]) / nrow(df[df${condition_2} {operator_2} {condition_value_2}, ]); round(prob, 2);"

    elif L == 3:
        if checkEmptyRow(f"len(df[(df['{condition_2}'] {operator_2} {condition_value_2}) & (df['{condition_3}'] {operator_3} {condition_value_3})])"):
            return "zero ans"
        Answer_code_py = round(eval(f"df[(df['{condition_1}'] {operator_1} {condition_value_1}) & (df['{condition_2}'] {operator_2} {condition_value_2}) & (df['{condition_3}'] {operator_3} {condition_value_3})].shape[0] / len(df[(df['{condition_2}'] {operator_2} {condition_value_2}) & (df['{condition_3}'] {operator_3} {condition_value_3})])"), 2)
        if Answer_code_py == 0:
          return "zero ans"
        Answer_code_R = f"prob <-nrow(df[df${condition_1} {operator_1} {condition_value_1} & df${condition_2} {operator_2} {condition_value_2} & df${condition_3} {operator_3} {condition_value_3}, ]) / nrow(df[df${condition_2} {operator_2} {condition_value_2} & df${condition_3} {operator_3} {condition_value_3}, ]); round(prob, 2);"

    Answer_py = Answer_code_py
    return [Answer_code_R, Answer_py]

#Template 5 Probability
def Probability_template(dataset_name, L, cat_name_1, cat_name_2, cat_name_3, cat_values_1, cat_values_2, cat_values_3, cat_operator_1, cat_operator_2, num_name_1, num_name_2, num_name_3, num_val_1, num_val_2, num_val_3, num_operator_1, num_operator_2):
    Question = "" 
    Answer_Code = "" 
    if L == 1:
        random_num = random.randint(1, 2)
        if random_num == 1:
            Question = f"What is the probability that {cat_name_1.upper()} {symbol_text_dictionary[cat_operator_1]} '{cat_values_1}'?"
            Answer_Code = Probability_template_code(L, cat_name_1, cat_operator_1, cat_values_1, "0", "0", "0", "0", "0", "0")
        else:
            Question = f"What is the probability that {num_name_1.upper()} {symbol_text_dictionary[num_operator_1]} {num_val_1}?"
            Answer_Code = Probability_template_code(L, num_name_1, num_operator_1, num_val_1, "0", "0", "0", "0", "0", "0")
    elif L == 2:
        random_num = random.randint(1, 4)
        if random_num == 1 and cat_name_1!=cat_name_2:
            Question = f"What is the probability that {cat_name_1.upper()} {symbol_text_dictionary[cat_operator_1]} '{cat_values_1}', where {cat_name_2.upper()} {symbol_text_dictionary[cat_operator_2]} '{cat_values_2}'?"
            Answer_Code = Probability_template_code(L, cat_name_1, cat_operator_1, cat_values_1, cat_name_2, cat_operator_2, cat_values_2, "0", "0", "0")
        elif random_num == 2:
            Question = f"What is the probability that {cat_name_1.upper()} {symbol_text_dictionary[cat_operator_1]} '{cat_values_1}', where {num_name_1.upper()} {symbol_text_dictionary[num_operator_1]} {num_val_1}?"
            Answer_Code = Probability_template_code(L, cat_name_1, cat_operator_1, cat_values_1, num_name_1, num_operator_1, num_val_1, "0", "0", "0")
        elif random_num == 3:
            Question = f"What is the probability that {num_name_1.upper()} {symbol_text_dictionary[num_operator_1]} {num_val_1}, where {cat_name_1.upper()} {symbol_text_dictionary[cat_operator_1]} '{cat_values_1}'?"
            Answer_Code = Probability_template_code(L, num_name_1, num_operator_1, num_val_1, cat_name_1, cat_operator_1, cat_values_1, "0", "0", "0")
        elif num_name_1!=num_name_2:
            Question = f"What is the probability that {num_name_1.upper()} {symbol_text_dictionary[num_operator_1]} {num_val_1}, where {num_name_2.upper()} {symbol_text_dictionary[num_operator_2]} {num_val_2}?"
            Answer_Code = Probability_template_code(L, num_name_1, num_operator_1, num_val_1, num_name_2, num_operator_2, num_val_2, "0", "0", "0")
    elif L == 3:
        random_num = random.randint(2, 4)
        if random_num == 2:
          if cat_name_3 != cat_name_1:
            Question = f"What is the probability that {cat_name_1.upper()} {symbol_text_dictionary[cat_operator_1]} '{cat_values_1}', where {num_name_1.upper()} {symbol_text_dictionary[num_operator_1]} {num_val_1} and {cat_name_3.upper()} {symbol_text_dictionary[cat_operator_1]} '{cat_values_3}'?"
            Answer_Code = Probability_template_code(L, cat_name_1, cat_operator_1, cat_values_1, num_name_1, num_operator_1, num_val_1, cat_name_3, cat_operator_1, cat_values_3)
          else:
            # not valid question because of overlaps in nums and cat choices.
            return ["", ""]
        elif random_num == 3:
          if cat_name_2 != cat_name_1:
            Question = f"What is the probability that {num_name_1.upper()} {symbol_text_dictionary[num_operator_1]} {num_val_1}, where {cat_name_1.upper()} {symbol_text_dictionary[cat_operator_1]} '{cat_values_1}' and {cat_name_2.upper()} {symbol_text_dictionary[cat_operator_2]} '{cat_values_2}'?"
            Answer_Code = Probability_template_code(L, num_name_1, num_operator_1, num_val_1, cat_name_1, cat_operator_1, cat_values_1, cat_name_2, cat_operator_2, cat_values_2)
          else:
            # not valid question because of overlaps in nums and cat choices.
            return ["", ""]
        elif random_num == 4:
          if cat_name_2 != cat_name_1 and cat_name_1!=cat_name_3 and cat_name_1!=cat_name_2:
            Question = f"What is the probability that {cat_name_1.upper()} {symbol_text_dictionary[cat_operator_1]} '{cat_values_1}', where {cat_name_3.upper()} {symbol_text_dictionary[cat_operator_1]} '{cat_values_3}' and {cat_name_2.upper()} {symbol_text_dictionary[cat_operator_2]} '{cat_values_2}'?"
            Answer_Code = Probability_template_code(L, cat_name_1, cat_operator_1, cat_values_1, cat_name_3, cat_operator_1, cat_values_3, cat_name_2, cat_operator_2, cat_values_2)
          else:
            # not valid question because of overlaps in nums and cat choices.
            return ["", ""]
        else:
          # not valid question because of overlaps in nums and cat choices.
          return ["", ""]

    Question_code = [Question, Answer_Code]
    return Question_code


def getProbabilityQuestions(question_no_split, df, Categorical_Columns, Numerical_Columns, dataset_name, onenumcol):
    Num_Operator = ["<", "<=", ">=", ">"]
    numops_below_25 = ["<", "<="]
    numops_25_75 = Num_Operator
    numops_above_75 = [">=", ">"]

    Cat_Operator = ["==", "!="]
    Ques_Ans = []
    duplicate_question_check = set()
    count = 0
    while(count < question_no_split):
        # Category
        Cat_name_1 = random.choice(Categorical_Columns)
        Unique_Cat_Values_1 = df[Cat_name_1].unique()
        Cat_Values_1 = random.choice(Unique_Cat_Values_1)

        Cat_name_2 = random.choice(Categorical_Columns)
        Unique_Cat_Values_2 = df[Cat_name_2].unique()
        Cat_Values_2 = random.choice(Unique_Cat_Values_2)

        Cat_name_3 = random.choice(Categorical_Columns)
        Unique_Cat_Values_3 = df[Cat_name_3].unique()
        Cat_Values_3 = random.choice(Unique_Cat_Values_3)

        if "'" in Cat_Values_1 or "'" in Cat_Values_2 or "'" in Cat_Values_3:
            continue

        Cat_Operator_1 = random.choice(Cat_Operator)
        Cat_Operator_2 = random.choice(Cat_Operator)

        Num_name_1 = random.choice(Numerical_Columns)
        value1 = min(df[Num_name_1])
        value2 = max(df[Num_name_1])
        Num_val_1 = round(random.uniform(1.1*value1, 0.9*value2), 2)

        intval_1 = int(Num_val_1)
        Num_val_1 = intval_1
        if intval_1 < value1:
            Num_val_1 = math.ceil(intval_1) 
        if Num_val_1 > value2:
            Num_val_1 = math.floor(intval_1) 

        diff = value2 - value1
        if Num_val_1 < (0.25 * diff):
            Num_Operator_1  = random.choice(numops_below_25) 
        elif Num_val_1 <= (0.75  * diff):
            Num_Operator_1 = random.choice(numops_25_75)
        elif Num_val_1 > (0.75 * diff):
            Num_Operator_1 = random.choice(numops_above_75)


        Num_name_2 = random.choice(Numerical_Columns)
        value1 = min(df[Num_name_2])
        value2 = max(df[Num_name_2])
        Num_val_2 = round(random.uniform(1.1*value1, 0.9*value2), 2)

        intval_2 = int(Num_val_2)
        Num_val_2 = intval_2
        if intval_2 < value1:
            Num_val_2 = math.ceil(intval_2) 
        if Num_val_2 > value2:
            Num_val_2 = math.floor(intval_2) 

        diff = value2 - value1
        if Num_val_2 < (0.25 * diff):
            Num_Operator_2  = random.choice(numops_below_25) 
        elif Num_val_2 <= (0.75  * diff):
            Num_Operator_2 = random.choice(numops_25_75)
        elif Num_val_2 > (0.75 * diff):
            Num_Operator_2 = random.choice(numops_above_75)


        Num_name_3 = random.choice(Numerical_Columns)
        value1 = int(min(df[Num_name_3]))
        value2 = int(max(df[Num_name_3]))
        Num_val_3 = random.randint(value1, value2)

        Type = "Probability Question"
        L = random.choice(range(1, 4))

        Generated_Question = Probability_template(dataset_name, L, Cat_name_1, Cat_name_2, Cat_name_3, Cat_Values_1,
                                                Cat_Values_2, Cat_Values_3, Cat_Operator_1, Cat_Operator_2, Num_name_1, Num_name_2,
                                                Num_name_3, Num_val_1, Num_val_2, Num_val_3, Num_Operator_1, Num_Operator_2)

        if Generated_Question[0] == "" or  Generated_Question[1] == "zero ans" or Generated_Question[0] in duplicate_question_check :
            continue
        elif Generated_Question[1][1] == 0:
            continue
        else:
            Generated_Answer =  Generated_Question[1][1]
            duplicate_question_check.add(Generated_Question[0])
            count += 1
    
        Ques_Ans.append([Type, Generated_Question[0], Generated_Answer, Generated_Question[1][0], dataset_name.upper(), str(datetime.now().date())])
    return Ques_Ans

def Hypothesis_template_code(L, num_name_2, cat_name_1, cat_values_1, cat_values_1_2, condition_1, operator_1, condition_value_1, condition_2, operator_2, condition_value_2):
    condition_value_1 = "'"+condition_value_1+"'" if isinstance(condition_value_1, str) else condition_value_1
    condition_value_2 = "'"+condition_value_2+"'" if isinstance(condition_value_2, str) else condition_value_2
    
    Answer_code_py = "Run the code by clicking the solution button and checking. If the output is lesser than 0.05 (customary significance level of 5%) then we reject the null hypothesis mentioned in the solution.R window, else we fail to reject the null hypothesis."
    Answer_code_R = ""
    
    if L == 1:
        Answer_code_R = f"# Null Hypothesis : The average {num_name_2.upper()} is the same when {cat_name_1.upper()} = '{cat_values_1}' and when {cat_name_1.upper()} = '{cat_values_1_2}';"
        Answer_code_R += f"permutation_test(df, '{cat_name_1}', '{num_name_2}', 10000, '{cat_values_1}', '{cat_values_1_2}');"
    if L == 2:
        ##print("here - 02")
        query = f"len(df[(df['{condition_1}'] {operator_1} {condition_value_1}) & (df['{cat_name_1}'] == '{cat_values_1}')])"
        if checkEmptyRow(query):
            #print("here - 12")
            return "zero ans"
        query = f"len(df[(df['{condition_1}'] {operator_1} {condition_value_1}) & (df['{cat_name_1}'] == '{cat_values_1_2}')])"
        if checkEmptyRow(query):
            #print("here - 22")
            return "zero ans"
        Answer_code_R = f"# Null Hypothesis : The average {num_name_2.upper()} is the same when {cat_name_1.upper()} = '{cat_values_1}' and when {cat_name_1.upper()} = '{cat_values_1_2}';"
        Answer_code_R += f"df <- df[df${condition_1} {operator_1} {condition_value_1}, ];"
        Answer_code_R += f"mean(df[df${cat_name_1} == '{cat_values_1}', ]${num_name_2}); mean(df[df${cat_name_1} == '{cat_values_1_2}', ]${num_name_2});"
        Answer_code_R += f"permutation_test(df, '{cat_name_1}', '{num_name_2}', 10000, '{cat_values_1}', '{cat_values_1_2}');"
    if L == 3:
        #print("here - 03")
        query = f"len(df[(df['{condition_1}'] {operator_1} {condition_value_1}) & (df['{condition_2}'] {operator_2} {condition_value_2}) & (df['{cat_name_1}'] == '{cat_values_1}')])"
        if checkEmptyRow(query):
            #print("here - 13")
            return "zero ans"
        query = f"len(df[(df['{condition_1}'] {operator_1} {condition_value_1}) & (df['{condition_2}'] {operator_2} {condition_value_2}) & (df['{cat_name_1}'] == '{cat_values_1_2}')])"
        if checkEmptyRow(query):
            #print("here - 23")
            return "zero ans"
        Answer_code_R = f"# Null Hypothesis : The average {num_name_2.upper()} is the same when {cat_name_1.upper()} = '{cat_values_1}' and when {cat_name_1.upper()} = '{cat_values_1_2}';"
        Answer_code_R += f"df <- df[df${condition_1} {operator_1} {condition_value_1} & df${condition_2} {operator_2} {condition_value_2}, ];"
        Answer_code_R += f"mean(df[df${cat_name_1} == '{cat_values_1}', ]${num_name_2}); mean(df[df${cat_name_1} == '{cat_values_1_2}', ]${num_name_2});"
        Answer_code_R += f"permutation_test(df, '{cat_name_1}', '{num_name_2}', 10000, '{cat_values_1}', '{cat_values_1_2}');"
    
    Answer_code = [Answer_code_R, Answer_code_py]
    return Answer_code

def Hypothesis_template(L, dataset_name, Cat_name_1, Cat_Values_1, Cat_Values_1_2, Num_name_2, Cat_name_2, Cat_Operator_2, Cat_Values_2, Cat_name_3, Cat_Operator_3, Cat_Values_3, Num_name_1, Num_val_1, Num_Operator_1, onenumcol, variant_row):
    Question = ""
    Answer_Code = ["", ""]
    
    if L == 1:
        random_num = random.randint(1, 4)
        if random_num == 1:
            Question =  f"Verify hypothesis that the average {Num_name_2.upper()} is higher when {Cat_name_1.upper()} is equal to '{Cat_Values_1}' than when {Cat_name_1.upper()} is equal to '{Cat_Values_1_2}'"
        else:
            Question =  f"Test the hypothesis that the average {Num_name_2.upper()} is higher when {Cat_name_1.upper()} is equal to '{Cat_Values_1}' than when {Cat_name_1.upper()} is equal to '{Cat_Values_1_2}'"
        Answer_Code = Hypothesis_template_code(L, Num_name_2, Cat_name_1, Cat_Values_1, Cat_Values_1_2, "0", "0", "0", "0", "0", "0")        
    elif L == 2:
        random_num = random.randint(1, 3)
        if random_num == 1 and Num_name_2!=Num_name_1:
            if variant_row[1] == 0: 
                Question =  f"{variant_row[0][0]} the average {Num_name_2.upper()} is higher when {Cat_name_1.upper()} is equal to '{Cat_Values_1}' than when {Cat_name_1.upper()} is equal to '{Cat_Values_1_2}', {variant_row[0][1]} the {Num_name_1.upper()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_1}"
            else:
                Question =  f"{variant_row[0][0]} the {Num_name_1.upper()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_1}, {variant_row[0][1]} the average {Num_name_2.upper()} is higher when {Cat_name_1.upper()} is equal to '{Cat_Values_1}' than when {Cat_name_1.upper()} is equal to '{Cat_Values_1_2}'"
            ans = Hypothesis_template_code(L, Num_name_2, Cat_name_1, Cat_Values_1, Cat_Values_1_2, Num_name_1, Num_Operator_1, Num_val_1, "0", "0", "0")        
            Answer_Code = "zero ans" if ans == "zero ans" else ans
        elif random_num == 2 and Cat_name_2!=Cat_name_1:
            if variant_row[1] == 0: 
                Question =  f"{variant_row[0][0]} the average {Num_name_2.upper()} is higher when {Cat_name_1.upper()} is equal to '{Cat_Values_1}' than when {Cat_name_1.upper()} is equal to '{Cat_Values_1_2}', {variant_row[0][1]} {Cat_name_2.upper()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_2}'"
            else:
                Question =  f"{variant_row[0][0]} {Cat_name_2.upper()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_2}', {variant_row[0][1]} the average {Num_name_2.upper()} is higher when {Cat_name_1.upper()} is equal to '{Cat_Values_1}' than when {Cat_name_1.upper()} is equal to '{Cat_Values_1_2}'"
            ans = Hypothesis_template_code(L, Num_name_2, Cat_name_1, Cat_Values_1, Cat_Values_1_2, Cat_name_2, Cat_Operator_2, Cat_Values_2, "0", "0", "0")        
            Answer_Code = "zero ans" if ans == "zero ans" else ans
    elif L == 3: 
        if Num_name_2!=Num_name_1 and Cat_name_2!=Cat_name_1:
            if variant_row[1] == 0: 
                Question =  f"{variant_row[0][0]} the average {Num_name_2.upper()} is higher when {Cat_name_1.upper()} is equal to '{Cat_Values_1}' than when {Cat_name_1.upper()} is equal to '{Cat_Values_1_2}', {variant_row[0][1]} the {Num_name_1.upper()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_1} and {Cat_name_2.upper()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_2}'"
            else:
                Question =  f"{variant_row[0][0]} the {Num_name_1.upper()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_1} and {Cat_name_2.upper()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_2}', {variant_row[0][1]} the average {Num_name_2.upper()} is higher when {Cat_name_1.upper()} is equal to '{Cat_Values_1}' than when {Cat_name_1.upper()} is equal to '{Cat_Values_1_2}'"
            ans = Hypothesis_template_code(L, Num_name_2, Cat_name_1, Cat_Values_1, Cat_Values_1_2, Num_name_1, Num_Operator_1, Num_val_1, Cat_name_2, Cat_Operator_2, Cat_Values_2)        
            Answer_Code = "zero ans" if ans == "zero ans" else ans
        
    return [Question, Answer_Code]

def getHypothesisQuestions(question_no_split, df, Categorical_Columns, Numerical_Columns, dataset_name, onenumcol, Hypothesis_Variants):
    Num_Operator = ["<", "<=", ">=", ">"]
    numops_below_25 = ["<", "<="]
    numops_25_75 = Num_Operator
    numops_above_75 = [">=", ">"]
    Cat_Operator = ["==", "!="]
    Ques_Ans = []
    duplicate_question_check = set()
    count = 0
    while(count < question_no_split):
        # Category
        Cat_name_1 = random.choice(Categorical_Columns)
        Unique_Cat_Values_1 = df[Cat_name_1].unique()
        Cat_Values_1 = random.choice(Unique_Cat_Values_1)
        Cat_Values_1_2 = random.choice(Unique_Cat_Values_1)
        while(Cat_Values_1_2 == Cat_Values_1):
            Cat_Values_1_2 = random.choice(Unique_Cat_Values_1)

        Cat_name_2 = random.choice(Categorical_Columns)
        Unique_Cat_Values_2 = df[Cat_name_2].unique()
        Cat_Values_2 = random.choice(Unique_Cat_Values_2)

        Cat_name_3 = random.choice(Categorical_Columns)
        Unique_Cat_Values_3 = df[Cat_name_3].unique()
        Cat_Values_3 = random.choice(Unique_Cat_Values_3)

        Cat_Operator_2 = random.choice(Cat_Operator)
        Cat_Operator_3 = random.choice(Cat_Operator)
                
        if "'" in Cat_Values_1 or "'" in Cat_Values_1_2 or "'" in Cat_Values_2 or "'" in Cat_Values_3:
            continue

        # here check if selected numval1 and 2 are at extremes then dont send invalid operators.
        Num_name_1 = random.choice(Numerical_Columns)
        value1 = min(df[Num_name_1])
        value2 = max(df[Num_name_1])
        Num_val_1 = round(random.uniform(1.1*value1, 0.9*value2), 2)

        intval_1 = int(Num_val_1)
        Num_val_1 = intval_1
        if intval_1 < value1:
            Num_val_1 = math.ceil(intval_1) 
        if Num_val_1 > value2:
            Num_val_1 = math.floor(intval_1) 

        diff = value2 - value1
        if Num_val_1 < (0.25 * diff):
            Num_Operator_1  = random.choice(numops_below_25) 
        elif Num_val_1 <= (0.75  * diff):
            Num_Operator_1 = random.choice(numops_25_75)
        elif Num_val_1 > (0.75 * diff):
            Num_Operator_1 = random.choice(numops_above_75)

        Num_name_2 = random.choice(Numerical_Columns)

        Type = "Hypothesis Question"
        L = random.choice(range(1, 4))
        variant_row = random.choice(Hypothesis_Variants)

        Generated_Question = Hypothesis_template(L, dataset_name, Cat_name_1, Cat_Values_1, Cat_Values_1_2, Num_name_2,
                                                 Cat_name_2, Cat_Operator_2, Cat_Values_2, 
                                                 Cat_name_3, Cat_Operator_3, Cat_Values_3,
                                                 Num_name_1, Num_val_1, Num_Operator_1, onenumcol, variant_row)

        if Generated_Question[0] == "" or Generated_Question[1] == "zero ans" or Generated_Question[0] in duplicate_question_check :
            continue
        if Generated_Question[1][1] == 0:
            continue
        else:
            Generated_Answer =  Generated_Question[1][1]
            duplicate_question_check.add(Generated_Question[0])
            count += 1

        Ques_Ans.append([Type, Generated_Question[0], Generated_Answer, Generated_Question[1][0], dataset_name.upper(), str(datetime.now().date())])
    return Ques_Ans


# Template 2: General Min, Max, and Mean
def Distribution_template_code(index, L, Cat_name_1, condition_1, operator_1, condition_value_1, condition_2, operator_2, condition_value_2):
    condition_value_1 = "'"+condition_value_1+"'" if isinstance(condition_value_1, str) else condition_value_1
    condition_value_2 = "'"+condition_value_2+"'" if isinstance(condition_value_2, str) else condition_value_2
    Answer_code_py = f"Run the solution and check the distribution of values from the table (You can find the highest/lowest value from checking the table as well.)"
    if index == 0:
        if L == 1:
            Answer_code_R = f"# The distribution of values for {Cat_name_1} is ;"
            Answer_code_R += f"table(df${Cat_name_1});"

        elif L == 2:
            Answer_code_R = f"# The distribution of values for {Cat_name_1} is ;"
            Answer_code_R += f"table(df${Cat_name_1}[df${condition_1} {operator_1} {condition_value_1}]);"
        
        elif L == 3:
            Answer_code_R = f"# The distribution of values for {Cat_name_1} is ;"
            Answer_code_R += f"table(df${Cat_name_1}[df${condition_1} {operator_1} {condition_value_1} & df${condition_2} {operator_2} {condition_value_2}]);"
    else:
        if L == 1:
            Answer_code_R = f"# The distribution of values for {Cat_name_1} is ;"
            Answer_code_R += f"freqtable <- table(df${Cat_name_1});"
            Answer_code_R += f"freqtable;"
            Answer_code_R += f"most_frequent_value <- names(freqtable)[which.max(freqtable)];"
            Answer_code_R += f"paste('The most frequent value is :', most_frequent_value);"

        elif L == 2:
            Answer_code_R = f"# The distribution of values for {Cat_name_1} is ;"
            Answer_code_R += f"freqtable <- table(df${Cat_name_1}[df${condition_1} {operator_1} {condition_value_1}]);"
            Answer_code_R += f"freqtable;"
            Answer_code_R += f"most_frequent_value <- names(freqtable)[which.max(freqtable)];"
            Answer_code_R += f"paste('The most frequent value is :', most_frequent_value);"
        
        elif L == 3:
            Answer_code_R = f"# The distribution of values for {Cat_name_1} is ;"
            Answer_code_R += f"freqtable <- table(df${Cat_name_1}[df${condition_1} {operator_1} {condition_value_1} & df${condition_2} {operator_2} {condition_value_2}]);"
            Answer_code_R += f"freqtable;"
            Answer_code_R += f"most_frequent_value <- names(freqtable)[which.max(freqtable)];"
            Answer_code_R += f"paste('The most frequent value is :', most_frequent_value);"

    Answer_py = Answer_code_py
    return [Answer_code_R, Answer_py]


def Distribution_template(Dataset_name, L, Cat_name_1, Cat_name_2, Cat_name_3, Cat_Values_1, Cat_Values_2, Cat_Values_3,
                     Cat_Operator_1, Cat_Operator_2, Num_name_1, Num_name_2, Num_name_3, Num_val_1, Num_val_2, Num_val_3,
                     Num_Operator_1, Num_Operator_2, onenumcol):
    global symbol_text_dictionary
    Question = ""
    Answer_Code = ""
    choicekeyword =  ["distribution of", "most frequent value of"]
    index = random.choice(range(0, 2))
    if L == 1:
        if index == 0:
            Question = f"What is the {choicekeyword[index]} {Cat_name_1.upper()}?"
            Answer_Code = Distribution_template_code(index, L, Cat_name_1, "0", "0", "0", "0", "0", "0")
        else:
            Question = f"What is the {choicekeyword[index]} {Cat_name_1.upper()}?"
            Answer_Code = Distribution_template_code(index, L, Cat_name_1, "0", "0", "0", "0", "0", "0")

    elif L == 2:
        choice = random.choice([1, 3])
        if index == 0:
            if choice == 1 and Cat_name_1!=Cat_name_2:
                Question = f"What is the {choicekeyword[index]} {Cat_name_1.upper()}, where {Cat_name_2.upper()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_2}'?"
                Answer_Code = Distribution_template_code(index, L, Cat_name_1, Cat_name_2, Cat_Operator_2, Cat_Values_2, "0", "0", "0")
            else:
                Question = f"What is the {choicekeyword[index]} {Cat_name_1.upper()}, where {Num_name_1.upper()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_1}?"
                Answer_Code = Distribution_template_code(index, L, Cat_name_1, Num_name_1, Num_Operator_1, Num_val_1, "0", "0", "0")
        else:
            if choice == 1 and Cat_name_1!=Cat_name_2:
                Question = f"What is the {choicekeyword[index]} {Cat_name_1.upper()}, where {Cat_name_2.upper()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_2}'?"
                Answer_Code = Distribution_template_code(index, L, Cat_name_1, Cat_name_2, Cat_Operator_2, Cat_Values_2, "0", "0", "0")
            else:
                Question = f"What is the {choicekeyword[index]} {Cat_name_1.upper()}, where {Num_name_1.upper()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_1}?"
                Answer_Code = Distribution_template_code(index, L, Cat_name_1, Num_name_1, Num_Operator_1, Num_val_1, "0", "0", "0")

    elif L == 3:
        choice = random.choice([1, 2, 3, 4])
        if index == 0:
            if choice == 1 and Cat_name_1!=Cat_name_2:
                Question = f"What is the {choicekeyword[index]} {Cat_name_1.upper()}, where {Num_name_1.upper()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_1} and {Cat_name_2.upper()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_2}'?"
                Answer_Code = Distribution_template_code(index, L, Cat_name_1, Num_name_1, Num_Operator_1, Num_val_1, Cat_name_2, Cat_Operator_2, Cat_Values_2)
            elif choice == 2 and Num_name_1!=Num_name_2:
                Question = f"What is the {choicekeyword[index]} {Cat_name_1.upper()}, where {Num_name_1.upper()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_1} and {Num_name_2.upper()} {symbol_text_dictionary[Num_Operator_2]} {Num_val_2}?"
                Answer_Code = Distribution_template_code(index, L, Cat_name_1, Num_name_1, Num_Operator_1, Num_val_1, Num_name_2, Num_Operator_2, Num_val_2)
            elif choice == 3 and Cat_name_1!=Cat_name_3:
                Question = f"What is the {choicekeyword[index]} {Cat_name_1.upper()}, where {Cat_name_3.upper()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_3}' and {Num_name_2.upper()} {symbol_text_dictionary[Num_Operator_2]} {Num_val_2}?"
                Answer_Code = Distribution_template_code(index, L, Cat_name_1, Cat_name_3, Cat_Operator_2, Cat_Values_3, Num_name_2, Num_Operator_2, Num_val_2)
            else:
                if Num_name_1!=Num_name_2 and Num_name_3!=Num_name_2:
                    return ["", ""]
        else:
            if choice == 1 and Cat_name_1!=Cat_name_2:
                Question = f"What is the {choicekeyword[index]} {Cat_name_1.upper()}, where {Num_name_1.upper()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_1} and {Cat_name_2.upper()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_2}'?"
                Answer_Code = Distribution_template_code(index, L, Cat_name_1, Num_name_1, Num_Operator_1, Num_val_1, Cat_name_2, Cat_Operator_2, Cat_Values_2)
            elif choice == 2 and Num_name_1!=Num_name_2:
                Question = f"What is the {choicekeyword[index]} {Cat_name_1.upper()}, where {Num_name_1.upper()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_1} and {Num_name_2.upper()} {symbol_text_dictionary[Num_Operator_2]} {Num_val_2}?"
                Answer_Code = Distribution_template_code(index, L, Cat_name_1, Num_name_1, Num_Operator_1, Num_val_1, Num_name_2, Num_Operator_2, Num_val_2)
            elif choice == 3 and Cat_name_1!=Cat_name_3:
                Question = f"What is the {choicekeyword[index]} {Cat_name_1.upper()}, where {Cat_name_3.upper()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_3}' and {Num_name_2.upper()} {symbol_text_dictionary[Num_Operator_2]} {Num_val_2}?"
                Answer_Code = Distribution_template_code(index, L, Cat_name_1, Cat_name_3, Cat_Operator_2, Cat_Values_3, Num_name_2, Num_Operator_2, Num_val_2)
            else:
                if Num_name_1!=Num_name_2 and Num_name_3!=Num_name_2:
                    return ["", ""]

    Question_code = [Question, Answer_Code]
    return Question_code


def getDistributionQuestions(question_no_split, df, Categorical_Columns, Numerical_Columns, dataset_name, onenumcol):
    Num_Operator = ["<", "<=", ">=", ">"]
    numops_below_25 = ["<", "<="]
    numops_25_75 = Num_Operator
    numops_above_75 = [">=", ">"]

    Cat_Operator = ["==", "!="]
    Ques_Ans = []
    duplicate_question_check = set()
    count = 0
    while(count < question_no_split):
        # Category
        Cat_name_1 = random.choice(Categorical_Columns)
        Unique_Cat_Values_1 = df[Cat_name_1].unique()
        Cat_Values_1 = random.choice(Unique_Cat_Values_1)
        Cat_Values_11 = random.choice(Unique_Cat_Values_1)

        Cat_name_2 = random.choice(Categorical_Columns)
        Unique_Cat_Values_2 = df[Cat_name_2].unique()
        Cat_Values_2 = random.choice(Unique_Cat_Values_2)

        Cat_name_3 = random.choice(Categorical_Columns)
        Unique_Cat_Values_3 = df[Cat_name_3].unique()
        Cat_Values_3 = random.choice(Unique_Cat_Values_3)

        Cat_Operator_1 = random.choice(Cat_Operator)
        Cat_Operator_2 = random.choice(Cat_Operator)

        if "'" in Cat_Values_1 or "'" in Cat_Values_2 or "'" in Cat_Values_3:
            continue

        # here check if selected numval1 and 2 are at extremes then dont send invalid operators.
        Num_name_1 = random.choice(Numerical_Columns)
        value1 = min(df[Num_name_1])
        value2 = max(df[Num_name_1])
        Num_val_1 = round(random.uniform(1.1*value1, 0.9*value2), 2)

        intval_1 = int(Num_val_1)
        Num_val_1 = intval_1
        if intval_1 < value1:
            Num_val_1 = math.ceil(intval_1) 
        if Num_val_1 > value2:
            Num_val_1 = math.floor(intval_1) 

        diff = value2 - value1
        if Num_val_1 < (0.25 * diff):
            Num_Operator_1  = random.choice(numops_below_25) 
        elif Num_val_1 <= (0.75  * diff):
            Num_Operator_1 = random.choice(numops_25_75)
        elif Num_val_1 > (0.75 * diff):
            Num_Operator_1 = random.choice(numops_above_75)


        Num_name_2 = random.choice(Numerical_Columns)
        value1 = min(df[Num_name_2])
        value2 = max(df[Num_name_2])
        Num_val_2 = round(random.uniform(1.1*value1, 0.9*value2), 2)

        intval_2 = int(Num_val_2)
        Num_val_2 = intval_2
        if intval_2 < value1:
            Num_val_2 = math.ceil(intval_2) 
        if Num_val_2 > value2:
            Num_val_2 = math.floor(intval_2) 

        diff = value2 - value1
        if Num_val_2 < (0.25 * diff):
            Num_Operator_2  = random.choice(numops_below_25) 
        elif Num_val_2 <= (0.75  * diff):
            Num_Operator_2 = random.choice(numops_25_75)
        elif Num_val_2 > (0.75 * diff):
            Num_Operator_2 = random.choice(numops_above_75)


        Num_name_3 = random.choice(Numerical_Columns)
        value1 = int(min(df[Num_name_3]))
        value2 = int(max(df[Num_name_3]))
        Num_val_3 = round(random.uniform(1.15*value1, 0.85*value2), 2)
        
        Type = "Distribution Question"

        L = random.choice(range(1, 4))
        
        Generated_Question = Distribution_template(dataset_name, L, Cat_name_1, Cat_name_2, Cat_name_3, Cat_Values_1,
                                            Cat_Values_2, Cat_Values_3, Cat_Operator_1, Cat_Operator_2, Num_name_1,
                                            Num_name_2, Num_name_3, Num_val_1, Num_val_2, Num_val_3, Num_Operator_1,
                                            Num_Operator_2, onenumcol)

        if Generated_Question[0] == "" or  Generated_Question[0] in duplicate_question_check :
            continue
        duplicate_question_check.add(Generated_Question[0])
        count += 1

        Ques_Ans.append([Type, Generated_Question[0], Generated_Question[1][1], Generated_Question[1][0], dataset_name.upper(), str(datetime.now().date())])
    return Ques_Ans



@app.route('/download_csv')
def download_csv():
    csv_file_path = 'datasets/Questions.csv'
    return send_file(csv_file_path, as_attachment=True)

@app.route('/generate', methods=['POST'])
def generate():
    global current_dataset, file_name, categorical_columns, numerical_columns, negation_dictionary, df
    try:
        sheet_id  = '1gO23DklLIPLB7PWMeCbd_1IZmJJXEFtodO_K9xqcDfc'
        sheet_name = 'Variants'
        url = 'https://docs.google.com/spreadsheets/d/'+sheet_id+'/gviz/tq?tqx=out:csv&sheet='+sheet_name

        variant_df=pd.read_csv(url)
        variant_df.fillna('', inplace=True)
        variant_df = variant_df.iloc[:, :3]
        
        no_of_questions = int(request.form['no_questions'])
        dataset_name = request.form['dataset_name']
        templates = request.form.to_dict()
        selected_templates = []

        for k,v in templates.items():
            if 'no_questions' == k or 'dataset_name' == k:
                continue
            else:
                selected_templates.append(k)

        onenumcol = True if len(numerical_columns) == 1 else False

        # reading the current dataframe
        # df = pd.read_csv(os.path.join(os.getcwd() +'/mysite/datasets', file_name))
        df = pd.read_csv(os.path.join(os.getcwd() +'/datasets', file_name))
        df = df.fillna(0)
        Vector_Ques_Ans = []
        question_no_split = no_of_questions//len(selected_templates)
        for template in selected_templates:
            if template == "General":
                #print("General")
                temp = getGeneralQuestions(question_no_split, df, categorical_columns, numerical_columns, dataset_name, onenumcol)

                Vector_Ques_Ans += temp

            if template == "Bayesian":
                #print("Bayesian")
                variants = variant_df[variant_df['Type'] == 'Bayesian']['Variant']
                directions = variant_df[variant_df['Type'] == 'Bayesian']['Direction']
                Bayesian_Variants = []
                for variant, direction in zip(variants, directions):
                    Bayesian_Variants.append([variant.split(','), direction])

                temp = getBayesianQuestions(question_no_split, df, categorical_columns, numerical_columns, dataset_name, onenumcol, Bayesian_Variants)
                
                #print("Bayesian")
                Vector_Ques_Ans += temp

            if template == "Probability":
                #print("Probability")
                temp = getProbabilityQuestions(question_no_split, df, categorical_columns, numerical_columns, dataset_name, onenumcol)
                
                #print("Probability")
                Vector_Ques_Ans += temp

            if template == "Hypothesis":
                #print("Hypothesis")
                variants = variant_df[variant_df['Type'] == 'Hypothesis']['Variant']
                directions = variant_df[variant_df['Type'] == 'Hypothesis']['Direction']
                Hypothesis_Variants = []
                for variant, direction in zip(variants, directions):
                    Hypothesis_Variants.append([variant.split(','), direction])

                temp = getHypothesisQuestions(question_no_split, df, categorical_columns, numerical_columns, dataset_name, onenumcol, Hypothesis_Variants)
                
                #print("Hypothesis")
                Vector_Ques_Ans += temp

            if template == "Distribution":
                #print("Distribution")
                temp = getDistributionQuestions(question_no_split, df, categorical_columns, numerical_columns, dataset_name, onenumcol)
                
                #print("Distribution")
                Vector_Ques_Ans += temp

        result = pd.DataFrame(Vector_Ques_Ans, columns=["Type", "Questions", "Answer", "Code", "Dataset_Name", "Date_Generated"])
        
        # if os.path.isfile(os.path.join(os.getcwd() +'/mysite/datasets/Questions.csv')):
        #     questionsDF = pd.read_csv(os.path.join(os.getcwd() +'/mysite/datasets/Questions.csv'))
        #     frames = [result, questionsDF]
        #     result = pd.concat(frames)
        # result.to_csv(os.path.join(os.getcwd() +'/mysite/datasets/Questions.csv'), index=False)

        if os.path.isfile(os.path.join(os.getcwd() +'/datasets/Questions.csv')):
            questionsDF = pd.read_csv(os.path.join(os.getcwd() +'/datasets/Questions.csv'))
            frames = [result, questionsDF]
            result = pd.concat(frames)
        result.to_csv(os.path.join(os.getcwd() +'/datasets/Questions.csv'), index=False)
        
        questions_html = result.to_html()
        return render_template('successful_csv_generation.html', data=questions_html)
    
    except Exception as e:
        return render_template('error.html')

# Flex grade below
@app.route('/flexigrade')
def flexigrade():
    return render_template('flexinetid.html')
    
@app.route('/flexicheck', methods=['GET', 'POST'])
def flexicheck():
    return render_template('flexicheck.html')
    
@app.route('/loadgrades', methods=['GET'])
def loadgrades():
    netid = session.get('netid')
    if netid:
        # if os.path.isfile(os.path.join(os.getcwd() +'/mysite/datasets/grades.csv')):
        #     gradesDF = pd.read_csv(os.path.join(os.getcwd() +'/mysite/datasets/grades.csv'))
                
        if os.path.isfile(os.path.join(os.getcwd() +'/datasets/grades.csv')):
            gradesDF = pd.read_csv(os.path.join(os.getcwd() +'/datasets/grades.csv'))

        grade_netid = gradesDF[gradesDF['SIS Login ID'] == netid]
        print(grade_netid)
        grade_netid_quiz = [col for col in grade_netid.columns if 'quiz' in col.lower()]
        grade_netid_heavy = [col for col in grade_netid.columns if 'heavy' in col.lower()]
        grade_netid_medium = [col for col in grade_netid.columns if(('quiz' not in col.lower()) and ('heavy' not in col.lower()))][2:]

        print(grade_netid_quiz)
        print(grade_netid_heavy)
        print(grade_netid_medium)
        
        filtered_json = grade_netid.to_json(orient='records')
        # return render_template('copyflexigrade.html', grades = filtered_json, quizzes = grade_netid_quiz, medium = grade_netid_medium, heavy = grade_netid_heavy)
        return render_template('copyflexigrade-demo.html', grades = filtered_json, quizzes = grade_netid_quiz, medium = grade_netid_medium, heavy = grade_netid_heavy)
    else:
        return render_template('notloggedin.html')
   
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        username = request.json['username']
        password = request.json['password'].encode('utf-8')
        new_user = User(username=username, password=password)
        
        db.session.add(new_user)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": "An error occurred while registering the user"+'\n'+str(e.args)}), 500

        return jsonify({"message": "User registered successfully"}), 201
 
    if request.method == "GET":
        return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()  # Clear the session
    return jsonify({"message": "Logged out successfully", "redirect": "/login"}), 200

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "GET":
        return render_template('login.html')
    
    if request.method == "POST":
        username = request.json['username']
        password = request.json['password'].encode('utf-8')
        
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['netid'] = username  # Save user ID in session

            return jsonify({"message": "Login successful", "redirect": "/loadgrades"}), 200

        elif user:
            return jsonify({"error": "Incorrect password"}), 401
        else:
            return jsonify({"error": "Username not found"}), 404
        

# Demo stuff below
@app.route('/flexidemo')
def flexidemo():
    
    return render_template('flexinetid-demo.html')
    
@app.route('/loaddemogrades', methods=['POST'])
def loaddemogrades():
    netid = request.form['netid']
    # if os.path.isfile(os.path.join(os.getcwd() +'/mysite/datasets/demo.csv')):
    #     gradesDF = pd.read_csv(os.path.join(os.getcwd() +'/mysite/datasets/demo.csv'))
            
    if os.path.isfile(os.path.join(os.getcwd() +'/datasets/demohw1.csv')):
        gradesDF = pd.read_csv(os.path.join(os.getcwd() +'/datasets/demohw1.csv'))
        
    grade_netid = gradesDF[gradesDF['SIS Login ID'] == netid]
    print(grade_netid)
    grade_netid_quiz = [col for col in grade_netid.columns if 'quiz' in col.lower()]
    grade_netid_heavy = [col for col in grade_netid.columns if 'heavy' in col.lower()]
    grade_netid_medium = [col for col in grade_netid.columns if(('quiz' not in col.lower()) and ('heavy' not in col.lower()))][2:]

    print(grade_netid_quiz)
    print(grade_netid_heavy)
    print(grade_netid_medium)
    
    filtered_json = grade_netid.to_json(orient='records')
    return render_template('copyflexigrade-demo.html', grades = filtered_json, quizzes = grade_netid_quiz, medium = grade_netid_medium, heavy = grade_netid_heavy)
    
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')