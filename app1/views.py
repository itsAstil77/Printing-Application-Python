
from django.shortcuts import render, redirect
from django.contrib import messages
import requests
import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image, ImageDraw, ImageFont,ImageOps
from io import BytesIO
from django.conf import settings

LOGIN = 'http://piqapi.foulath.com.bh/api/Authentication/Login'

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        payload = {
            "userId": username,
            "password": password
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        try:
            response = requests.post(LOGIN, json=payload, headers=headers, allow_redirects=False)
            try:
                data = response.json()
            except ValueError:
                data = {}

            print('Response data:', data)

            message = data.get('message', '')

            if response.status_code == 200:
                if message and 'Otp' in message:
                    request.session['username'] = username
                    request.session['password'] = password
                    messages.success(request, 'OTP sent to your email.')
                    return redirect('otp')
                else:
                    messages.error(request, message or 'Login failed. Please check email and password.')
            else:
                messages.error(request, message or 'Invalid username or password.')

        except requests.RequestException as e:
            print(f"Request Exception: {e}")
            messages.error(request, 'There was an error connecting to the login API.')

    return render(request, 'app1/login.html')

OTP_API = 'http://piqapi.foulath.com.bh/api/Authentication/TwoFactorAuthentication'

def otp_view(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        username = request.session.get('username')
        password = request.session.get('password')

        payload = {
            "userId": username,
            "twoAuthCode": otp
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        try:
            response = requests.post(OTP_API, json=payload, headers=headers)
            if response.status_code != 200:
                messages.error(request, f"Error: {response.status_code} - Could not contact the OTP API.")
                return render(request, 'app1/otp.html')

            try:
                data = response.json()
            except ValueError:
                messages.error(request, "Error: Invalid JSON response from OTP verification API.")
                return render(request, 'app1/otp.html')

            print("OTP response:", data)

            if data.get('isError'):
                messages.error(request, f"OTP verification failed: {data.get('errorMessage', 'Unknown error')}")
                return render(request, 'app1/otp.html')

            if data.get('message') and 'Login' in data['message']:
                messages.success(request, 'OTP verified successfully.')
                return redirect('emp')

            messages.error(request, 'OTP verification failed. Please try again.')

        except requests.RequestException as e:
            messages.error(request, f'An error occurred during OTP verification: {str(e)}')

    return render(request, 'app1/otp.html')

RESEND_OTP_API = 'http://piqapi.foulath.com.bh/api/Authentication/ReSendOtpLogin'

def resend_otp_view(request):
    username = request.session.get('username')
    if username:
        payload = {"userId": username}
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'text/plain'
        }

        try:
            response = requests.post(RESEND_OTP_API, json=payload, headers=headers)
            print("API Response Status Code:", response.status_code)
            print("API Response Body:", response.text)

            data = response.json()

            if data.get("isError") == False and data.get("statusCode") == 0:
                messages.success(request, data.get("message", "OTP has been resent successfully."))
            else:
                error_message = data.get("errorMessage", "Failed to resend OTP.")
                messages.error(request, f"Failed to resend OTP: {error_message}")
        except requests.RequestException as e:
            messages.error(request, f'An error occurred: {str(e)}')
        except ValueError:
            messages.error(request, "Failed to process the API response.")
    else:
        messages.error(request, 'Session expired or invalid. Please log in again.')

    return redirect('otp')

def employee_info_view(request):
    email = request.session.get('username', 'Guest')
    tenant_id = 'CS000067'
    payload = {
        "data": {
            "clientId": "CS000067",
            "userId": email,
            "pageNumber": 1,
            "pageSize": 36,
            "searchKey": "",
            "projectId": "",
            "countryId": "",
            "areaId": "",
            "buildingId": "",
            "floorId": "",
            "zoneId": "",
            "roleid": "",
            "fromDate": "",
            "toDate": ""
        }
    }

    headers = {
        'Content-Type': 'application/json',
        'Tenant-ID': tenant_id,
    }

    full_response = {}

    try:
        response = requests.post(
            'http://piqapi.foulath.com.bh/api/administrator/Configuration/Employee/EmployeeSummary',
            headers=headers,
            json=payload
        )

        if response.status_code == 200:
            full_response = response.json()
            employee_data = full_response.get('employees', [])
            print('api response body :', response.text)
            print("Employee Data:", employee_data)
        else:
            print("API Error:", response.status_code, response.text)
            employee_data = []

    except requests.RequestException as e:
        print("Request Exception:", e)
        employee_data = []

    return render(request, 'app1/emp.html', {
        'employee_data': employee_data,
        'full_response': full_response,
        'email': email
    })

ID_CARD_SAVE_PATH = os.path.join(settings.MEDIA_ROOT, 'generated_id_cards')
FONT_PATH = os.path.join(settings.BASE_DIR, 'app1', 'static', 'app1', 'fonts', 'RedHatDisplay-Medium.ttf')

TEMPLATE_PATHS = {
    'type1': 'http://piqapi.foulath.com.bh/uploads/PrintingCards/BahrainStaffCard.jpg',
    'type2': 'http://piqapi.foulath.com.bh/uploads/PrintingCards/BahrainContractorCard.jpg',
    'type3': 'http://piqapi.foulath.com.bh/uploads/PrintingCards/FoulathStaffCard.jpg',
    'type4': 'http://piqapi.foulath.com.bh/uploads/PrintingCards/FoulathContractorCard.jpg',
    'type5': 'http://piqapi.foulath.com.bh/uploads/PrintingCards/InfotechStaffCard.jpg',
    'type6': 'http://piqapi.foulath.com.bh/uploads/PrintingCards/InfotechContractorCard.jpg',
    'type7': 'http://piqapi.foulath.com.bh/uploads/PrintingCards/SulbStaffCard.jpg',
    'type8': 'http://piqapi.foulath.com.bh/uploads/PrintingCards/SulbContractorCard.jpg'


}

os.makedirs(ID_CARD_SAVE_PATH, exist_ok=True)

def fetch_employee_data(employee_id):
    """ Fetch employee details from API """
    payload = {
        "data": {
            "clientId": "CS000067",
            "userId": "mohammed.kamal@foulath.com.bh",
            "searchKey": employee_id
        }
    }
    headers = {'Content-Type': 'application/json', 'Tenant-ID': 'CS000067'}

    try:
        response = requests.post(
            'http://piqapi.foulath.com.bh/api/administrator/Configuration/Employee/EmployeeSummary',
            headers=headers,
            json=payload
        )
        if response.status_code == 200:
            data = response.json()
            employee = next((emp for emp in data.get('employees', []) if emp['idNumber'] == employee_id), None)
            return employee
    except requests.RequestException as e:
        print(f"API request failed: {e}")
    return None


# @csrf_exempt
# def generate_selected_id_cards(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             employee_ids = data.get('employee_ids', [])
#             card_type = data.get('card_type', 'type1')

#             print(f"DEBUG: Frontend sent card_type (as received by Django): '{card_type}'")
#             print(f"DEBUG: TEMPLATE_PATHS keys: {list(TEMPLATE_PATHS.keys())}")

#             if not employee_ids:
#                 return JsonResponse({'message': 'No employees selected.'}, status=400)

#             if card_type not in TEMPLATE_PATHS:
#                 print(f"DEBUG: Invalid card type '{card_type}' received. Not in TEMPLATE_PATHS.")
#                 return JsonResponse({'message': f"Invalid card type: {card_type}"}, status=400)

#             template_url = TEMPLATE_PATHS[card_type]
#             print(f"DEBUG: Django selected template URL: {template_url}") 

#             response = requests.get(template_url)
#             if response.status_code != 200:
#                 return JsonResponse(
#                     {'message': f'Template image could not be fetched from {template_url}. Status: {response.status_code}'},
#                     status=500
#                 )

#             template_image = Image.open(BytesIO(response.content)).convert("RGB")
#             generated_files = []

#             try:
#                 font_large = ImageFont.truetype(FONT_PATH, 24)
#                 font_medium = ImageFont.truetype(FONT_PATH, 24)
#                 font_small = ImageFont.truetype(FONT_PATH, 24)
#             except OSError:
#                 print(f"WARNING: Font not found at {FONT_PATH}. Using default font.")
#                 font_large = font_medium = font_small = ImageFont.load_default()

#             for employee_id in employee_ids:
#                 employee = fetch_employee_data(employee_id)
#                 if not employee:
#                     print(f"WARNING: Employee data not found for ID: {employee_id}")
#                     continue

#                 id_card = template_image.copy()
#                 draw = ImageDraw.Draw(id_card)

#                 # Fetch and paste employee image
#                 employee_image_url = employee.get('employeeImage', None)
#                 if employee_image_url:
#                     try:
#                         img_response = requests.get(employee_image_url)
#                         if img_response.status_code == 200:
#                             emp_img = Image.open(BytesIO(img_response.content)).convert('RGB')
#                             emp_img = ImageOps.exif_transpose(emp_img)
#                             emp_img = ImageOps.fit(emp_img, (237, 317), method=Image.LANCZOS, centering=(0.5, 0.3))
#                             id_card.paste(emp_img, (729, 186))
#                         else:
#                             print(f"WARNING: Could not fetch employee image for {employee_id}. Status: {img_response.status_code}")
#                     except Exception as e:
#                         print(f"Error loading employee image for {employee_id}: {e}")

#                 # Draw employee details
#                 draw.text((235, 253), f"{employee.get('firstname', 'N/A')} {employee.get('lastname', '')}", fill="black", font=font_large)
#                 draw.text((235, 318), f"{employee.get('department', 'N/A')}", fill="black", font=font_medium)
#                 draw.text((235, 378), f"{employee.get('idNumber', 'N/A')}", fill="black", font=font_small)
#                 draw.text((235, 440), f"{employee.get('nationalId', 'N/A')}", fill="black", font=font_small)
#                 draw.text((235, 506), f"{employee.get('endDate', 'N/A')}", fill="black", font=font_small)

#                 # Ensure RGB before saving as PNG
#                 id_card = id_card.convert("RGB")
#                 output_filename = f"{employee['idNumber']}_id_card.png"
#                 output_path = os.path.join(ID_CARD_SAVE_PATH, output_filename)
#                 id_card.save(output_path, format="PNG", optimize=True, quality=85)

#                 generated_files.append(output_filename)

#             return JsonResponse({'message': 'ID cards generated successfully.', 'files': generated_files})

#         except Exception as e:
#             print(f"Error in generate_selected_id_cards: {e}") 
#             return JsonResponse({'message': f'An error occurred while generating ID cards: {str(e)}'}, status=500)

#     return JsonResponse({'message': 'Invalid request method.'}, status=405)




@csrf_exempt
def generate_selected_id_cards(request):
    try:
        # Accept both JSON (AJAX) and form POST
        if request.method != 'POST':
            return JsonResponse({'message': 'Invalid request method'}, status=405)

        try:
            data = json.loads(request.body)
            employee_ids = data.get('employee_ids', [])
            card_type = data.get('card_type', '')
        except (json.JSONDecodeError, TypeError):
            employee_ids = request.POST.getlist('employee_ids[]') or request.POST.getlist('employee_ids')
            card_type = request.POST.get('card_type', '')

        print("DEBUG: Received employee_ids:", employee_ids)
        print("DEBUG: Received card_type:", card_type)

        if not employee_ids or not card_type:
            return JsonResponse({'message': 'Employee IDs and card type are required'}, status=400)

        template_url = TEMPLATE_PATHS.get(card_type)
        if not template_url:
            return JsonResponse({'message': f'Invalid card type: {card_type}'}, status=400)

        response = requests.get(template_url)
        if response.status_code != 200:
            return JsonResponse({'message': f'Template image could not be fetched from {template_url}. Status: {response.status_code}'}, status=500)

        template_image = Image.open(BytesIO(response.content)).convert("RGB")

        try:
            font_large = ImageFont.truetype(FONT_PATH, 24)
            font_medium = ImageFont.truetype(FONT_PATH, 24)
            font_small = ImageFont.truetype(FONT_PATH, 24)
        except OSError:
            print(f"WARNING: Font not found at {FONT_PATH}. Using default font.")
            font_large = font_medium = font_small = ImageFont.load_default()

        LAYOUTS = {
            "group1": {  
                "image_size": (237, 317),
                "image_pos": (729, 186),
                "fields": [
                    {"key": "firstname", "pos": (235, 253), "font": "large", "suffix": " {lastname}"},
                    {"key": "designation", "pos": (235, 318), "font": "medium"},
                    {"key": "idNumber", "pos": (235, 378), "font": "small"},
                    {"key": "nationalId", "pos": (235, 440), "font": "small"},
                    {"key": "endDate", "pos": (235, 506), "font": "small"},
                ]
            },
            "group2": {  
                "image_size": (237, 317),
                "image_pos": (729, 186),
                "fields": [
                    {"key": "firstname", "pos": (120, 220), "font": "large", "suffix": " {lastname}"},
                    {"key": "designation", "pos": (120, 280), "font": "medium"},
                    {"key": "nationalId", "pos": (120, 340), "font": "small"},
                    {"key": "endDate", "pos": (120, 400), "font": "small"},
                ]
            }
        }

        
        generated_files = []

        for employee_id in employee_ids:
            employee = fetch_employee_data(employee_id)
            if not employee:
                print(f"WARNING: Employee data not found for ID: {employee_id}")
                continue

            id_card = template_image.copy()
            draw = ImageDraw.Draw(id_card)

            # Select layout group
            layout_key = GROUP_MAPPING.get(card_type, "group1")
            layout = LAYOUTS[layout_key]

            # Employee photo
            employee_image_url = employee.get('employeeImage')
            if employee_image_url:
                try:
                    img_response = requests.get(employee_image_url)
                    if img_response.status_code == 200:
                        emp_img = Image.open(BytesIO(img_response.content)).convert('RGB')
                        emp_img = ImageOps.exif_transpose(emp_img)
                        emp_img = ImageOps.fit(emp_img, layout["image_size"], method=Image.LANCZOS, centering=(0.5, 0.3))
                        id_card.paste(emp_img, layout["image_pos"])
                except Exception as e:
                    print(f"Error loading employee image for {employee_id}: {e}")

            # Draw fields dynamically
            for field in layout["fields"]:
                value = employee.get(field["key"], "N/A")
                if "{lastname}" in field.get("suffix", ""):
                    value = f"{employee.get('firstname', 'N/A')} {employee.get('lastname', '')}"
                text = f"{field.get('prefix', '')}{value}{field.get('suffix', '').replace('{lastname}', '')}"
                font = {"large": font_large, "medium": font_medium, "small": font_small}[field["font"]]
                draw.text(field["pos"], text, fill="black", font=font)

            # Save file
            id_card = id_card.convert("RGB")
            output_filename = f"{employee['idNumber']}_{card_type}_id_card.png"
            output_path = os.path.join(ID_CARD_SAVE_PATH, output_filename)
            id_card.save(output_path, format="PNG", optimize=True, quality=85)
            generated_files.append(output_filename)

        return JsonResponse({'message': 'ID cards generated successfully!', 'files': generated_files})

    except Exception as e:
        print(f"Error in generate_selected_id_cards: {str(e)}")
        return JsonResponse({'message': f'Error generating ID cards: {str(e)}'}, status=500)
