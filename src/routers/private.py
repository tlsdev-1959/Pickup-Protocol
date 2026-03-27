from routers import api
import json

from objects.student import Student


CREW_FIELD: str = 'custom_field_two'
CARLINE_FIELD: str = 'custom_field_five'

router = api.APIRouter()
templates = api.Jinja2Templates(directory='templates')


@router.get('/', name='home')
async def home(request: api.Request, user=api.Depends(api.get_current_user)):
        print(user)
        return templates.TemplateResponse(request, 'home.html', {'user': user})

@router.get('/student', name='student')
async def getStudent(request: api.Request, id: int, user=api.Depends(api.get_current_user)):
    raw_response = await api.studentById(request, id, user)
    api_response = json.loads(raw_response.body)
    
    data=api_response['student']
    pickups = api_response['pickups']
    visitors = api_response['visitors']
    schedule = api_response['schedule']
    at_now = api_response['At now']


    student_obj = Student(id=data['id'], carline=data[CARLINE_FIELD], first=data['first_name'], last=data['last_name'], 
                      grade='GRADE_HERE', crew=data[CREW_FIELD], 
                      picutre_url=f'https:{data['profile_photo']['photo_url']}',
                      pickups=pickups, visitors=visitors, schedule=schedule, at_now=at_now)

    student = {
        'id': id,
        'name': f"{data['first_name']} {data['last_name']}",
        'grade': 'GRADE_HERE',
        'teacher': data['custom_field_two'],
        'homeroom': data['custom_field_two'],
        'photo_url': 'https:' + data['profile_photo']['photo_url'],
        #'photo_url': 'https:' + data['profile_pictures']['large_filename_url'],
        'pickups': pickups,
        'visitors': visitors,
        'where': at_now
    }
    return templates.TemplateResponse(request, 'student_found.html', {'user': user, 'student': student, 'student_obj': student_obj})
    

