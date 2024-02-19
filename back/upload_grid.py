import requests
import httpx
import time

url = "http://localhost:8000/teams/grid?secret=aaaaaa&team_name=first&password=aaaaaa"
# # files = {'file': open('data/grid.csv','rb')}
# files = {'file': open('requirements.txt','rb')}
# # files = {'file': open('requirements.txt','rb')}
# values = {'team_name': 'first', 'password': 'aaaaaa'}

# with httpx.Client(timeout=None) as client:
#     r = client.post(url, data=values, files=files)
#     print(r.status_code, r.json(), sep=' ')

# import requests
# from requests_toolbelt.multipart import encoder

# url = "http://localhost:8000/teams/grid?secret=aaaaaa"

# session = requests.Session()
# with open('data/grid.csv', 'rb') as f:
# # with open('requirements.txt', 'rb') as f:
#     form = encoder.MultipartEncoder({
#         "file": ("grid.csv", f, "application/octet-stream"),
#         'team_name': 'first', 
#         'password': 'aaaaaa'
#     })
#     headers = {"Prefer": "respond-async", "Content-Type": form.content_type}
#     resp = session.post(url, headers=headers, data=form)
#     print(resp.content)
# session.close()

# files = {'file': open('data.grid.csv', 'rb')}
filename = 'grid.csv'
files = {'file': open(f"data/{filename}",'rb')}
headers={'Filename': filename}
data = {'team_name': 'first', 'password': 'aaaaaa'}

with httpx.Client() as client:
    start = time.time()
    r = client.post(url, data=data, files=files, headers=headers)
    end = time.time()
    print(f'Time elapsed: {end - start}s')
    print(r.status_code, r.json(), sep=' ')