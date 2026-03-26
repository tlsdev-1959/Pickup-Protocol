from routers import api

router = api.APIRouter()
templates = api.Jinja2Templates(directory='templates')


@router.get('/', name='home')
async def home(request: api.Request, user=api.Depends(api.get_current_user)):
        print(user)
        return templates.TemplateResponse(request, 'home.html', {'user': user, 'preferred': user['preferred']})

@router.get('/student', name='student')
async def getStudent(request: api.Request, id: int = 1, user=api.Depends(api.get_current_user)):
    async with api.httpx.AsyncClient() as client:
        api_response = await client.get(
            url=str(request.url_for('get_student_by_user_id')),
            params={'id': id},
            cookies=request.cookies
        )

    data=api_response.json()['student']
    pickups = api_response.json()['pickups']
    visitors = api_response.json()['visitors']
    at_now = api_response.json()['At now'][0]


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
    return templates.TemplateResponse(request, 'student_found.html', {'student': student})
    

