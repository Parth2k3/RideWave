from flask import Flask, render_template, request, redirect, flash,session, jsonify
from db import login,signupinsert,clusterinsert,loadclusters,loaddetails,loadpool,loadrequests,requestaccepted,requestinsert,loadstatus,match,loadcluster_part,removemember,delete
from functools import wraps
import os
import folium
from folium import Map, PolyLine
import folium.plugins as plugins
key=os.environ['API_KEY']
def login_required_for_id(f):
    @wraps(f)
    def decorated_function(id, *args, **kwargs):
        if 'username' not in session or session['username'] != id:
            return redirect('/login')
        return f(id, *args, **kwargs)
    return decorated_function

app = Flask(__name__)
app.secret_key = 'my_secret_key'

@app.route("/")
def hello():
  if 'username' in session:
          return redirect('/user/{}'.format(session['username']))
  return render_template('home.html')

@app.route("/login", methods=['GET', 'POST'])
def login_page():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    result = login(username, password)
    if result == "Welcome":
      session['username'] = username
      return redirect('/user/{}'.format(username))
    else:
      flash(result, 'error')
  return render_template('login.html')
  
@app.route("/logout")
def logout_page():
    session.pop('username', None)
    return redirect('/')
  
@app.route("/user/<id>")
@login_required_for_id
def data_page(id):
  return render_template('loggedin.html',username = id)

@app.route("/signup",methods=['GET','POST'])
def signup():
  if request.method=='POST':
    data=request.form
    result=signupinsert(data)
    if result == "Success":
      return redirect('/login')
    else:
      flash(result, 'error')
  return render_template('signup.html')
  
@app.route("/user/<id>/driver_form",methods=['GET','POST'])
@login_required_for_id
def driver_form(id):
  if request.method=='POST':
    data=request.form
    result=clusterinsert(id,data)
    if result=="Success":
      return redirect('/user/{}/clusters'.format(id))
    else:
      flash(result,'error')
  return render_template("driver_form.html",username=id,key=key)
 
@app.route("/user/<id>/clusters")
@login_required_for_id
def cluster(id):
  clusters=loadclusters(id)
  cluster_part=loadcluster_part(id)
  return render_template('cluster.html',username=id,clusters=clusters,clusters_part=cluster_part)
  
@app.route("/user/<id>/clusters/<cid>")
@login_required_for_id
def details(id,cid):
  det=loaddetails(cid)
  passengers=loadpool(cid)
  waypoints = ""
  for passenger in passengers:
    waypoints += str(passenger['lat']) + "," + str(passenger['lng']) + "|"
  waypoints = waypoints[:-1] 
  return render_template('details.html',username=id,clusters=cid,details=det,passengers=passengers,key=key,waypoints=waypoints)

@app.route("/user/<id>/clusters/<cid>/remove/<mid>")
@login_required_for_id
def remove(id,mid,cid):
  removemember(cid,mid)
  return redirect('/user/{}/clusters/{}'.format(id,cid))
@app.route("/user/<id>/clusters/<cid>/delete")
@login_required_for_id
def dele(id,cid):
  delete(cid)
  return redirect('/user/{}/clusters'.format(id))  
@app.route("/user/<id>/requests")
@login_required_for_id
def req(id):
  requests=loadrequests(id)
  return render_template('request.html',username=id,requests=requests,key = key)
  
@app.route("/processing/<what>/<id>/<rid>", methods=['GET', 'POST'])
@login_required_for_id
def accept_request(id,rid,what):
  c=requestaccepted(rid,what)
  if what=='0':
    return redirect('/user/{}/requests'.format(id))
  else:
    return redirect('/user/{}/clusters/{}'.format(id, c))
    
@app.route("/user/<id>/rider_form",methods=['GET','POST'])
@login_required_for_id
def rider_form(id):
  if request.method=='POST':
    data=request.form
    lat=data.get('lat')
    lng=data.get('lng')
    return redirect("/user/{}/rider_form/options/{}/{}".format(id,lat,lng))
  return render_template("rider_form.html",username=id,key=key)

@app.route("/user/<id>/rider_form/options/<lat>/<lng>")
@login_required_for_id
def options(id,lat,lng):
  m=match(id,lat,lng)
  return render_template("options.html",username=id,lat=lat,lng=lng,match=m)

@app.route("/user/<id>/rider_form/options/<lat>/<lng>/<cid>/<admin>",methods=['GET','POST'])
def req_insert(cid,id,lat,lng,admin):
  requestinsert(admin,cid,id,lat,lng)
  return redirect('/user/{}/request_status'.format(id))

@app.route("/user/<id>/request_status")
@login_required_for_id
def status(id):
  stat=loadstatus(id)
  return render_template('request_status.html',username=id,status=stat)
@app.route("/user/<id>/clusters/<cid>/map")
@login_required_for_id
def map(id,cid):
  det=loaddetails(cid)
  passengers=loadpool(cid)
  initial_location = [det['initiallocationx'], det['initiallocationy']]
  final_location = [det['finallocationx'], det['finallocationy']]
  pitstop_locations = [[passenger['lat'], passenger['lng'], passenger['username']] for passenger in passengers]
  # Create a map object centered on the initial location
  m = folium.Map(location=initial_location, zoom_start=12,tiles="https://maps.googleapis.com/maps/api/roadmap/tile?&key={}".format(key),attr='Map data © Google')
  # Add the initial and final markers to the map
  folium.Marker(initial_location, tooltip='Start').add_to(m)
  folium.Marker(final_location, tooltip='End').add_to(m)
  # Add the pit stop markers and names to the map
  for location in pitstop_locations:
      folium.Marker(location[:2], tooltip=location[2]).add_to(m)
  # Generate the route between the initial and final locations with the pit stops
  waypoints1 = pitstop_locations.copy()
  waypoints1.insert(0, initial_location)
  waypoints1.append(final_location)
  coordinates = [[float(location[0]),float(location[1])] for location in waypoints1]
  timestamps = [0] + [i * 60 for i in range(1, len(pitstop_locations) + 2)]
  route = folium.PolyLine(locations=coordinates, color='red', weight=5)
  # Add the polyline to the map using the TimestampedGeoJson plugin
  plugins.TimestampedGeoJson({
    'type': 'FeatureCollection',
    'features': [
        {
            'type': 'Feature',
            'geometry': {
                'type': 'LineString',
                'coordinates': coordinates
            },
            'properties': {
                'times': timestamps
            }
        }
    ]
  } , period='PT1M', add_last_point=True, auto_play=True).add_to(m)

  # Add the route to the map
  route.add_to(m)

  # Render the map
  map_html = m._repr_html_()
  print(map_html)
  # Render the template with the map HTML
  return render_template('maps.html',username=id,clusters=cid,details=det,passengers=passengers,key=key,map=map_html)
if __name__=="__main__":
  app.run(host='0.0.0.0',debug=True)



