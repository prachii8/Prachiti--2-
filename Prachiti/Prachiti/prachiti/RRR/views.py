import json

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
import csv
import math
# import datetime
from datetime import datetime, timedelta
from re import search
import sklearn.metrics
from sklearn.metrics import pairwise_distances

import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import OneHotEncoder
import numpy as np


from joblib import load

user_row = []
restaurant_names=[]
line=''
# file=pd.read_csv('ratings.csv')
# for i in range(len(file)):
#     file.loc[i,'1']=0
#     file.loc[i,'2']=0
#     file.loc[i,'3']=0
#     file.loc[i,'4']=0
#     file.loc[i,'5']=0
#     file.loc[i,'Total Vote']=0
#     file.loc[i,'Rating']=0.0

# file.to_csv('ratings.csv',index=False)


def home(request):
    return render(request, 'home.html')


def login(request):
    global user_row
    user_row = []
    if(request.method == 'POST'):
        email = request.POST['email']
        password = request.POST['password']
        user_data = pd.read_csv('user_data.csv')
        for row in range(len(user_data)):
            if(user_data.loc[row, 'email'] == email):
                print(str(user_data.loc[row, 'password']))
                if(user_data.loc[row, 'password'] == password):
                    # print(row+2)
                    # user_row=row+2
                    user_row.append(user_data.loc[row, 'name'])
                    user_row.append(user_data.loc[row, 'email'])
                    user_row.append(row)
                    return redirect('/dashboard')
                else:
                    return render(request, 'login.html', {'message': 'Please check your password'})

        return render(request, 'login.html', {'Issue': True})

    return render(request, 'login.html')


def signup(request):
    if(request.method == "POST"):
        name = request.POST['name']
        email = request.POST['email']
        password = request.POST['password']
        cpassword = request.POST['cpassword']
        if(password!=cpassword):
            return render(request, 'signup.html', {'Issue': "Password didn't match"})
        user_data = pd.read_csv('user_data.csv')

        for row in range(len(user_data)):
            if(user_data.loc[row, 'email'] == email):
                return render(request, 'signup.html', {'Issue': 'Email already exists !'})

        i = len(user_data)+1
        user_data.loc[i, 'name'] = name
        user_data.loc[i, 'email'] = email
        user_data.loc[i, 'password'] = str(password)
        # user_data.loc[i,'history']=[]

        user_data.to_csv("user_data.csv", index=False)
        return redirect('/login')

    return render(request, 'signup.html')


def dashboard(request):
    global user_row
    print('Dashboard')
    # global data,final
    final = []
    csv_fp = open('restaurant.csv', 'r')

    reader = csv.DictReader(csv_fp)
    headers = [col for col in reader.fieldnames if col != 'Unnamed: 0']
    for row in reader:
        data = []
        data.append(row['Restaurant Name'])
        data.append(row['Address'])
        data.append(row['Online Order'])
        data.append(row['Book Table'])
        data.append(row['Rate'])
        data.append(row['Phone'])
        data.append(row['Restaurant Type'])
        data.append(row['Famous Dishes'])
        data.append(row['Cuisines'])
        data.append(row['Approx cost(for two people)'])
        data.append(row['Type'])
        final.append(data)
    if request.method == 'POST':
        print("Searching !!!")
        find = request.POST['search']
        print(find)
        csv_fp = open('restaurant.csv', 'r')
        reader = csv.DictReader(csv_fp)
        final = []
        for row in reader:
            if(find in row['Restaurant Name'] or find.lower() in row['Restaurant Name'] or find.capitalize() in row['Restaurant Name']):
                data = []
                data.append(row['Restaurant Name'])
                data.append(row['Address'])
                data.append(row['Online Order'])
                data.append(row['Book Table'])
                data.append(row['Rate'])
                data.append(row['Phone'])
                data.append(row['Restaurant Type'])
                data.append(row['Famous Dishes'])
                data.append(row['Cuisines'])
                data.append(row['Approx cost(for two people)'])
                data.append(row['Type'])
                final.append(data)
                # print(row['Number'])

    final.sort(key=lambda x: x[4], reverse=True)
    print(user_row)
    return render(request, 'dashboard.html', {'data': final, 'headers': headers, 'name': user_row[0]})


def filter(request):
    if(request.method == 'POST'):

        order = request.POST.get("online_order", None)
        book_table = request.POST.get("book_table", None)
        rate = request.POST.get("Rate", None)
        type = request.POST.get("type", None)
        lprice = request.POST.get("price", None)
        print("Order : ", order)
        print("Book table : ", book_table)
        print("Rating : ", rate)
        print("Typing : ", type)
        print("Price : ", lprice)
        if(lprice != None):
            uprice = int(lprice)+200
        else:
            uprice = 1000
            lprice = 0
        if(order == None):
            order = ""
        if(book_table == None):
            book_table = ""
        if(rate == None):
            rate = '0.0'
        if(type == None):
            type = ''
        csv_fp = open('restaurant.csv', 'r')
        reader = csv.DictReader(csv_fp)
        headers = [col for col in reader.fieldnames if col != 'Unnamed: 0']
        final = []
        for row in reader:
            if(order in row['Online Order'] and book_table in row['Book Table'] and float(rate) <= float(row['Rate']) and type in row['Restaurant Type'] and int(lprice) <= int(row['Approx cost(for two people)']) < int(uprice)):
                data = []
                data.append(row['Restaurant Name'])
                data.append(row['Address'])
                data.append(row['Online Order'])
                data.append(row['Book Table'])
                data.append(row['Rate'])
                data.append(row['Phone'])
                data.append(row['Restaurant Type'])
                data.append(row['Famous Dishes'])
                data.append(row['Cuisines'])
                data.append(row['Approx cost(for two people)'])
                data.append(row['Type'])
                final.append(data)

    final.sort(key=lambda x: x[4], reverse=True)
    return render(request, 'dashboard.html', {'data': final, 'headers': headers})


def calculate_rating(line):
    csv = pd.read_csv('ratings.csv', sep=',')
    row = csv.loc[line]
    print(row)
    curr_rating = (float(row[2])*5+float(row[3])*4+float(row[4])
                   * 3+float(row[5])*2+float(row[6])*1)/float(row[1])
    print(round(curr_rating, 2))
    return round(curr_rating, 2)
    csv.loc[line, 'Rating'] = curr_rating
    csv.to_csv("ratings.csv", index=False)


def res_suggestion(line):
    # csv_res = open('restaurant.csv', 'r')
    csv_pd = pd.read_csv('restaurant.csv')
    # reader = csv.DictReader(csv_res)
    cuisines = (csv_pd.loc[line]['Cuisines']).split(',')
    # print(cuisines)
    dic = []
    for cuisine in cuisines:
        # for row in reader:
        #     if(cuisine in row['Cuisines']):
        #         temp.append(row['Restaurant_Name'])
        # final.append(temp)
        for i in range(len(csv_pd)):
            temp = []
            if(cuisine in csv_pd.loc[i, 'Cuisines'] and csv_pd.loc[i, 'Restaurant Name'] not in dic and csv_pd.loc[i, 'Restaurant Name'] != csv_pd.loc[line, 'Restaurant Name']):
                temp.append(csv_pd.loc[i, 'Restaurant Name'])
                temp.append(csv_pd.loc[i, 'Cuisines'])
                temp.append(csv_pd.loc[i, 'Rate'])
                temp.append(csv_pd.loc[i, 'Famous Dishes'])
                temp.append(csv_pd.loc[i, 'Approx cost(for two people)'])
                temp.append(csv_pd.loc[i, 'Address'])
                dic.append(temp)

    # print(dic)
    # print(final)
    dic.sort(key=lambda x: x[2], reverse=True)
    return dic


def review(request):
    global user_row,restaurant_names
    rating_file = open('ratings.csv', 'r')

    reader = csv.DictReader(rating_file)
    for row in reader:
        restaurant_names.append(row['Restaurant_Name'])
    rating_file.close()

    file = pd.read_csv('ratings.csv', sep=',')

    user_data = pd.read_csv('user_data.csv')

    if(request.method == "POST"):
        global line
        cuisine_list=[]
        res=request.POST.get('restaurant')
        rate=request.POST.get('rating')
        print("Restaurant Selected is : ",res)
        print("Rating : ",rate)

        rating_file = open('ratings.csv', 'r')

        reader = csv.DictReader(rating_file)
        now = datetime.now()
        info=[]
        info.append(res)
        info.append(rate)
        info.append(now.strftime("%Y-%m-%d %H:%M:%S"))
        print(info)
        x=(user_data.loc[user_row[2],'history'])
        # Important- Time limitation

        if(str(x) == 'nan'):
            user_data.loc[user_row[2],'history']=info
            user_data.to_csv('user_data.csv',index=False)
        else:
            # print(user_data.loc[user_row[2],'history'].split(',')[2][2:-2])
            time=user_data.loc[user_row[2],'history'].split(',')[2][2:-2]
            # restaurant=user_data.loc[user_row[2],'history'].split(',')[0][2:-1]
            converted_dt=datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
            if(converted_dt + timedelta(hours=3)<=datetime.now()):
                print("You can submit a review.")
                print(','.join([str(x),str(info)]))
                user_data.loc[user_row[2],'history']=','.join([str(info),str(x)])
                user_data.to_csv('user_data.csv',index=False)

            else:
                print("You can submit only after 3hrs from previous.")
                return render(request,'review.html',{'data':restaurant_names,'msg':'You can submit only after 3hrs from previous.'})

        #Updating the rating
        for row in reader:
            if(res==row['Restaurant_Name']):
                line=reader.line_num
                value=float(row[rate])
                total=float(row['Total Vote'])
                
        print("Line no is : ",line)
        file.loc[line-2,rate]=value+1.0
        file.loc[line-2,'Total Vote']=total+1.0
        file.to_csv("ratings.csv", index=False)
        print("No of {} star rating is : {}".format(rate,file.loc[line-2,rate]))
        print("Total ratings : {}".format(file.loc[line-2,'Total Vote']))
        curr_rating=calculate_rating(line-2)
        file.loc[line-2,'Rating']=curr_rating
        file.to_csv("ratings.csv", index=False)
        
        restaurant_file = pd.read_csv('restaurant.csv',sep=',')
        restaurant_file.loc[line-2,'Rate']=curr_rating
        restaurant_file.to_csv("restaurant.csv", index=False)

        restaurant_file = open('restaurant.csv', 'r')
        reader = csv.DictReader(restaurant_file)
        cuisine_list=[]
        for row in reader:
            temp=row['Cuisines'].split(',')
            for cuisine in temp:
                if(cuisine.strip() not in cuisine_list):
                    cuisine_list.append(cuisine.strip())

        restaurant_file.close()
        return render(request,'review.html',{'showModal':True,'data':restaurant_names,'cuisine_list':cuisine_list,'user_name':user_row[0]})

        # data=res_suggestion(line-2)
        # data['data']=final
        
        return render(request,'review.html',{'data':restaurant_names})



    return render(request,'review.html',{'data':restaurant_names})

def suggestion(request):
    global restaurant_names,line
    if(request.method == "POST"):
            if 'choice' in request.POST:
                # print("Choice")
                choices=set(request.POST.getlist('cuisine_select'))
                print(choices)
                restaurant_file = open('restaurant.csv', 'r')
                reader = csv.DictReader(restaurant_file)
                sugg=[]
                for each_rest in reader:
                    temp=[]
                    cuisine_list=set(map(str.strip, each_rest['Cuisines'].split(',')))
                    if len(cuisine_list.intersection(choices)) > 0:
                        temp.append(each_rest['Restaurant Name'])
                        temp.append(each_rest['Cuisines'])
                        temp.append(each_rest['Rate'])
                        temp.append(each_rest['Famous Dishes'])
                        temp.append(each_rest['Approx cost(for two people)'])
                        temp.append(each_rest['Address'])
                        sugg.append(temp)
                restaurant_file.close()
                # print(sugg)
                sugg.sort(key=lambda x: x[2], reverse=True)
                return render(request,'review.html',{'data':restaurant_names,'sugg':sugg})
            elif 'default' in request.POST:
                print("Default")
                sugg=res_suggestion(line-2)                                                                                         
                return render(request,'review.html',{'data':restaurant_names,'sugg':sugg})


restaurant_data = pd.read_csv('Zomato Analysis (1).csv', encoding='ISO-8859-1')
knn_model = load('knn_model.joblib')
data = {
    'location_encoded': [1, 2, 3],
    'cuisine_encoded': [4, 5, 6],
    'Dining(rate)': [4.5, 3.8, 4.2],
    'location': ['Location A', 'Location B', 'Location C']
}
data = {
    'location_encoded': [1, 2, 3],
    'cuisine_encoded': [4, 5, 6],
    'Dining(rate)': [4.5, 3.8, 4.2],
    'location': ['Location A', 'Location B', 'Location C']
}

def recommend_restaurants(request):
    if request.method == 'POST':
        user_location = request.POST.get('location')
        user_cuisine = request.POST.get('cuisines')
        rating_str = request.POST.get('Dining_rate')
        user_rating = 1

        if rating_str is not None and rating_str.strip() != "":
            try:
                user_rating = float(rating_str)
            except ValueError:
                return HttpResponse("Invalid rating input. Please enter a valid number.")

        restaurant_data.rename(columns={"Location": "location", "Cuisines": "cuisines", "Dining(rate)": "Dining_rate"},
                               inplace=True)

        renamed_restaurant_data = restaurant_data.copy()

        user_cuisine = [cuisine.strip() for cuisine in user_cuisine.split(',')]
        user_location = [location.strip() for location in user_location.split(',')]

        filtered_restaurants = renamed_restaurant_data.query(
            f"location.str.contains('{', '.join(user_location)}', case=False) "
            f"and cuisines.str.contains('{', '.join(user_cuisine)}', case=False) "
            f"and Dining_rate >= {user_rating}"
        )

        if 'data' in globals() and data is not None:
            features = np.array([data['location_encoded'], data['cuisine_encoded'], data['Dining(rate)']]).T
            target = np.array(data['location'])

            _, indices = knn_model.kneighbors(features)

            recommended_indices = indices[0]

            recommended_indices = recommended_indices[np.random.permutation(len(recommended_indices))]

            recommended_restaurants = renamed_restaurant_data.iloc[recommended_indices]

            recommended_restaurants_list = recommended_restaurants.to_dict(orient='records')

            return render(request, 'recommendation.html', {'recommended_restaurants': recommended_restaurants_list})
        else:
            return HttpResponse("No recommendation data available.")

    else:
        return render(request, 'recommendation.html', {'recommended_restaurants': []})