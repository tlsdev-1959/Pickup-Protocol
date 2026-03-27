from routers import api
import json

from objects.student import Student


router = api.APIRouter()
templates = api.Jinja2Templates(directory='templates')


@router.get('/', name='home')
async def home(request: api.Request, user=api.Depends(api.get_current_user)):
        print(user)
        return templates.TemplateResponse(request, 'home.html', {'user': user, 'preferred': user['preferred']})

@router.get('/student', name='student')
async def getStudent(request: api.Request, id: int, user=api.Depends(api.get_current_user)):
    
    #async with api.httpx.AsyncClient() as client:
    #    api_response = await client.get(
    #        url=str(request.url_for('get_student_by_user_id')),
    #        params={'id': id},
    #        cookies=request.cookies
    #    )
    raw_response = await api.studentById(request, id, user)
    api_response = json.loads(raw_response.body)
    
    data=api_response['student']
    pickups = api_response['pickups']
    visitors = api_response['visitors']
    at_now = api_response['At now']


    student_obj = Student(id=data['id'], first=data['first_name'], last=data['last_name'], 
                      grade='GRADE_HERE', crew=data['custom_field_two'], 
                      picutre_url='https:'+data['profile_pictures']['large_filename_url'],
                      pickups=pickups, visitors=visitors, at_now=at_now)

    student = {
        'id': id,
        'name': f"{data['first_name']} {data['last_name']}",
        'grade': 'GRADE_HERE',
        'teacher': data['custom_field_two'],
        'homeroom': data['custom_field_two'],
        'photo_url': 'https:' + data['profile_pictures']['large_filename_url'],
        'pickups': pickups,
        'visitors': visitors,
        'where': at_now
    }
    return templates.TemplateResponse(request, 'student_found.html', {'student': student, 'student_obj': student_obj})
    

