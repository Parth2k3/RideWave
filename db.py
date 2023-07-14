from sqlalchemy import  create_engine,text
import os
db_conn_str = os.environ['DB_CONN_STRING']

engine = create_engine(db_conn_str, connect_args={
  "ssl":{
    "ssl_ca": "/etc/ssl/cert.pem"
  }
},echo=True) 
def row_to_dict(result_proxy):
    row = result_proxy.fetchone()
    if row:
        column_names = result_proxy.keys()
        values = row
        diction = dict(zip(column_names, values))
        return diction
    else:
        return {}
def rows_to_list_of_dicts(result_proxy):
    rows = []
    for row in result_proxy:
        column_names = result_proxy.keys()
        values = row
        diction = dict(zip(column_names, values))
        rows.append(diction)
    return rows

def login(name, pword):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT username, password FROM Users WHERE username = :val"), {"val": name})
        d = row_to_dict(result)
        if not d:
          print("no user")
          return("Username not found")
        elif d['password'] == pword:
          print("welcome")
          return("Welcome")
        else:
          print("no pass")
          return("Wrong password")



def signupinsert(data):
  username = data['uname']
  firstname = data['fname']
  lastname = data['lname']
  email = data['mail']
  phoneNo = data['phone']
  password = data['pass']
  try:
        with engine.connect() as conn:
           conn.execute(
               text("insert into Users(`username`, `userFirstName`, `userLastName`, `EmailID`, `PhoneNo.`, `password`)values(:z,:x,:y,:a,:b,:c)"),
              {"x": firstname, "y": lastname, "z": username, "a": email, "b": phoneNo, "c": password}
           )
        return "Success"
  except Exception as e:
        return str(e)
def clusterinsert(id,data):
  carname= data['carname']
  carno= data['carno']
  cost=data['cost']
  initx=data['initx']
  inity=data['inity']
  finalx=data['finalx']
  finaly=data['finaly']
  leavedate=data['leavedate']
  leavetime=data['leavetime']
  seats=data['seats']
  try:
        with engine.connect() as conn:
           conn.execute(
               text("insert into Cluster(`adminusername`,`carname`, `carNo`, `cost`, `initiallocationx`, `initiallocationy`, `finallocationx`,`finallocationy`,`leavingtime`,`leavedate`,`seats`)values(:v0,:v1,:v2,:v3,:v4,:v5,:v6,:v7,:v8,:v9,:v10)"),
              {"v0":id,"v1": carname, "v2": carno, "v3": cost, "v4": initx, "v5": inity, "v6": finalx,"v7":finaly,"v9":leavedate,"v8":leavetime,"v10":seats}
           )
        return "Success"
  except Exception as e:
        return str(e)
def loadclusters(id):
  with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM Cluster where adminusername=:val"), {"val": id})
    return rows_to_list_of_dicts(result)

def loaddetails(cid):
  with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM Cluster where clusterid=:val"), {"val": cid})
    return row_to_dict(result)

def loadpool(cid):
  with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM Users where clusterid=:val"), {"val": cid})
    return rows_to_list_of_dicts(result)
def loadrequests(id):
  with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM Requests where adminusername=:val"), {"val": id})
    return rows_to_list_of_dicts(result)

def requestaccepted(id,what):
  with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM Requests where requestid=:val"), {"val": id})
    d=row_to_dict(result)
    cid=d['clusterid']
    uname=d['username']
    lat=d['latitude']
    lng=d['longitude']
    if(what=='1'):
      conn.execute(text("Update Users set clusterid=:cid,lng=:lng,lat=:lat where username=:uname"),{"cid":cid,"uname":uname,"lng":lng,"lat":lat})
      conn.execute(text("Update Cluster set noofpassengers=noofpassengers+1 where clusterid=:cid"),{"cid":cid})
    conn.execute(text("delete from Requests where requestid=:rid"),{"rid":id})
  return cid  
def requestinsert(admin,cid,id,lat,lng):
  try:
        with engine.connect() as conn:
          result1 = conn.execute(text("SELECT username FROM Users where username=:val and clusterid=:cid"), {"val": id,"cid":cid})
          r=row_to_dict(result1)
          if(len(r)>0):
            return '0'
          else:
            conn.execute(
               text("insert into Requests(`username`, `adminusername`, `clusterid`, `latitude`, `longitude`)values(:x,:y,:z,:a,:b)"),
              {"x": id, "y": admin, "z": cid, "a": lat, "b": lng}
           )
            return "Success"
  except Exception as e:
        return str(e)
def loadstatus(id):
  with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM Requests where username=:val"), {"val": id})
    return rows_to_list_of_dicts(result)
def match(id,lat,lng):
  with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM Cluster where adminusername<>:admin and noofpassengers<=seats "),{"admin":id})
    return rows_to_list_of_dicts(result)

def loadcluster_part(id):
  with engine.connect() as conn:
    result = conn.execute(text("SELECT c.* FROM Cluster c inner join Users u on c.clusterid=u.clusterid and u.username=:val"), {"val": id})
    return rows_to_list_of_dicts(result)
def removemember(cid,mid):
  with engine.connect() as conn:
    conn.execute(text("Update Users set clusterid=NULL where username=:mid"),{"mid":mid})
    conn.execute(text("Update Cluster set noofpassengers=noofpassengers-1 where clusterid=:cid"),{"cid":cid})
  return 0
def delete(cid):
  with engine.connect() as conn:
    print(cid)
    conn.execute(text("delete from Cluster where clusterid=:cid"),{"cid":cid})
    conn.execute(text("Update Users set clusterid=NULL where clusterid=:cid"),{"cid":cid})