from django.shortcuts import render, redirect
from .forms import UserForm
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
import json
import requests
from django.http import JsonResponse
from datetime import date, timedelta
from django.conf import settings
from google import genai
from django.views.decorators.http import require_http_methods
from .models import QuestionAnswer
# Create your views here.


client = genai.Client(api_key=settings.SECRET_KEY_AI)




@login_required(login_url='signin')
def index(request):
    today = date.today()
    yesterday = date.today() - timedelta(days=1)
    seven_days_ago = date.today() - timedelta(days=7)
    
    questions = QuestionAnswer.objects.filter(user=request.user)
    t_questions = questions.filter(created=today)
    y_questions = questions.filter(created=yesterday)
    s_questions = questions.filter(created__gte=seven_days_ago, created__lte=today)
    
    context = {"t_questions":t_questions, "y_questions": y_questions, "s_questions": s_questions}
    return render(request,'chatapp/index.html',context)

def signup(request):
    if request.user.is_authenticated:
        return redirect("index")
    form=UserForm()
    if request.method=='POST':
        form=UserForm(request.POST)
        if form.is_valid():
            form.save()
            username=request.POST["username"]
            password=request.POST["password1"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("index")
    context={"form":form}
    return render(request,'chatapp/signup.html',context)

def signin(request):
    err = None
    if request.user.is_authenticated:
        return redirect("index")
    
    if request.method == 'POST':
        
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("index")
        
        else:
            err = "Invalid Credentials"
        
        
    context = {"error": err}
    return render(request,'chatapp/signin.html',context)

def signout(request):
    logout(request)
    return redirect("signin")


def ask_ai(message):
    try:
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                {"role": "user", "parts": [{"text": message}]}
            ],
        )

        answer = response.text
        return answer
    except Exception as e:
        # Catch any exceptions during the API call (e.g., network issues, invalid API key)
        print(f"Error calling Gemini API: {e}")
        # Re-raise the exception to be caught by the calling getValue function
        raise Exception(f"Failed to get response from AI: {e}")


@require_http_methods(["POST"])
def getValue(request):
    try:
        data = json.loads(request.body)
        message = data.get("msg") 
        if not message:
            return JsonResponse({"error": "No 'msg' key found in request body"}, status=400)

        print(f"Received message: {message}")
        response = ask_ai(message)
        print(f"Gemini response: {response}")

        QuestionAnswer.objects.create(user = request.user, question=message, answer=response)
        return JsonResponse({"msg": message, "res": response})
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON in request body"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)