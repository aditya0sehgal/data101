from flask import Flask, render_template, request, send_file
import pandas as pd
import random, numpy as np, csv, io, os, json
from datetime import datetime


app = Flask(__name__)
column_cat = {}
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
    return render_template('home.html')

@app.route('/upload', methods=['POST'])
def upload():
    global file_name
    file = request.files['datasetFile']
    if file:
        destination_path = os.getcwd()  # Get the current working directory
        # file.save(os.path.join(destination_path+'/mysite/datasets', file.filename))
        file.save(os.path.join(destination_path+'/datasets', file.filename))
        file_name = file.filename
        # print(file_name)
        column_names = extract_column_names(file_name)
        temparr = []
        for col in column_names:
            # print(col)
            temparr.append(col)
        return {'column_names': temparr}
    else:
        return {'column_names': []}

@app.route('/roulette/<template>', methods=['GET'])
def roulette_template(template):
    # df = pd.read_csv(os.path.join(os.getcwd() +'/mysite/datasets/', 'Questions.csv'))
    df = pd.read_csv(os.path.join(os.getcwd() +'/datasets', 'Questions.csv'))

    val = template.split('-')
    df = df[df['Dataset_Name'] == (val[0]+" "+val[1]).upper()]
    rows = []
    # Iterate over the DataFrame and get each row's values
    for index, row in df.iterrows():
        values = row.values
        rows.append([values[1], values[2], values[3], values[4]])

    roulette_template = {0: rows}
    return render_template('rouletteQA.html', data=roulette_template)

def extract_column_names(file):
    global current_dataset_columns
    # col_names = pd.read_csv(os.path.join(os.getcwd() +'/mysite/datasets', file)).columns
    col_names = pd.read_csv(os.path.join(os.getcwd() +'/datasets', file)).columns
    current_dataset_columns = col_names
    # print(col_names)
    return col_names

# Post call based on no of questions input
@app.route('/column-selection', methods=['POST'])
def selectCatNumIgnore():
    try:
        global current_dataset_columns, column_cat, categorical_columns, numerical_columns, Questions

        categorical_columns, numerical_columns = [], []
        data = {}
        for col in current_dataset_columns:
            data[col] = request.form.get(col)

        column_cat = json.dumps(data)
        # print(column_cat, data)
        
        for key, value in data.items():
            if value == "numerical": 
                numerical_columns.append(key)
            elif value == "categorical": 
                categorical_columns.append(key)
        # print(column_cat)
        # print(categorical_columns)
        # print(numerical_columns)
        return render_template('generate.html')

    except Exception as e:
        return render_template('error.html')
        
def Evaluate_py_code(py_code):
  global df
#   print(py_code)
  evaluated_code = eval(py_code)
#   print(evaluated_code)
  return round(evaluated_code, 2)

def General_template(Dataset_name, L, Cat_name_1, Cat_name_2, Cat_name_3, Cat_Values_1, Cat_Values_2, Cat_Values_3,
                     Cat_Operator_1, Cat_Operator_2, Num_name_1, Num_name_2, Num_name_3, Num_val_1, Num_val_2, Num_val_3,
                     Num_Operator_1, Num_Operator_2):
    # print(Dataset_name, L, Cat_name_1, Cat_name_2, Cat_name_3, Cat_Values_1, Cat_Values_2, Cat_Values_3,
    #                  Cat_Operator_1, Cat_Operator_2, Num_name_1, Num_name_2, Num_name_3, Num_val_1, Num_val_2, Num_val_3,
    #                  Num_Operator_1, Num_Operator_2)
    
    Aggregate_selection = random.choice(["max", "min", "mean"])
    aggregate_text_dictionary = {"max" : "maximum", "min" : "minimum", "mean" : "mean"}

    Question = ""
    global symbol_text_dictionary
    if L == 1:
        Question = f"What is the {aggregate_text_dictionary[Aggregate_selection]} {Num_name_1.lower()} in {Dataset_name}?"
        Answer_Code = General_template_code(L, Aggregate_selection, Num_name_1, "0", "0", "0", "0", "0", "0")

    elif L == 2:
        choice = random.choice([1, 2])
        # print(choice)
        if choice == 1 and Num_name_1!=Num_name_2:
            Question = f"What is the {aggregate_text_dictionary[Aggregate_selection]} {Num_name_1.lower()} in {Dataset_name}, where {Num_name_2.lower()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_2}?"
            Answer_Code = General_template_code(L, Aggregate_selection, Num_name_1, Num_name_2, Num_Operator_1, Num_val_2, "0", "0", "0")
        else:
          Question = f"What is the {aggregate_text_dictionary[Aggregate_selection]} {Num_name_1.lower()} in {Dataset_name}, where {Cat_name_2.lower()} {symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_2}'?"
          Answer_Code = General_template_code(L, Aggregate_selection, Num_name_1, Cat_name_2, Cat_Operator_1, Cat_Values_2, "0", "0", "0")

    elif L == 3:
        choice = random.choice([1, 2, 3])
        # print(choice)
        if choice == 1 and Cat_name_1!=Cat_name_2:
            Question = f"What is the {aggregate_text_dictionary[Aggregate_selection]} {Num_name_1.lower()} in {Dataset_name}, where {Cat_name_1.lower()} {symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}' and {Cat_name_2.lower()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_2}'?"
            Answer_Code = General_template_code(L, Aggregate_selection, Num_name_1, Cat_name_1, Cat_Operator_1, Cat_Values_1, Cat_name_2, Cat_Operator_2, Cat_Values_2)
        elif choice == 2  and Num_name_1!=Num_name_2:
            Question = f"What is the {aggregate_text_dictionary[Aggregate_selection]} {Num_name_1.lower()} in {Dataset_name}, where {Num_name_2.lower()} {symbol_text_dictionary[Num_Operator_2]} {Num_val_2} and {Cat_name_3.lower()} {symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_3}'?"
            Answer_Code = General_template_code(L, Aggregate_selection, Num_name_1, Num_name_2, Num_Operator_2, Num_val_2, Cat_name_3, Cat_Operator_1, Cat_Values_3)
        else:
            if Num_name_1!=Num_name_2 and Num_name_3!=Num_name_2:
              return ["", ""]
              
    if Question == "":
      return ["", ""]
    else:
      Question_code = [Question, Answer_Code]
    #   print(Question_code)
      return Question_code



# Template 2: General Min, Max, and Mean
def General_template_code(L, Aggregate_selection, Num_name_1, condition_1, operator_1, condition_value_1, condition_2, operator_2, condition_value_2):
    # print(L, Aggregate_selection, Num_name_1, condition_1, operator_1, condition_value_1, condition_2, operator_2, condition_value_2)

    if L == 1:
        Answer_code_R = f"{Aggregate_selection}(df${Num_name_1});"
        Answer_code_py = f"df['{Num_name_1}'].{Aggregate_selection}()"

    elif L == 2:
        if isinstance(condition_value_1, str):
          Answer_code_R = f"temp <- df[df${condition_1} {operator_1} '{condition_value_1}', ]; {Aggregate_selection}(temp${Num_name_1});"
          Answer_code_py = f"df.loc[df['{condition_1}'] {operator_1} '{condition_value_1}', '{Num_name_1}'].{Aggregate_selection}()"
        else:
          Answer_code_R = f"temp <- df[df${condition_1} {operator_1} {condition_value_1}, ]; {Aggregate_selection}(temp${Num_name_1});"
          Answer_code_py = f"df.loc[df['{condition_1}'] {operator_1} {condition_value_1}, '{Num_name_1}'].{Aggregate_selection}()"
       
    elif L == 3:
        
        if isinstance(condition_value_1, str):
          Answer_code_R = f"temp <- df[df${condition_1} {operator_1} '{condition_value_1}' & df${condition_2} {operator_2} '{condition_value_2}', ]; {Aggregate_selection}(temp${Num_name_1});"
          Answer_code_py = f"df.loc[(df['{condition_1}'] {operator_1} '{condition_value_1}') & (df['{condition_2}'] {operator_2} '{condition_value_2}'), '{Num_name_1}'].{Aggregate_selection}()"
        else:
          Answer_code_R = f"temp <- df[df${condition_1} {operator_1} {condition_value_1} & df${condition_2} {operator_2} '{condition_value_2}', ]; {Aggregate_selection}(temp${Num_name_1});"
          Answer_code_py = f"df.loc[(df['{condition_1}'] {operator_1} {condition_value_1}) & (df['{condition_2}'] {operator_2} '{condition_value_2}'), '{Num_name_1}'].{Aggregate_selection}()"
        
    Answer_py = Evaluate_py_code(Answer_code_py)
    return [Answer_code_R, Answer_py]

def getGeneralQuestions(question_no_split, df, Categorical_Columns, Numerical_Columns, dataset_name):
    # print("getGeneralQuestions")
    Num_Operator = ["<", ">", "<=", ">="]
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

        # Measure
        Num_name_1 = random.choice(Numerical_Columns)
        value1 = int(min(df[Num_name_1]))
        value2 = int(max(df[Num_name_1]))
        Num_val_1 = random.randint(value1, value2)

        Num_name_2 = random.choice(Numerical_Columns)
        value1 = int(min(df[Num_name_2]))
        value2 = int(max(df[Num_name_2]))
        Num_val_2 = random.randint(value1, value2)

        Num_name_3 = random.choice(Numerical_Columns)
        value1 = int(min(df[Num_name_3]))
        value2 = int(max(df[Num_name_3]))
        Num_val_3 = random.randint(value1, value2)

        Num_Operator_1 = random.choice(Num_Operator)
        Num_Operator_2 = random.choice(Num_Operator)


        Type = "General Question"

        L = random.choice(range(1, 4))
        # print(dataset_name, L, Cat_name_1, Cat_name_2, Cat_name_3, Cat_Values_1,
        #                                     Cat_Values_2, Cat_Values_3, Cat_Operator_1, Cat_Operator_2, Num_name_1,
        #                                     Num_name_2, Num_name_3, Num_val_1, Num_val_2, Num_val_3, Num_Operator_1,
        #                                     Num_Operator_2)
        
        Generated_Question = General_template(dataset_name, L, Cat_name_1, Cat_name_2, Cat_name_3, Cat_Values_1,
                                            Cat_Values_2, Cat_Values_3, Cat_Operator_1, Cat_Operator_2, Num_name_1,
                                            Num_name_2, Num_name_3, Num_val_1, Num_val_2, Num_val_3, Num_Operator_1,
                                            Num_Operator_2)
        # print(Generated_Question)
        if Generated_Question[0] == "" or  Generated_Question[0] in duplicate_question_check :
            continue
        duplicate_question_check.add(Generated_Question[0])
        count += 1

        Generated_Answer =  "Empty result" if np.isnan(Generated_Question[1][1]) else Generated_Question[1][1]
        Ques_Ans.append([Type, Generated_Question[0], Generated_Answer, Generated_Question[1][0], dataset_name.upper(), str(datetime.now().date())])
    return Ques_Ans


# Template 1 Bayesian
def Bayesian_template(Dataset_name, L, Cat_name_1, Cat_name_2, Cat_name_3, Cat_Values_1, Cat_Values_2, Cat_Values_3, Cat_Operator_1, Cat_Operator_2, Num_name_1, Num_name_2, Num_name_3, Num_val_1, Num_val_2, Num_val_3, Num_Operator_1, Num_Operator_2):

    Question = ""
    Answer_Code = ""
    
    global symbol_text_dictionary
    if L == 2:
        choice = random.randint(1, 4)
        if choice == 1:
            Question = f"What are the posterior odds of {Cat_name_1.lower()} being {pre_symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}' in {Dataset_name}, given that {Cat_name_2.lower()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_2}'?"
            # print(Question)
            Answer_Code = Bayesian_template_code(L, Cat_name_1, Cat_Operator_1, Cat_Values_1, Cat_name_2, Cat_Operator_2, Cat_Values_2, "0", "0", "0")
        elif choice == 2:
            Question = f"What are the posterior odds of {Cat_name_1.lower()} being {pre_symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}' in {Dataset_name}, given that {Num_name_1.lower()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_1}?"
            # print(Question)
            Answer_Code = Bayesian_template_code(L, Cat_name_1, Cat_Operator_1, Cat_Values_1, Num_name_1, Num_Operator_1, Num_val_1, "0", "0", "0")
        elif choice == 3:
            Question = f"What are the posterior odds of {Num_name_1.lower()} being {pre_symbol_text_dictionary[Num_Operator_1]} {Num_val_1} in {Dataset_name}, given that {Cat_name_1.lower()} {symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}'?"
            # print(Question)
            Answer_Code = Bayesian_template_code(L, Num_name_1, Num_Operator_1, Num_val_1, Cat_name_1, Cat_Operator_1, Cat_Values_1, "0", "0", "0")
        elif choice > 3:
            if Num_name_1 == Num_name_2:
              return ["", ""]
            else:
              Question = f"What are the posterior odds of {Num_name_1.lower()} being {pre_symbol_text_dictionary[Num_Operator_1]} {Num_val_1} in {Dataset_name}, given that {Num_name_2.lower()} {symbol_text_dictionary[Num_Operator_2]} {Num_val_2}?"
              # print(Question)
              Answer_Code = Bayesian_template_code(L, Num_name_1, Num_Operator_1, Num_val_1, Num_name_2, Num_Operator_2, Num_val_2, "0", "0", "0")

    else:
        choice = random.randint(1, 6)
        if choice == 1:
          if (Cat_name_1 == Cat_name_2 or Cat_name_3 == Cat_name_2 or Cat_name_1 == Cat_name_3):
            # not valid question because of overlaps in nums and cat choices.
            return ["", ""]

          else:
            Question = f"What are the posterior odds of {Cat_name_1.lower()} being {pre_symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}' in {Dataset_name}, given that {Cat_name_2.lower()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_2}' and {Cat_name_3.lower()} {symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_3}'?"
            # print(Question)
            Answer_Code = Bayesian_template_code(L, Cat_name_1, Cat_Operator_1, Cat_Values_1, Cat_name_2, Cat_Operator_2, Cat_Values_2, Cat_name_3, Cat_Operator_1, Cat_Values_3)
        elif choice == 2:
          if (Cat_name_1 == Cat_name_3):
            # not valid question because of overlaps in nums and cat choices.
            return ["", ""]
          else:
            Question = f"What are the posterior odds of {Cat_name_1.lower()} being {pre_symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}' in {Dataset_name}, given that {Num_name_1.lower()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_1} and {Cat_name_3.lower()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_3}'?"
            # print(Question)
            Answer_Code = Bayesian_template_code(L, Cat_name_1, Cat_Operator_1, Cat_Values_1, Num_name_1, Num_Operator_1, Num_val_1, Cat_name_3, Cat_Operator_2, Cat_Values_3)
        elif choice == 3:
          if (Cat_name_1 == Cat_name_2):
            # not valid question because of overlaps in nums and cat choices.
            return ["", ""]
          else:
            Question = f"What are the posterior odds of {Num_name_1.lower()} being {pre_symbol_text_dictionary[Num_Operator_1]} {Num_val_1} in {Dataset_name}, given that {Cat_name_1.lower()} {symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}' and {Cat_name_2.lower()} {symbol_text_dictionary[Cat_Operator_2]} '{Cat_Values_2}'?"
            # print(Question)
            Answer_Code = Bayesian_template_code(L, Num_name_1, Num_Operator_1, Num_val_1, Cat_name_1, Cat_Operator_1, Cat_Values_1, Cat_name_2, Cat_Operator_2, Cat_Values_2)
        elif choice == 4 and Num_name_1!=Num_name_2:
            Question = f"What are the posterior odds of {Num_name_1.lower()} being {pre_symbol_text_dictionary[Num_Operator_1]} {Num_val_1} in {Dataset_name}, given that {Num_name_2.lower()} {symbol_text_dictionary[Num_Operator_2]} {Num_val_2} and {Cat_name_3.lower()} {symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_3}'?"
            # print(Question)
            Answer_Code = Bayesian_template_code(L, Num_name_1, Num_Operator_1, Num_val_1, Num_name_2, Num_Operator_2, Num_val_2, Cat_name_3, Cat_Operator_1, Cat_Values_3)
        elif choice == 5 and Num_name_1!=Num_name_2:
            Question = f"What are the posterior odds of {Num_name_1.lower()} being {pre_symbol_text_dictionary[Num_Operator_1]} {Num_val_1} in {Dataset_name}, given that {Num_name_2.lower()} {symbol_text_dictionary[Num_Operator_2]} {Num_val_2} and {Num_name_3.lower()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_3}?"
            # print(Question)
            Answer_Code = Bayesian_template_code(L, Num_name_1, Num_Operator_1, Num_val_1, Num_name_2, Num_Operator_2, Num_val_2, Num_name_3, Num_Operator_1, Num_val_3)
        else:
          if Num_name_2!=Num_name_3:
              Question = f"What are the posterior odds of {Cat_name_1.lower()} being {pre_symbol_text_dictionary[Cat_Operator_1]} '{Cat_Values_1}' in {Dataset_name}, given that {Num_name_2.lower()} {symbol_text_dictionary[Num_Operator_2]} {Num_val_2} and {Num_name_3.lower()} {symbol_text_dictionary[Num_Operator_1]} {Num_val_3}?"
              # print(Question)
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
    # print(L, "code gen block")
    if L == 2:
        Prior = eval(f"df[df['{condition_1}'] {operator_1} {condition_value_1}].shape[0] / len(df)")
        # print("Prior - ", Prior)
        if Prior == 1:
          return "zero ans"
        PriorOdds = eval(f"round({Prior} / (1 - {Prior}), 2)")
        # print("PriorOdds - ", PriorOdds)
        # print("--", condition_2, operator_2, condition_value_2, condition_1, operator_1, condition_value_1 )
        # print( f"round(len(df[(df['{condition_2}'] {operator_2} {condition_value_2}) & (df['{condition_1}'] {operator_1} {condition_value_1})]) / len(df[(df['{condition_1}'] {operator_1} {condition_value_1})]), 2)" )
        if eval(f"len(df[df['{condition_1}'] {operator_1} {condition_value_1}])") == 0:
          return "zero ans"
        TruePositive = eval(f"round(len(df[(df['{condition_2}'] {operator_2} {condition_value_2}) & (df['{condition_1}'] {operator_1} {condition_value_1})]) / len(df[(df['{condition_1}'] {operator_1} {condition_value_1})]), 2)")
        # print("TruePositive - ", TruePositive)
        FalsePositive = eval(f"round(len(df[(df['{condition_2}'] {operator_2} {condition_value_2}) & (df['{condition_1}'] {negation_dictionary[operator_1]} {condition_value_1})]) / len(df[(df['{condition_1}'] {negation_dictionary[operator_1]} {condition_value_1})]), 2)")
        # print("FalsePositive - ", FalsePositive)
        if TruePositive == 0 or FalsePositive == 0:
          return "zero ans"
        LikelihoodRatio = eval(f"round({TruePositive} / {FalsePositive}, 2)")
        # print("LikelihoodRatio - ", LikelihoodRatio)
        PosteriorOdds = eval(f"{LikelihoodRatio} * {PriorOdds}")
        # print("PosteriorOdds - ", PosteriorOdds)
        Posterior = eval(f"{PosteriorOdds} / (1 + {PosteriorOdds})")
        # print("Posterior - ", Posterior)
        Answer_code_py = round(Posterior, 2)

        # # belief : DOZES_OFF != 'always'
        # # observation : PARTICIPATION < 1 and SCORE < 93
        Answer_code_R = f"# belief : {condition_1} {operator_1} {condition_value_1}; # observation : {condition_2} {operator_2} {condition_value_2};"
        Answer_code_R += f"Prior<-nrow(df[df${condition_1} {operator_1} {condition_value_1}, ])/nrow(df); cat('Prior is equal to:', Prior);"
        Answer_code_R += f"PriorOdds<-round(Prior/(1-Prior), 2); cat('Prior Odds are equal to:', PriorOdds);"
        Answer_code_R += f"TruePositive<-round(nrow(df[df${condition_2} {operator_2} {condition_value_2} & df${condition_1} {operator_1} {condition_value_1}, ])/nrow(df[df${condition_1} {operator_1} {condition_value_1}, ]), 2); cat('TruePositive is equal to:', TruePositive);"
        Answer_code_R += f"FalsePositive<-round(nrow(df[df${condition_2} {operator_2} {condition_value_2} & df${condition_1} {negation_dictionary[operator_1]} {condition_value_1}, ])/nrow(df[df${condition_1} {negation_dictionary[operator_1]} {condition_value_1}, ]), 2); cat('FalsePositive is equal to:', FalsePositive);"
        Answer_code_R += f"LikelihoodRatio<-round(TruePositive/FalsePositive,2); cat('LikelihoodRatio is equal to:', LikelihoodRatio);"
        Answer_code_R += f"PosteriorOdds <-LikelihoodRatio * PriorOdds; cat('Posterior Odds are equal to:', PosteriorOdds);"
        Answer_code_R += f"Posterior <-PosteriorOdds/(1+PosteriorOdds); cat('Posterior is equal to:', Posterior); "

    elif L == 3:
        # print("-", eval(f"df[df['{condition_1}'] {operator_1} {condition_value_1}].shape[0]"))
        Prior = eval(f"df[df['{condition_1}'] {operator_1} {condition_value_1}].shape[0] / len(df)")
        if Prior == 1:
          return "zero ans"
        # print("Prior - ", Prior)
        PriorOdds = eval(f"round({Prior} / (1 - {Prior}), 2)")
        # print("PriorOdds - ", PriorOdds)
        # print("--", condition_2, operator_2, condition_value_2, condition_1, operator_1, condition_value_1, condition_3, operator_3, condition_value_3 )
        # print(f"round(len(df[df['{condition_2}'] {operator_2} {condition_value_2} & df['{condition_1}'] {operator_1} {condition_value_1} & df['{condition_3}'] {operator_3} {condition_value_3}]) / len(df[df['{condition_1}'] {operator_1} {condition_value_1}]), 2)")
        if eval(f"len(df[df['{condition_1}'] {operator_1} {condition_value_1}])") == 0:
          return "zero ans"
        TruePositive = eval(f"round(len(df[(df['{condition_2}'] {operator_2} {condition_value_2}) & (df['{condition_1}'] {operator_1} {condition_value_1}) & (df['{condition_3}'] {operator_3} {condition_value_3})]) / len(df[(df['{condition_1}'] {operator_1} {condition_value_1})]), 2)")
        # print("TruePositive - ", TruePositive)
        FalsePositive = eval(f"round(len(df[(df['{condition_2}'] {operator_2} {condition_value_2}) & (df['{condition_1}'] {negation_dictionary[operator_1]} {condition_value_1}) & (df['{condition_3}'] {operator_3} {condition_value_3})]) / len(df[(df['{condition_1}'] {negation_dictionary[operator_1]} {condition_value_1})]), 2)")
        # print("FalsePositive - ", FalsePositive)
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
        Answer_code_R += f"Posterior <-PosteriorOdds/(1+PosteriorOdds); cat('Posterior is equal to:', Posterior);"

    # Answer_py = Evaluate_py_code(Answer_code_py)
    Answer_py = Answer_code_py
    return [Answer_code_R, Answer_py]


def getBayesianQuestions(question_no_split, df, Categorical_Columns, Numerical_Columns, dataset_name):
    # print("getBayesianQuestions")
    Num_Operator = ["<", ">", "<=", ">="]
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

        # Measure
        Num_name_1 = random.choice(Numerical_Columns)
        value1 = int(min(df[Num_name_1]))
        value2 = int(max(df[Num_name_1]))
        Num_val_1 = random.randint(value1, value2)

        Num_name_2 = random.choice(Numerical_Columns)
        value1 = int(min(df[Num_name_2]))
        value2 = int(max(df[Num_name_2]))
        Num_val_2 = random.randint(value1, value2)

        # here check if selected numval1 and 2 are at extremes then dont send invalid operators.

    # Below for num3 might be not needed. Same thing pastedbelow just for the function to work.
        # Num_name_3 = random.choice(Numerical_Columns)
        # value1 = int(min(df[Num_name_3]))
        # value2 = int(max(df[Num_name_3]))
        # Num_val_3 = random.randint(value1, value2)

        Num_name_3 = random.choice(Numerical_Columns)
        value1 = int(min(df[Num_name_3]))
        value2 = int(max(df[Num_name_3]))
        Num_val_3 = random.randint(value1, value2)


        Num_Operator_1 = random.choice(Num_Operator)
        Num_Operator_2 = random.choice(Num_Operator)


        Type = "Bayesian Question"

        L = random.choice(range(2, 4))

        if L == 2 and Cat_name_1 == Cat_name_2:
            continue
        if L == 2 and Num_name_1 == Num_name_2:
            continue
        # if L == 3 and (Cat_name_1 == Cat_name_2 or Cat_name_3 == Cat_name_2 or Cat_name_1 == Cat_name_3):
        #   continue
        # if L == 3 and (Num_name_1 == Num_name_2 or Num_name_3 == Num_name_2 or Num_name_1 == Num_name_3):
        #   continue

        Generated_Question = Bayesian_template(dataset_name, L, Cat_name_1, Cat_name_2, Cat_name_3, Cat_Values_1,
                                            Cat_Values_2, Cat_Values_3, Cat_Operator_1, Cat_Operator_2, Num_name_1,
                                            Num_name_2, Num_name_3, Num_val_1, Num_val_2, Num_val_3, Num_Operator_1,
                                            Num_Operator_2)

        if Generated_Question[0] == "" or  Generated_Question[1] == "zero ans" or Generated_Question[0] in duplicate_question_check :
            continue
        if Generated_Question[1][1] == 0:
            continue
        else:
            Generated_Answer =  Generated_Question[1][1]
            duplicate_question_check.add(Generated_Question[0])
            count += 1

        # print(Generated_Question, Generated_Answer)
        Ques_Ans.append([Type, Generated_Question[0], Generated_Answer, Generated_Question[1][0], dataset_name.upper(), str(datetime.now().date())])
    return Ques_Ans


def getHypothesisQuestions(question_no_split):
    print("getHypothesisQuestions")
def getDistributionQuestions(question_no_split):
    print("getDistributionQuestions")
def getProbabilityQuestions(question_no_split):
    print("getProbabilityQuestions")

@app.route('/download_csv')
def download_csv():
    csv_file_path = 'datasets/Questions.csv'
    return send_file(csv_file_path, as_attachment=True)

# Post call based on no of questions input
@app.route('/generate', methods=['POST'])
def generate():
    global current_dataset, file_name, categorical_columns, numerical_columns, negation_dictionary, df
    try:
        # getting values from the front-end.
        no_of_questions = int(request.form['no_questions'])
        dataset_name = request.form['dataset_name']
        templates = request.form.to_dict()
        selected_templates = []
        for k,v in templates.items():
            if 'no_questions' == k or 'dataset_name' == k:
                continue
            else:
                selected_templates.append(k)
                
        # reading the current dataframe
        # df = pd.read_csv(os.path.join(os.getcwd() +'/mysite/datasets', file_name))
        df = pd.read_csv(os.path.join(os.getcwd() +'/datasets', file_name))
        df = df.fillna(0)
        Vector_Ques_Ans = []
        question_no_split = no_of_questions//len(selected_templates)
        # print(question_no_split)
        for template in selected_templates:
            if template == "General":
                temp = getGeneralQuestions(question_no_split, df, categorical_columns, numerical_columns, dataset_name)
                Vector_Ques_Ans += temp

            if template == "Bayesian":
                temp = getBayesianQuestions(question_no_split, df, categorical_columns, numerical_columns, dataset_name)
                Vector_Ques_Ans += temp

            if template == "Hypothesis":
                getHypothesisQuestions(question_no_split, dataset_name)
            if template == "Distribution":
                getDistributionQuestions(question_no_split, dataset_name)
            if template == "Probability":
                getProbabilityQuestions(question_no_split, dataset_name)

        # print(Vector_Ques_Ans)
        result = pd.DataFrame(Vector_Ques_Ans, columns=["Type", "Questions", "Answer", "Code", "Dataset_Name", "Date_Generated"])
        
        # if os.path.isfile(os.path.join(os.getcwd() +'/mysite/datasets/Questions.csv')):
        #     questionsDF = pd.read_csv(os.path.join(os.getcwd() +'/mysite/datasets/Questions.csv'))
        #     frames = [questionsDF, result]
        #     result = pd.concat(frames)

        # result.to_csv(os.path.join(os.getcwd() +'/mysite/datasets/Questions.csv'), index=False)

        if os.path.isfile(os.path.join(os.getcwd() +'/datasets/Questions.csv')):
            questionsDF = pd.read_csv(os.path.join(os.getcwd() +'/datasets/Questions.csv'))
            frames = [questionsDF, result]
            result = pd.concat(frames)

        result.to_csv(os.path.join(os.getcwd() +'/datasets/Questions.csv'), index=False)
        
        questions_html = result.to_html()
        # print(questions_html)
        return render_template('successful_csv_generation.html', data=questions_html)
    
    except Exception as e:
        # print(e)
        return render_template('error.html')
        

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')